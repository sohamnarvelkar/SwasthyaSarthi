"""
Execution Agent - Places orders and triggers notifications.
Uses LangSmith observability for traceability.
"""
from tools.order_tool import create_order
from tools.webhook_tool import trigger_fulfillment, trigger_order_notifications
from agents.state_schema import AgentState
from agents.llm_provider import invoke_with_trace, is_tracing_enabled


def execution_agent(state: AgentState) -> AgentState:
    """
    If approved and confirmed by user, place the order and set a success message.
    Also sends order confirmations via configured channels.
    Uses LangSmith tracing for full observability.
    """
    # Initialize agent trace for observability
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    safety = state.get("safety_result", {})
    requires_confirmation = state.get("requires_confirmation", False)
    user_confirmed = state.get("user_confirmed")
    
    # Trace entry for observability
    trace_entry = {
        "agent": "execution_agent",
        "step": "execute_order",
        "safety_approved": safety.get("approved"),
        "requires_confirmation": requires_confirmation,
        "user_confirmed": user_confirmed
    }
    
    # Trace the execution decision
    if is_tracing_enabled():
        trace_prompt = f"""Execution Decision:
- Safety Approved: {safety.get("approved")}
- Requires Confirmation: {requires_confirmation}
- User Confirmed: {user_confirmed}
- Order Details: {state.get("structured_order")}
- Patient: {state.get("user_id", "PAT001")}

Determine the final response to return to the user."""
        trace_result = invoke_with_trace(trace_prompt, agent_name="execution")
        trace_entry["llm_trace"] = trace_result
        print(f"[Execution Agent] Trace result: {trace_result}")
    
    # Check if order was rejected by safety
    if not safety.get("approved"):
        reason = safety.get("reason", "")
        if reason == "prescription_required":
            state["final_response"] = "Prescription is required to place this order."
        elif reason == "out_of_stock":
            state["final_response"] = "Sorry, this item is out of stock."
        elif reason == "not_found":
            state["final_response"] = "Sorry, we couldn't find that medicine in our inventory."
        else:
            state["final_response"] = "Could not process your request."
        trace_entry["result"] = "rejected"
        trace_entry["reason"] = reason
        print(f"[Execution Agent] Order rejected: {reason}")
        state["agent_trace"].append(trace_entry)
        return state
    
    # If confirmation is required but user hasn't confirmed yet
    if requires_confirmation and user_confirmed is None:
        # Ask for confirmation
        confirmation_msg = state.get("confirmation_message", "Please confirm your order.")
        state["final_response"] = confirmation_msg
        trace_entry["result"] = "awaiting_confirmation"
        state["agent_trace"].append(trace_entry)
        return state
    
    # If user declined the confirmation
    if requires_confirmation and user_confirmed is False:
        state["final_response"] = "Order cancelled as per your request. Let me know if you need anything else!"
        trace_entry["result"] = "cancelled_by_user"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Proceed with order placement (user has confirmed or no confirmation needed)
    order = state.get("structured_order", {})
    patient_id = state.get("user_id", "PAT001")
    product_name = order.get("product_name", "")
    quantity = order.get("quantity", 1)
    
    if not product_name:
        state["final_response"] = "Could not process your request. No product specified."
        trace_entry["result"] = "no_product"
        state["agent_trace"].append(trace_entry)
        return state
    
    print(f"[Execution Agent] Creating order: {product_name} x{quantity} for {patient_id}")
    res = create_order(patient_id, product_name, quantity)
    
    if res.get("status") == "success":
        # Trigger fulfillment webhook
        trigger_fulfillment(f"{patient_id}-{product_name}")
        
        # Prepare order details for notifications
        order_details = {
            "order_id": res.get("order_id", f"{patient_id}-{product_name}"),
            "patient_id": patient_id,
            "items": [{
                "name": product_name,
                "quantity": quantity,
                "price": res.get("price", 0)
            }],
            "total": res.get("price", 0),
            "date": res.get("date", "Now"),
            "customer_email": state.get("user_email", "customer@example.com"),
            "customer_phone": state.get("user_phone", "+1234567890"),
            "address": state.get("user_address", "Default Address"),
            "status": "confirmed"
        }
        
        # Send notifications via all configured channels
        try:
            notification_results = trigger_order_notifications(
                order_details=order_details,
                channels=["email", "sms", "webhook"]
            )
            trace_entry["notifications_sent"] = notification_results
            print(f"[Execution Agent] Notification results: {notification_results}")
        except Exception as e:
            print(f"[Execution Agent] Notification error: {e}")
        
        total_price = res.get("price", 0)
        state["final_response"] = f"Order placed successfully! Total price: ₹{total_price:.2f}. You will receive a confirmation email shortly."
        trace_entry["result"] = "success"
        trace_entry["order_id"] = res.get("order_id")
        print(f"[Execution Agent] Order success: {res.get('order_id')}")
    else:
        state["final_response"] = "Failed to place order. Please try again."
        trace_entry["result"] = "failed"
        trace_entry["error"] = str(res)
        print(f"[Execution Agent] Order failed: {res}")
    
    state["agent_trace"].append(trace_entry)
    return state
