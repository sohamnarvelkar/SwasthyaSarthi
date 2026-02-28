from typing import TypedDict, List, Any, Optional

class AgentState(TypedDict):
    # User info
    user_input: str
    user_id: str
    user_email: str
    user_phone: str
    user_address: str
    user_language: str
    
    # === ROUTER + SPECIALIST ARCHITECTURE ===
    # Intent classification
    intent_type: str
    current_intent: str
    detected_language: str
    
    # Session tracking
    session_id: str
    
    # Conversation memory references
    identified_symptoms: List[str]
    possible_conditions: List[str]
    medical_advice: str
    recommended_medicines: List[dict]
    
    # Metadata for observability
    metadata: dict
    
    # === ORDER FLOW (existing) ===
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

    # Drug interaction detection
    drug_interaction_warning: Optional[dict]

    # Alternative recommendations
    alternative_recommendations: Optional[List[dict]]

    # Procurement triggers
    procurement_triggered: Optional[bool]
    procurement_details: Optional[dict]

    # Price tracking for orders
    order_price_details: Optional[dict]

    # Observability - tracing agent interactions
    agent_trace: List[dict]
    
    # === DUAL KNOWLEDGE ARCHITECTURE (NEW) ===
    # Medicine source tracking (internal = dataset, external = non-dataset)
    medicine_source: str  # "internal" | "external" | "unknown"
    
    # Last discussed medicine for follow-up queries
    last_medicine_discussed: Optional[str]
    
    # External order tracking
    external_order_requested: bool
    external_order_created: bool
    external_order_id: Optional[str]
    external_order_details: Optional[dict]
    
    # Global medicine info (from LLM knowledge)
    global_medicine_info: Optional[dict]
    
    # Medicine availability info
    medicine_availability: Optional[dict]
