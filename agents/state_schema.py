from typing import TypedDict, List, Any

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
    
    # Proactive features
    is_proactive: bool
    refill_alerts: List[Any]
