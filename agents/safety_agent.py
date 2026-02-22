"""
Safety Agent - Validates stock and prescription requirements.
Uses LangSmith observability for traceability.
"""
from tools.inventory_tool import get_medicine
from agents.state_schema import AgentState
from agents.llm_provider import invoke_with_trace, is_tracing_enabled

def safety_agent(state: AgentState) -> AgentState:
    """
    Check stock and prescription requirements.
    Uses LangSmith tracing to show validation chain of thought.
    """
    order = state.get("structured_order", {})
    name = order.get("product_name", "")
    qty = order.get("quantity", 0)

    # Get medicine details from inventory
    med = get_medicine(name)

    result = {"approved": False, "reason": ""}
    
    # Trace the safety check reasoning
    if is_tracing_enabled():
        trace_prompt = f"""Safety Check for Order:
- Product: {name}
- Quantity: {qty}
- Medicine Found: {med is not None}

Evaluate and return:
{{"approved": true/false, "reason": "explanation"}}"""
        trace_result = invoke_with_trace(trace_prompt, agent_name="safety")
        print(f"[Safety Agent] Trace result: {trace_result}")

    if not med:
        result["reason"] = "not_found"
        print(f"[Safety Agent] Medicine not found: {name}")
    elif med.get("stock", 0) < qty:
        result["reason"] = "out_of_stock"
        print(f"[Safety Agent] Out of stock: {name} (available: {med.get('stock')}, requested: {qty})")
    elif med.get("prescription_required", False):
        result["reason"] = "prescription_required"
        print(f"[Safety Agent] Prescription required: {name}")
    else:
        result["approved"] = True
        print(f"[Safety Agent] Approved: {name} (stock: {med.get('stock')})")

    state["safety_result"] = result
    return state
