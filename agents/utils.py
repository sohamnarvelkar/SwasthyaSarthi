"""Utility functions for agent state management."""

from agents.state_schema import AgentState


def create_initial_state(
    user_input: str,
    user_id: str = "PAT001",
    user_email: str = "patient@example.com",
    user_phone: str = "+1234567890",
    user_address: str = "Default Address",
    language: str = "English"
) -> AgentState:
    """
    Create an initial agent state with all required fields.
    
    Args:
        user_input: The raw user input text
        user_id: The patient's ID
        user_email: The patient's email
        user_phone: The patient's phone number
        user_address: The delivery address
        language: The preferred language
    
    Returns:
        AgentState: Initialized state dictionary
    """
    return {
        "user_input": user_input,
        "user_id": user_id,
        "user_email": user_email,
        "user_phone": user_phone,
        "user_address": user_address,
        "language": language,
        "structured_order": {},
        "safety_result": {},
        "final_response": ""
    }
