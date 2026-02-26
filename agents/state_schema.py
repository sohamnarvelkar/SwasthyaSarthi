from typing import TypedDict, List, Any, Optional

class AgentState(TypedDict):
    # User info
    user_input: str
    user_id: str
    user_email: str
    user_phone: str
    user_address: str
    user_language: str
    
    # Order info
    structured_order: dict
    safety_result: dict
    final_response: str
    
    # Order vs Info request detection
    is_order_request: bool
    
    # Info request fields
    info_product: str
    info_response: str
    
    # Confirmation flow
    requires_confirmation: bool
    confirmation_message: str
    user_confirmed: Optional[bool]
    pending_order_details: Optional[dict]
    
    # Proactive features
    is_proactive: bool
    refill_alerts: List[Any]
    
    # Observability - tracing agent interactions
    agent_trace: List[dict]
