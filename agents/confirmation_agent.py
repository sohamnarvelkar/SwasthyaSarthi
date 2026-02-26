"""
Confirmation Agent - Handles order confirmation requests from users.
This agent asks for user confirmation before placing orders, making the 
interaction more human-friendly like ChatGPT.
"""
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Language-specific response templates
CONFIRMATION_TEMPLATES = {
    "en": {
        "confirm_prompt": 'You are confirming an order. The user said "{user_input}". Does this contain a confirmation word like "yes", "confirm", "place order", "order now", "proceed", "ok", "sure", "okay", "please do", "go ahead"? Return ONLY a JSON with keys: "confirmed" (true/false) and "response" (a friendly message).',
        "pending_message": "I understand you'd like to order {product} x {quantity}. Could you please confirm by saying 'yes' or 'confirm' to place this order? You can also say 'cancel' to abort."
    },
    "hi": {
        "confirm_prompt": 'आप एक ऑर्डर की पुष्टि कर रहे हैं। उपयोगकर्ता ने कहा "{user_input}"। क्या इसमें "yes", "confirm", "place order", "order now", "proceed", "ok", "sure" जैसा कोई शब्द है? केवल JSON रिटर्न करें: "confirmed" और "response"।',
        "pending_message": "मैं समझता हूं कि आप {product} x {quantity} ऑर्डर करना चाहेंगे। कृपया 'yes' या 'confirm' कहकर इस ऑर्डर की पुष्टि करें? आप 'cancel' भी कह सकते हैं।"
    },
    "mr": {
        "confirm_prompt": 'तुम एका ऑर्डरची पुष्टी करत आहात. वापरून म्हणाले "{user_input}". यात "yes", "confirm", "place order", "order now", "proceed", "ok", "sure" असा शब्द आहे का? फक्त JSON रिटर्न करा: "confirmed" आणि "response".',
        "pending_message": "मी समजतो तुम्हाला {product} x {quantity} ऑर्डर करायचा आहे. कृपया 'yes' किंवा 'confirm' म्हणून या ऑर्डरची पुष्टी करा. तुम 'cancel' सुद्धा म्हणू शकता."
    }
}

def _get_language_config(user_language: str) -> dict:
    """Get confirmation templates for the user's language."""
    return CONFIRMATION_TEMPLATES.get(user_language, CONFIRMATION_TEMPLATES["en"])


def _check_confirmation_with_llm(user_input: str, user_language: str = "en") -> dict:
    """
    Use LLM to determine if user has confirmed the order.
    This makes the interaction more natural and conversational.
    """
    llm = get_llm()
    lang_config = _get_language_config(user_language)
    
    if llm is None:
        # Fallback to rule-based check
        return _rule_based_confirmation_check(user_input)
    
    prompt = lang_config["confirm_prompt"].format(user_input=user_input)
    
    try:
        response_content = invoke_with_trace(prompt, agent_name="confirmation")
        
        if response_content is None:
            # Fallback
            return _rule_based_confirmation_check(user_input)
        
        # Try to parse JSON from response
        try:
            result = json.loads(response_content.strip())
            return result
        except:
            json_match = response_content.strip()
            if 'confirmed' in json_match.lower() and 'true' in json_match.lower():
                return {"confirmed": True, "response": "Order confirmed!"}
            elif 'confirmed' in json_match.lower() and 'false' in json_match.lower():
                return {"confirmed": False, "response": "Order not confirmed."}
            return _rule_based_confirmation_check(user_input)
    except Exception as e:
        print(f"[Confirmation Agent] LLM error: {e}")
        return _rule_based_confirmation_check(user_input)


def _rule_based_confirmation_check(user_input: str) -> dict:
    """
    Rule-based fallback for confirmation detection.
    Checks for common confirmation words.
    """
    user_input_lower = user_input.lower().strip()
    
    # Positive confirmation words
    positive_words = [
        "yes", "yeah", "yep", "sure", "ok", "okay", "okay!", "yes!",
        "confirm", "confirmed", "place order", "order now", "proceed",
        "go ahead", "do it", "please do", "please go ahead", "please",
        "absolutely", "definitely", "of course", "that's right", "correct",
        "please order", "order it", "buy it", "get it", "yes please"
    ]
    
    # Negative/Cancellation words
    negative_words = [
        "no", "nope", "not", "cancel", "abort", "stop", "don't", "do not",
        "wait", "later", "maybe", "think", "consider", "not now"
    ]
    
    # Check for positive confirmation
    for word in positive_words:
        if word in user_input_lower:
            return {
                "confirmed": True,
                "response": "Great! I'll place your order now."
            }
    
    # Check for negative/cancellation
    for word in negative_words:
        if word in user_input_lower:
            return {
                "confirmed": False,
                "response": "No problem! Your order has been cancelled. Let me know if you need anything else."
            }
    
    # Not clear - need more info
    return {
        "confirmed": None,
        "response": "I'm not sure if you want to confirm the order. Please say 'yes' to confirm or 'cancel' to abort."
    }


def confirmation_agent(state: AgentState) -> AgentState:
    """
    Agent that handles order confirmation flow.
    This makes the system ask user before placing orders,
    making it more human-friendly like ChatGPT.
    
    The agent:
    1. Checks if there's a pending order awaiting confirmation
    2. If user confirms (says yes/confirm), proceed with order
    3. If user declines (says no/cancel), cancel the order
    4. If unclear, ask for clarification
    """
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    requires_confirmation = state.get("requires_confirmation", False)
    pending_order = state.get("pending_order_details", {})
    
    # Initialize agent trace for observability
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    # Add this agent interaction to trace
    trace_entry = {
        "agent": "confirmation_agent",
        "step": "check_confirmation",
        "user_input": user_input,
        "requires_confirmation": requires_confirmation
    }
    
    if not requires_confirmation:
        # No pending order to confirm - normal flow
        trace_entry["action"] = "no_confirmation_needed"
        state["agent_trace"].append(trace_entry)
        return state
    
    if not user_input:
        # No user input yet - send confirmation message
        trace_entry["action"] = "requesting_confirmation"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Check user's response for confirmation
    confirmation_result = _check_confirmation_with_llm(user_input, user_language)
    
    trace_entry["confirmation_result"] = confirmation_result
    
    if confirmation_result.get("confirmed") is True:
        # User confirmed - proceed with order
        trace_entry["action"] = "confirmed"
        state["user_confirmed"] = True
        state["final_response"] = confirmation_result.get(
            "response", 
            "Great! Placing your order now..."
        )
        
    elif confirmation_result.get("confirmed") is False:
        # User declined - cancel order
        trace_entry["action"] = "declined"
        state["user_confirmed"] = False
        state["final_response"] = confirmation_result.get(
            "response",
            "Order cancelled. Let me know if you need anything else!"
        )
        # Clear pending order
        state["requires_confirmation"] = False
        state["pending_order_details"] = {}
        
    else:
        # Unclear response - ask for clarification
        trace_entry["action"] = "needs_clarification"
        state["user_confirmed"] = None
        state["final_response"] = confirmation_result.get(
            "response",
            "I'm not sure. Could you please confirm with 'yes' or 'cancel'?"
        )
    
    state["agent_trace"].append(trace_entry)
    
    # Log for observability
    if is_tracing_enabled():
        print(f"[Confirmation Agent] Trace: {trace_entry}")
    
    return state


def create_confirmation_message(state: AgentState, user_language: str = "en") -> str:
    """
    Create a friendly confirmation message for the user.
    This is called when a new order is being prepared.
    """
    order = state.get("structured_order", {})
    product = order.get("product_name", "this item")
    quantity = order.get("quantity", 1)
    
    lang_config = _get_language_config(user_language)
    
    message = lang_config["pending_message"].format(
        product=product,
        quantity=quantity
    )
    
    return message


__all__ = ["confirmation_agent", "create_confirmation_message"]
