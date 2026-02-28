"""
LangGraph Workflow - With Router Agent:
1. Router Agent - Intent detection and routing
2. Pharmacist Agent - Order parsing and validation
3. Safety Agent - Medicine safety checks
4. Execution Agent - Order processing
5. Refill Trigger Agent - Medication refill reminders
6. Prescription Agent - Prescription OCR & medicine extraction
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state_schema import AgentState
from agents.router_agent import router_agent
from agents.pharmacist_agent import pharmacist_agent
from agents.safety_agent import safety_agent
from agents.execution_agent import execution_agent
from agents.refill_trigger_agent import refill_trigger_agent
from agents.prescription_agent import prescription_agent
import os


def should_route_intent(state: AgentState) -> str:
    """Route based on detected intent from router agent."""
    intent = state.get("current_intent", state.get("intent_type", "MEDICINE_ORDER"))
    
    # If router already set final_response, skip to end
    if state.get("final_response"):
        return "end"
    
    # Route based on intent
    if intent == "SHOW_MEDICINES":
        return "end"  # Router handles this
    elif intent == "UPLOAD_PRESCRIPTION":
        return "prescription"
    elif intent == "ORDER_HISTORY":
        return "end"  # Router handles this
    elif intent == "REFILL_REMINDERS":
        return "refill"
    elif intent == "SHOW_PROFILE":
        return "end"  # Router handles this
    elif intent == "GENERAL_CHAT":
        return "end"  # Router handles this
    elif intent == "MEDICINE_ORDER":
        return "pharmacist"
    else:
        return "pharmacist"


def should_route_to_prescription(state: AgentState) -> str:
    """Check if user wants to upload a prescription."""
    user_input = state.get("user_input", "").lower()
    intent = state.get("intent_type", "")
    
    if "prescription" in user_input or "prescribe" in user_input or intent == "PRESCRIPTION_UPLOAD":
        return "prescription"
    return "pharmacist"


def should_route_to_safety(state: AgentState) -> str:
    """After pharmacist, route to safety check."""
    return "safety"


def should_route_to_execution(state: AgentState) -> str:
    """After safety check, route to execution."""
    return "execution"


def should_route_to_refill(state: AgentState) -> str:
    """Check if user wants refill reminders."""
    user_input = state.get("user_input", "").lower()
    intent = state.get("intent_type", "")
    
    if "refill" in user_input or "reminder" in user_input or intent == "REFILL_REMINDERS":
        return "refill"
    return "end"


# Create the workflow
workflow = StateGraph(AgentState)

# Add all agent nodes
workflow.add_node("router", router_agent)
workflow.add_node("prescription", prescription_agent)
workflow.add_node("pharmacist", pharmacist_agent)
workflow.add_node("safety", safety_agent)
workflow.add_node("execution", execution_agent)
workflow.add_node("refill", refill_trigger_agent)

# Entry point - start with router
workflow.set_entry_point("router")

# Router routes to appropriate handler based on intent
workflow.add_conditional_edges(
    "router",
    should_route_intent,
    {
        "prescription": "prescription",
        "pharmacist": "pharmacist",
        "refill": "refill",
        "end": END
    }
)

# Route based on input type for prescription upload
workflow.add_conditional_edges(
    "prescription",
    should_route_to_prescription,
    {
        "prescription": "prescription",
        "pharmacist": "pharmacist"
    }
)

# Prescription flow: if prescription uploaded, process it
workflow.add_edge("prescription", "pharmacist")

# Pharmacist → Safety
workflow.add_edge("pharmacist", "safety")

# Safety → Execution
workflow.add_edge("safety", "execution")

# Execution → Check for refill
workflow.add_conditional_edges(
    "execution",
    should_route_to_refill,
    {
        "refill": "refill",
        "end": END
    }
)

# Refill → End
workflow.add_edge("refill", END)

# Compile with checkpoint memory for conversation continuity
checkpointer = MemorySaver()
app_graph = workflow.compile(checkpointer=checkpointer)

# Export for use in other modules
__all__ = ["app_graph"]


def run_conversation(user_input: str, user_id: str = "default", session_id: str = "default", 
                    user_language: str = "en") -> dict:
    """
    Run a conversation turn through the agent workflow.
    
    Args:
        user_input: User's message
        user_id: User identifier
        session_id: Session identifier
        user_language: User's preferred language
    
    Returns:
        dict with final_response, agent_trace, and metadata
    """
    # Initialize state
    initial_state = {
        "user_input": user_input,
        "user_id": user_id,
        "session_id": session_id,
        "user_language": user_language,
        "intent_type": "MEDICINE_ORDER",
        "current_intent": "MEDICINE_ORDER",
        "detected_language": user_language,
        "identified_symptoms": [],
        "possible_conditions": [],
        "medical_advice": "",
        "recommended_medicines": [],
        "metadata": {
            "agent_name": "workflow",
            "action": "process_user_input",
            "language": user_language
        },
        "agent_trace": []
    }
    
    # Run the graph
    try:
        result = app_graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": f"{user_id}:{session_id}"}}
        )
        
        response_data = {
            "response": result.get("final_response", ""),
            "intent": result.get("intent_type", "MEDICINE_ORDER"),
            "trace": result.get("agent_trace", []),
            "metadata": result.get("metadata", {}),
            "recommended_medicines": result.get("recommended_medicines", []),
            "symptoms": result.get("identified_symptoms", [])
        }
        
        return response_data
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
