"""
Safety Agent - Validates stock and prescription requirements, or provides medicine information.
Uses LangSmith observability for traceability.
"""
from tools.inventory_tool import get_medicine
from agents.state_schema import AgentState
from agents.llm_provider import invoke_with_trace, is_tracing_enabled
from agents.confirmation_agent import create_confirmation_message

# Human-friendly medicine information templates
MEDICINE_INFO_TEMPLATES = {
    "en": {
        "found": "Great news! We have {product} available. Here are the details:\n\n📦 **Stock:** {stock} units available\n💰 **Price:** ₹{price}\n{prescription}\n\nWould you like to place an order for this medicine?",
        "not_found": "I couldn't find '{product}' in our inventory. Would you like me to check for alternatives or help you with something else?",
        "out_of_stock": "I found {product}, but unfortunately it's currently out of stock. We have {stock} units available. Would you like me to notify you when it's back in stock?",
        "prescription_info": "ℹ️ **Prescription Required:** Yes, you'll need a doctor's prescription to purchase this medicine.",
        "no_prescription": "ℹ️ **Prescription Required:** No, you can purchase this medicine without a prescription."
    },
    "hi": {
        "found": "बहुत अच्छी खबर! हमारे पास {product} उपलब्ध है। यहां विवरण हैं:\n\n📦 **स्टॉक:** {stock} यूनिट उपलब्ध\n💰 **कीमत:** ₹{price}\n{prescription}\n\nक्या आप इस दवा का ऑर्डर देना चाहेंगे?",
        "not_found": "मुझे हमारी इन्वेंटरी में '{product}' नहीं मिला। क्या आप विकल्पों की जांच करना चाहेंगे?",
        "out_of_stock": "मुझे {product} मिला, लेकिन दुर्भाग्य से यह currently out of stock है।",
        "prescription_info": "ℹ️ **नुस्खा आवश्यक:** हां, इस दवा को खरीदने के लिए डॉक्टर का नुस्खा आवश्यक होगा।",
        "no_prescription": "ℹ️ **नुस्खा आवश्यक:** नहीं, आप इस दवा को बिना नुस्खे के खरीद सकते हैं।"
    },
    "mr": {
        "found": "छान! आमच्याकडे {product} उपलब्ध आहे. तपशील खालीलप्रमाणे:\n\n📦 **स्टॉक:** {stock} युनिट उपलब्ध\n💰 **किंमत:** ₹{price}\n{prescription}\n\nतुम्हाला या औषधाचा ऑर्डर द्यायचा आहे का?",
        "not_found": "मला आमच्या इन्व्हेंटरीमध्ये '{product}' सापडले नाही.",
        "out_of_stock": "मला {product} सापडले, पण दुर्दैवी ते स्टॉकमध्ये नाही.",
        "prescription_info": "ℹ️ **पावती आवश्यक:** होय, तुम्हाला डॉक्टरची पावती लागेल.",
        "no_prescription": "ℹ️ **पावती आवश्यक:** नाही, तुम्हाला पावतीशिवाय हे औषध मिळेल."
    }
}

def _get_medicine_info(user_language: str, med: dict, product_name: str) -> str:
    """Get medicine information in the user's language."""
    lang_code = user_language if user_language in MEDICINE_INFO_TEMPLATES else "en"
    templates = MEDICINE_INFO_TEMPLATES.get(lang_code, MEDICINE_INFO_TEMPLATES["en"])
    
    stock = med.get("stock", 0)
    price = med.get("price", 0)
    prescription = templates["prescription_info"] if med.get("prescription_required") else templates["no_prescription"]
    
    if stock > 0:
        return templates["found"].format(
            product=product_name,
            stock=stock,
            price=price,
            prescription=prescription
        )
    else:
        return templates["out_of_stock"].format(
            product=product_name,
            stock=stock
        )


def safety_agent(state: AgentState) -> AgentState:
    """
    Check stock and prescription requirements OR provide medicine information.
    Uses LangSmith tracing to show validation chain of thought.
    If user is just asking about a medicine (not ordering), provides info instead.
    If ordering, validates and sets up confirmation request for the user.
    """
    # Initialize agent trace for observability
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    order = state.get("structured_order", {})
    name = order.get("product_name", "")
    qty = order.get("quantity", 0)
    user_language = state.get("user_language", "en")
    
    # Check if user is just asking for info (not placing order)
    is_order_request = state.get("is_order_request", True)

    # Get medicine details from inventory
    med = get_medicine(name)
    
    # Trace entry for observability
    trace_entry = {
        "agent": "safety_agent",
        "step": "validate_order" if is_order_request else "provide_info",
        "product": name,
        "quantity": qty,
        "medicine_found": med is not None,
        "is_order_request": is_order_request
    }

    if is_order_request:
        # Order request flow - validate and confirm
        result = _handle_order_validation(state, med, name, qty, user_language, trace_entry)
    else:
        # Information request flow - provide medicine details
        result = _handle_info_request(state, med, name, user_language, trace_entry)

    state["agent_trace"].append(trace_entry)
    
    # Log final trace
    if is_tracing_enabled():
        print(f"[Safety Agent] Full trace: {trace_entry}")
    
    return result


def _handle_order_validation(state: AgentState, med: dict, name: str, qty: int, user_language: str, trace_entry: dict) -> AgentState:
    """Handle order validation and confirmation setup."""
    result = {"approved": False, "reason": ""}
    
    if not med:
        result["reason"] = "not_found"
        trace_entry["result"] = "not_found"
        print(f"[Safety Agent] Medicine not found: {name}")
        state["safety_result"] = result
        state["final_response"] = f"I couldn't find '{name}' in our inventory. Could you please check the name or ask for alternatives?"
    elif med.get("stock", 0) < qty:
        result["reason"] = "out_of_stock"
        trace_entry["result"] = "out_of_stock"
        trace_entry["available_stock"] = med.get("stock")
        print(f"[Safety Agent] Out of stock: {name} (available: {med.get('stock')}, requested: {qty})")
        state["safety_result"] = result
        state["final_response"] = f"I found {name}, but we only have {med.get('stock')} units in stock. Would you like to order a smaller quantity or wait for restock?"
    elif med.get("prescription_required", False):
        result["reason"] = "prescription_required"
        trace_entry["result"] = "prescription_required"
        print(f"[Safety Agent] Prescription required: {name}")
        state["safety_result"] = result
        state["final_response"] = f"I found {name}, but it requires a doctor's prescription. Would you like to place the order and visit with your prescription?"
    else:
        result["approved"] = True
        trace_entry["result"] = "approved"
        print(f"[Safety Agent] Approved: {name} (stock: {med.get('stock')})")
        
        # If approved, set up confirmation request for the user
        confirmation_msg = create_confirmation_message(state, user_language)
        
        # Set confirmation state
        state["requires_confirmation"] = True
        state["confirmation_message"] = confirmation_msg
        state["pending_order_details"] = {
            "product_name": name,
            "quantity": qty,
            "price": med.get("price", 0),
            "stock": med.get("stock", 0)
        }
        
        # Update trace
        trace_entry["confirmation_setup"] = True
        trace_entry["confirmation_message"] = confirmation_msg
        state["safety_result"] = result
    
    return state


def _handle_info_request(state: AgentState, med: dict, name: str, user_language: str, trace_entry: dict) -> AgentState:
    """Handle information request - provide medicine details without ordering."""
    trace_entry["step"] = "provide_medicine_info"
    
    if not med:
        trace_entry["result"] = "not_found"
        print(f"[Safety Agent] Medicine info not found: {name}")
        lang_code = user_language if user_language in MEDICINE_INFO_TEMPLATES else "en"
        templates = MEDICINE_INFO_TEMPLATES.get(lang_code, MEDICINE_INFO_TEMPLATES["en"])
        state["final_response"] = templates["not_found"].format(product=name)
        state["safety_result"] = {"approved": False, "reason": "not_found"}
    else:
        trace_entry["result"] = "info_provided"
        print(f"[Safety Agent] Providing info for: {name}")
        
        # Get medicine information in user's language
        info_response = _get_medicine_info(user_language, med, name)
        state["final_response"] = info_response
        state["safety_result"] = {"approved": True, "reason": "info_provided"}
    
    return state
