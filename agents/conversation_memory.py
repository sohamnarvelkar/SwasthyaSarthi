"""
Conversation Memory - Stores conversation context for SwasthyaSarthi.
Maintains last symptoms, recommended medicines, intents for follow-up queries.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# In-memory conversation storage (per user session)
_conversation_store: Dict[str, Dict[str, Any]] = {}


def _get_session_key(user_id: str = "default", session_id: str = "default") -> str:
    """Generate unique session key."""
    return f"{user_id}:{session_id}"


def init_session(user_id: str = "default", session_id: str = "default") -> Dict[str, Any]:
    """
    Initialize a new conversation session.
    Returns the session data.
    """
    key = _get_session_key(user_id, session_id)
    
    _conversation_store[key] = {
        "user_id": user_id,
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "last_intent": None,
        "last_symptoms": [],
        "last_conditions": [],
        "recommended_medicines": [],
        "last_order": None,
        "conversation_history": [],
        "language": "en"
    }
    
    return _conversation_store[key]


def get_session(user_id: str = "default", session_id: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get existing session data.
    Creates new session if doesn't exist.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        return init_session(user_id, session_id)
    
    return _conversation_store[key]


def update_session(user_id: str, session_id: str, updates: Dict[str, Any]) -> None:
    """
    Update session with new data.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        init_session(user_id, session_id)
    
    _conversation_store[key].update(updates)


def add_message(user_id: str, session_id: str, role: str, content: str) -> None:
    """
    Add a message to conversation history.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        init_session(user_id, session_id)
    
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    _conversation_store[key]["conversation_history"].append(message)


def store_symptoms(user_id: str, session_id: str, symptoms: List[str], 
                   conditions: List[str] = None) -> None:
    """
    Store identified symptoms and possible conditions.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        init_session(user_id, session_id)
    
    _conversation_store[key]["last_symptoms"] = symptoms
    _conversation_store[key]["last_conditions"] = conditions or []
    _conversation_store[key]["symptoms_stored_at"] = datetime.now().isoformat()


def store_recommendations(user_id: str, session_id: str, medicines: List[Dict]) -> None:
    """
    Store recommended medicines from dataset.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        init_session(user_id, session_id)
    
    _conversation_store[key]["recommended_medicines"] = medicines
    _conversation_store[key]["recommendations_stored_at"] = datetime.now().isoformat()


def store_order(user_id: str, session_id: str, order_data: Dict) -> None:
    """
    Store order details.
    """
    key = _get_session_key(user_id, session_id)
    
    if key not in _conversation_store:
        init_session(user_id, session_id)
    
    _conversation_store[key]["last_order"] = order_data
    _conversation_store[key]["last_order_at"] = datetime.now().isoformat()


def get_last_symptoms(user_id: str = "default", session_id: str = "default") -> List[str]:
    """Get last identified symptoms."""
    session = get_session(user_id, session_id)
    return session.get("last_symptoms", [])


def get_last_recommendations(user_id: str = "default", session_id: str = "default") -> List[Dict]:
    """Get last recommended medicines."""
    session = get_session(user_id, session_id)
    return session.get("recommended_medicines", [])


def get_conversation_history(user_id: str = "default", session_id: str = "default") -> List[Dict]:
    """Get full conversation history."""
    session = get_session(user_id, session_id)
    return session.get("conversation_history", [])


def clear_session(user_id: str = "default", session_id: str = "default") -> None:
    """Clear session data."""
    key = _get_session_key(user_id, session_id)
    if key in _conversation_store:
        del _conversation_store[key]


def clear_all_sessions() -> None:
    """Clear all conversation sessions."""
    _conversation_store.clear()


# Quick access functions for agents
def has_symptoms(user_id: str = "default", session_id: str = "default") -> bool:
    """Check if session has stored symptoms."""
    session = get_session(user_id, session_id)
    return len(session.get("last_symptoms", [])) > 0


def has_recommendations(user_id: str = "default", session_id: str = "default") -> bool:
    """Check if session has stored recommendations."""
    session = get_session(user_id, session_id)
    return len(session.get("recommended_medicines", [])) > 0


def get_last_intent(user_id: str = "default", session_id: str = "default") -> str:
    """Get last intent type."""
    session = get_session(user_id, session_id)
    return session.get("last_intent", "GENERAL_CHAT")


def set_last_intent(user_id: str, session_id: str, intent: str) -> None:
    """Set last intent type."""
    key = _get_session_key(user_id, session_id)
    if key not in _conversation_store:
        init_session(user_id, session_id)
    _conversation_store[key]["last_intent"] = intent
