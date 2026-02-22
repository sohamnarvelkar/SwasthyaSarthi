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
    If approved, place the order and set a success message (in user's language).
    Also sends order confirmations via configured channels.
    Uses LangSmith tracing for full observability.
    """
    safety = state.get("safety_result", {})
    
    # Trace the execution decision
    if is_tracing_enabled():
        trace_prompt = f"""Execution Decision:
- Safety Approved: {safety.get("approved")}
- Order Details: {state.get("structured_order")}
- Patient: {state.get("user_id", "PAT001")}

Determine the final response to return to the user."""
        trace_result = invoke_with_trace(trace_prompt, agent_name="execution")
        print(f"[Execution Agent] Trace result: {trace_result}")
    
    if safety.get("approved"):
        order = state.get("structured_order", {})
        patient_id = state.get("user_id", "PAT001")
        product_name = order.get("product_name", "")
        quantity = order.get("quantity", 1)
        
        if not product_name:
            state["final_response"] = "Could not process your request. No product specified."
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
                print(f"[Execution Agent] Notification results: {notification_results}")
            except Exception as e:
                print(f"[Execution Agent] Notification error: {e}")
            
            total_price = res.get("price", 0)
            state["final_response"] = f"Order placed successfully! Total price: ₹{total_price:.2f}. You will receive a confirmation email/SMS shortly."
            print(f"[Execution Agent] Order success: {res.get('order_id')}")
        else:
            state["final_response"] = "Failed to place order. Please try again."
            print(f"[Execution Agent] Order failed: {res}")
    else:
        reason = safety.get("reason", "")
        if reason == "prescription_required":
            state["final_response"] = "Prescription is required to place this order."
        elif reason == "out_of_stock":
            state["final_response"] = "Sorry, this item is out of stock."
        elif reason == "not_found":
            state["final_response"] = "Sorry, we couldn't find that medicine in our inventory."
        else:
            state["final_response"] = "Could not process your request."
        print(f"[Execution Agent] Order rejected: {reason}")
    
    return state
