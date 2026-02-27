"""
Router Agent - Intent classification for SwasthyaSarthi.
Classifies user input into specific categories to route to appropriate specialist agents.

Uses Ollama for local inference with strict structured output.
"""
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from agents.prompt_templates import format_router_prompt
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re


# Intent types
INTENT_TYPES = [
    "GREETING",
    "GENERAL_CHAT",
    "SYMPTOM_QUERY",
    "MEDICAL_INFORMATION",
    "MEDICINE_RECOMMENDATION",
    "MEDICINE_ORDER",
    "FOLLOW_UP"
]

# Language detection keywords
LANGUAGE_KEYWORDS = {
    "hi": ["namaste", "namaskar", "kaise", "kya", "haan", "nahi", "dawai", "dawa", "bimar", "illaj"],
    "mr": ["namaskar", "kasa", "kaay", "haa", "nahi", "oyushad", "oyu", "vayambe", "upchar"],
    "bn": ["namaskar", "kemon", "ki", "haa", "na", "oshudh", "bimar", "chikitsa"],
    "gu": ["namaste", "kem cho", "shu", "haa", "nai", "davai", "bimar", "ilaj"],
    "ml": ["namaskaram", "ente", "enn", "aa", "alla", "vaidyam", "rogi"],
    "en": []  # Default
}

# Router system prompt (Ollama optimized) - imported from prompt_templates
# Kept here for backward compatibility
ROUTER_SYSTEM_PROMPT = """You are an intent classifier for a pharmacy assistant.

Classify the user message into ONE category:
GREETING - Friendly greetings, hellos, thanks
GENERAL_CHAT - Casual conversation, how are you, jokes
SYMPTOM_QUERY - User describes symptoms like fever, cough, pain
MEDICAL_INFORMATION - User asks about medicine info, side effects, uses
MEDICINE_RECOMMENDATION - User asks for medicine suggestions based on symptoms
MEDICINE_ORDER - User wants to buy/order medicine
FOLLOW_UP - User continues previous conversation about same topic

Return ONLY valid JSON with no additional text:
{{"intent": "<category>"}}"""



def detect_language(user_input: str) -> str:
    """Detect user language from input."""
    user_lower = user_input.lower()
    
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        if lang == "en":
            continue
        for keyword in keywords:
            if keyword in user_lower:
                return lang
    
    return "en"  # Default to English


def _extract_intent_from_response(response: str) -> str:
    """Extract intent from LLM response."""
    response = response.strip()
    
    # Try to parse JSON
    try:
        data = json.loads(response)
        if "intent" in data and data["intent"] in INTENT_TYPES:
            return data["intent"]
    except:
        pass
    
    # Try to extract from text
    for intent in INTENT_TYPES:
        if intent in response.upper():
            return intent
    
    # Default fallback
    return "GENERAL_CHAT"


def router_agent(state: AgentState) -> AgentState:
    """
    Classify user input into intent types and route to appropriate agent.
    
    Flow:
    1. Detect language
    2. Classify intent using LLM or rule-based
    3. Add metadata for observability
    """
    # Initialize trace
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    user_input = state.get("user_input", "")
    user_language = detect_language(user_input)
    
    # Update state with detected language
    state["user_language"] = user_language
    state["detected_language"] = user_language
    
    # Trace entry
    trace_entry = {
        "agent": "router_agent",
        "step": "classify_intent",
        "user_input": user_input[:50],
        "detected_language": user_language
    }
    
    # Get LLM for classification
    llm = get_llm()
    
    if llm is None or not user_input.strip():
        # Rule-based fallback
        intent = _rule_based_intent(user_input)
        trace_entry["intent"] = intent
        trace_entry["method"] = "rule_based"
        trace_entry["agent_name"] = "router_agent"
        trace_entry["action"] = "classify_intent"
        print(f"[Router Agent] Rule-based intent: {intent}")
    else:
        # Use LLM for classification with Ollama-optimized prompt
        try:
            # Use formatted prompt from templates
            prompt = format_router_prompt(user_input, user_language)
            
            response = llm.invoke(
                [HumanMessage(content=prompt)],
                config=_get_langsmith_config()
            )
            
            intent = _extract_intent_from_response(response.content)
            trace_entry["intent"] = intent
            trace_entry["method"] = "llm"
            trace_entry["llm_response"] = response.content[:200]
            trace_entry["agent_name"] = "router_agent"
            trace_entry["action"] = "classify_intent"
            trace_entry["language"] = user_language
            print(f"[Router Agent] LLM intent: {intent}")
            
        except Exception as e:
            print(f"[Router Agent] LLM error: {e}")
            intent = _rule_based_intent(user_input)
            trace_entry["intent"] = intent
            trace_entry["method"] = "fallback"
            trace_entry["agent_name"] = "router_agent"
            trace_entry["action"] = "classify_intent_fallback"

    
    # Update state with intent
    state["intent_type"] = intent
    state["current_intent"] = intent
    
    # Add observability metadata for LangSmith
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["intent_type"] = intent
    state["metadata"]["language"] = user_language
    state["metadata"]["agent_name"] = "router_agent"
    state["metadata"]["action"] = "intent_classification"
    state["metadata"]["router_agent"] = "completed"
    
    state["agent_trace"].append(trace_entry)
    
    return state



def _rule_based_intent(user_input: str) -> str:
    """Rule-based intent classification fallback."""
    text_lower = user_input.lower().strip()
    
    # GREETING
    greeting_keywords = ["hi", "hello", "hey", "namaste", "namaskar", "good morning", "good evening", "thanks", "thank you"]
    for kw in greeting_keywords:
        if kw in text_lower and len(text_lower) < 20:
            return "GREETING"
    
    # MEDICINE ORDER
    order_keywords = ["order", "buy", "purchase", "get", "want", "need", "place order", "order now"]
    for kw in order_keywords:
        if kw in text_lower:
            return "MEDICINE_ORDER"
    
    # SYMPTOM_QUERY - check these before general keywords
    symptom_keywords = ["fever", "cough", "cold", "pain", "headache", "stomach", "vomit", "diarrhea", "allergy", "tired", "weak", "sick", "unwell", "symptom", "feeling"]
    for kw in symptom_keywords:
        if kw in text_lower:
            return "SYMPTOM_QUERY"
    
    # MEDICAL_INFORMATION
    info_keywords = ["information", "info", "details", "tell me about", "what is", "how does", "explain", "prescription", "side effects", "uses", "benefits", "dosage"]
    for kw in info_keywords:
        if kw in text_lower:
            return "MEDICAL_INFORMATION"
    
    # MEDICINE_RECOMMENDATION
    recommend_keywords = ["suggest", "recommend", "which medicine", "what medicine", "what should i take", "please suggest", "recommend me"]
    for kw in recommend_keywords:
        if kw in text_lower:
            return "MEDICINE_RECOMMENDATION"
    
    # Default to general chat
    return "GENERAL_CHAT"
