"""
LangGraph Workflow with Router + Specialist Agent Architecture.
Provides full traceability of the multi-agent pharmacy system.

Agent Flow:
1. ROUTER - Classifies intent (GREETING, SYMPTOM_QUERY, MEDICINE_ORDER, etc.)
2. Based on intent:
   - GREETING/GENERAL_CHAT → General Conversation Agent
   - SYMPTOM_QUERY → Medical Advisor Agent → Recommendation Agent
   - MEDICINE_RECOMMENDATION → Recommendation Agent  
   - MEDICINE_ORDER → Pharmacist Agent → Safety Agent → Confirmation → Execution

Each step is traced for observability in LangSmith.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state_schema import AgentState

# Import all agents
from agents.router_agent import router_agent
from agents.general_chat_agent import general_chat_agent
from agents.medical_advisor_agent import medical_advisor_agent
from agents.recommendation_agent import recommendation_agent
from agents.pharmacist_agent import pharmacist_agent
from agents.safety_agent import safety_agent
from agents.drug_interaction_agent import drug_interaction_agent
from agents.confirmation_agent import confirmation_agent
from agents.execution_agent import execution_agent

# Import conversation memory for intent handling
from agents.conversation_memory import set_last_intent, get_last_intent, has_symptoms, has_recommendations
import os

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "swasthya-sarthi")

# Configure LangSmith if available
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"[Graph] LangSmith enabled - Project: {LANGSMITH_PROJECT}")
else:
    print("[Graph] LangSmith not configured - set LANGSMITH_API_KEY for tracing")


def should_route_to_medical(state: AgentState) -> str:
    """
    Router logic to determine next agent based on intent.
    Enhanced for conversational flow with memory awareness.
    """
    intent = state.get("intent_type", state.get("current_intent", "GENERAL_CHAT"))
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    print(f"[Router] Intent: {intent}")
    
    # Store intent in memory for follow-up tracking
    set_last_intent(user_id, session_id, intent)
    
    # Route based on intent type
    if intent in ["GREETING", "GENERAL_CHAT"]:
        return "general"
    elif intent in ["SYMPTOM_QUERY", "MEDICAL_INFORMATION"]:
        return "medical"
    elif intent == "MEDICINE_RECOMMENDATION":
        # If we already have symptoms, go straight to recommendation
        if has_symptoms(user_id, session_id):
            return "recommend"
        return "medical"  # Need to analyze symptoms first
    elif intent == "MEDICINE_ORDER":
        return "order"
    elif intent == "FOLLOW_UP":
        # Smart follow-up routing based on conversation memory
        if has_recommendations(user_id, session_id):
            # User likely wants to order previously recommended medicine
            return "order"
        elif has_symptoms(user_id, session_id):
            # Continue with recommendation flow
            return "recommend"
        else:
            return "general"
    else:
        return "general"



def should_route_from_medical(state: AgentState) -> str:
    """
    After medical advisor, determine next step.
    If symptoms were found, recommend medicines.
    Otherwise, end the conversation.
    """
    symptoms = state.get("identified_symptoms", [])
    if symptoms and len(symptoms) > 0:
        return "recommend"
    return "end"


def should_route_after_recommendation(state: AgentState) -> str:
    """
    After recommendation, check if user wants to order.
    This is determined by intent or user confirmation.
    """
    intent = state.get("intent_type", "GENERAL_CHAT")
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    # If user explicitly wants to order
    if intent == "MEDICINE_ORDER":
        return "order"
    
    # If we have recommendations and user is following up
    if has_recommendations(user_id, session_id) and intent == "FOLLOW_UP":
        return "order"
    
    return "end"



# Create the workflow
workflow = StateGraph(AgentState)

# Add all agent nodes
workflow.add_node("router", router_agent)
workflow.add_node("general_chat", general_chat_agent)
workflow.add_node("medical_advisor", medical_advisor_agent)
workflow.add_node("recommendation", recommendation_agent)
workflow.add_node("pharmacist", pharmacist_agent)
workflow.add_node("safety", safety_agent)
workflow.add_node("drug_interaction", drug_interaction_agent)
workflow.add_node("confirmation", confirmation_agent)
workflow.add_node("execution", execution_agent)

# Entry point
workflow.set_entry_point("router")

# Router decision - route based on intent
workflow.add_conditional_edges(
    "router",
    should_route_to_medical,
    {
        "general": "general_chat",
        "medical": "medical_advisor",
        "recommend": "recommendation",
        "order": "pharmacist"
    }
)

# Medical advisor → Recommendation (conditional)
workflow.add_conditional_edges(
    "medical_advisor",
    should_route_from_medical,
    {
        "recommend": "recommendation",
        "end": END
    }
)

# After recommendation, check if user wants to order
workflow.add_conditional_edges(
    "recommendation",
    should_route_after_recommendation,
    {
        "order": "pharmacist",
        "end": END
    }
)


# Order flow: pharmacist → safety → drug_interaction → confirmation → execution
workflow.add_edge("pharmacist", "safety")
workflow.add_edge("safety", "drug_interaction")
workflow.add_edge("drug_interaction", "confirmation")
workflow.add_edge("confirmation", "execution")
workflow.add_edge("execution", END)

# Compile with checkpoint memory for conversation continuity
checkpointer = MemorySaver()
app_graph = workflow.compile(checkpointer=checkpointer)

# Export for use in other modules
__all__ = ["app_graph"]


def run_conversation(user_input: str, user_id: str = "default", session_id: str = "default", 
                    user_language: str = "en") -> dict:
    """
    Run a conversation turn through the agent workflow.
    Enhanced with full observability and conversational memory.
    
    Args:
        user_input: User's message
        user_id: User identifier
        session_id: Session identifier
        user_language: User's preferred language
    
    Returns:
        dict with final_response, agent_trace, and metadata
    """
    from agents.conversation_memory import get_session, add_message
    
    # Initialize or get existing session
    session = get_session(user_id, session_id)
    
    # Add user message to history
    add_message(user_id, session_id, "user", user_input)
    
    # Initialize state with conversation context
    initial_state = {
        "user_input": user_input,
        "user_id": user_id,
        "session_id": session_id,
        "user_language": user_language,
        "intent_type": "GENERAL_CHAT",
        "current_intent": "GENERAL_CHAT",
        "detected_language": user_language,
        "identified_symptoms": session.get("last_symptoms", []),
        "possible_conditions": session.get("last_conditions", []),
        "medical_advice": "",
        "recommended_medicines": session.get("recommended_medicines", []),
        "metadata": {
            "agent_name": "conversation_router",
            "action": "process_user_input",
            "language": user_language
        },
        "agent_trace": []
    }
    
    # Run the graph with checkpointing for conversation continuity
    try:
        result = app_graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": f"{user_id}:{session_id}"}}
        )
        
        # Add assistant response to history
        add_message(user_id, session_id, "assistant", result.get("final_response", ""))
        
        return {
            "response": result.get("final_response", ""),
            "intent": result.get("intent_type", "GENERAL_CHAT"),
            "trace": result.get("agent_trace", []),
            "metadata": result.get("metadata", {}),
            "recommended_medicines": result.get("recommended_medicines", []),
            "symptoms": result.get("identified_symptoms", [])
        }
    except Exception as e:
        print(f"[Graph] Error: {e}")
        return {
            "response": "I apologize, but I encountered an error. Please try again.",
            "intent": "ERROR",
            "trace": [],
            "metadata": {"error": str(e), "agent_name": "error_handler"},
            "recommended_medicines": [],
            "symptoms": []
        }


def get_conversation_context(user_id: str = "default", session_id: str = "default") -> dict:
    """
    Get the current conversation context for a session.
    Useful for follow-up queries and maintaining state.
    """
    from agents.conversation_memory import get_session
    
    session = get_session(user_id, session_id)
    return {
        "last_symptoms": session.get("last_symptoms", []),
        "last_recommendations": session.get("recommended_medicines", []),
        "last_intent": session.get("last_intent", "GENERAL_CHAT"),
        "conversation_history": session.get("conversation_history", [])
    }
