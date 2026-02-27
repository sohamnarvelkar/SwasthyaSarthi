"""
Execution Agent - Places orders and triggers notifications.
Uses LangSmith observability for traceability.
"""
from tools.order_tool import create_order
from tools.webhook_tool import trigger_fulfillment, trigger_order_notifications
from tools.inventory_tool import get_medicine
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
    
    # Fetch medicine info from inventory to get price from dataset
    print(f"[Execution Agent] Fetching price for: {product_name}")
    med_info = get_medicine(product_name)
    
    if not med_info:
        state["final_response"] = f"Sorry, we couldn't find '{product_name}' in our inventory."
        trace_entry["result"] = "medicine_not_found"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Validate price is available from dataset
    unit_price = med_info.get("price")
    if unit_price is None or unit_price <= 0:
        state["final_response"] = f"Sorry, price information is not available for '{product_name}'. Cannot process order."
        trace_entry["result"] = "price_not_available"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Calculate total price
    total_price = round(unit_price * quantity, 2)
    
    # Store price details in agent state for observability
    state["order_price_details"] = {
        "unit_price": unit_price,
        "total_price": total_price,
        "currency": "INR",
        "product_name": product_name,
        "quantity": quantity
    }
    
    print(f"[Execution Agent] Creating order: {product_name} x{quantity} for {patient_id} at ₹{total_price}")
    res = create_order(patient_id, product_name, quantity)

    
    if res.get("status") == "success":
        # Trigger fulfillment webhook
        trigger_fulfillment(f"{patient_id}-{product_name}")
        
        # Prepare order details for notifications with price info
        order_details = {
            "order_id": res.get("order_id", f"{patient_id}-{product_name}"),
            "patient_id": patient_id,
            "items": [{
                "name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price
            }],
            "unit_price": unit_price,
            "total_price": total_price,
            "total": total_price,
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
        
        # Build detailed response with price breakdown
        state["final_response"] = (
            f"Your order has been placed successfully!\n\n"
            f"📋 Order Details:\n"
            f"• Medicine: {product_name}\n"
            f"• Quantity: {quantity}\n"
            f"• Price per unit: ₹{unit_price:.2f}\n"
            f"• Total Price: ₹{total_price:.2f}\n\n"
            f"You will receive a confirmation email shortly."
        )
        
        # Add LangSmith observability metadata with pricing
        trace_entry["result"] = "success"
        trace_entry["order_id"] = res.get("order_id")
        trace_entry["action"] = "order_created"
        trace_entry["unit_price"] = unit_price
        trace_entry["total_price"] = total_price
        trace_entry["currency"] = "INR"
        
        # Update metadata for LangSmith
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["action"] = "order_created"
        state["metadata"]["unit_price"] = unit_price
        state["metadata"]["total_price"] = total_price
        state["metadata"]["currency"] = "INR"
        
        print(f"[Execution Agent] Order success: {res.get('order_id')} - Total: ₹{total_price}")

    else:
        state["final_response"] = "Failed to place order. Please try again."
        trace_entry["result"] = "failed"
        trace_entry["error"] = str(res)
        print(f"[Execution Agent] Order failed: {res}")
    
    state["agent_trace"].append(trace_entry)
    return state
