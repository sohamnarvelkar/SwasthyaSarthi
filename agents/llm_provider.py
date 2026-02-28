"""
Gemini LLM Provider for SwasthyaSarthi.
Uses Google Gemini as the primary LLM with fallback to rule-based responses.

Model Selection:
- Gemini 1.5 Flash: Simple conversations, routing, voice
- Gemini 1.5 Pro: Complex reasoning, medical advice, prescriptions

When Gemini is unavailable, the system falls back to rule-based responses.
"""
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "swasthya-sarthi")

# Check for Gemini configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_AVAILABLE = bool(GOOGLE_API_KEY)

# Don't raise error - just log warning and use fallback
if not GEMINI_AVAILABLE:
    print("[LLM Provider] WARNING: GOOGLE_API_KEY not set. Using rule-based fallback.")
    print("[LLM Provider] To enable AI features, add GOOGLE_API_KEY to your .env file")
else:
    print("[LLM Provider] Gemini API key detected - AI features enabled")

# LangSmith configuration
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"[Observability] LangSmith enabled - Project: {LANGSMITH_PROJECT}")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print("[Observability] LangSmith not configured - set LANGSMITH_API_KEY for tracing")

# LLM type 
_llm_type = "gemini" if GEMINI_AVAILABLE else "rule_based"
print(f"[LLM Provider] Mode: {'Gemini AI' if GEMINI_AVAILABLE else 'Rule-based fallback'}")


def _get_langsmith_config(model_type: str = "gemini"):
    """Get LangSmith configuration with model type tracking."""
    if LANGSMITH_API_KEY:
        return RunnableConfig(
            configurable={
                "tags": ["swasthya-sarthi", "pharmacy-agent", model_type],
                "metadata": {
                    "project": "swasthya-sarthi",
                    "environment": "production",
                    "llm_provider": model_type,
                    "model": "gemini-1.5-flash" if model_type == "flash" else "gemini-1.5-pro"
                }
            }
        )
    return RunnableConfig()


def get_llm():
    """
    Get Gemini service client.
    
    Returns:
        Gemini service instance or None if not available
    """
    if not GEMINI_AVAILABLE:
        print("[LLM Provider] Gemini not available - returning None")
        return None
    
    try:
        from backend.services import gemini_service
        if gemini_service.is_gemini_available():
            print("[LLM Provider] Using Gemini")
            return gemini_service
        else:
            print("[LLM Provider] Gemini service not available - returning None")
            return None
    except Exception as e:
        print(f"[LLM Provider] Error getting Gemini service: {e}")
        return None


def invoke_with_trace(prompt: str, agent_name: str = "agent", model_type: str = "flash"):
    """
    Invoke LLM with full LangSmith tracing.
    
    Args:
        prompt: User prompt
        agent_name: Name of the agent for tracing
        model_type: "flash" or "pro" for Gemini
    
    Returns:
        Generated response or None
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        from backend.services import gemini_service
        
        response = gemini_service.generate_response_simple(
            prompt=prompt,
            temperature=0.4,
            model_type=model_type
        )
        return response
    except Exception as e:
        print(f"[LLM Provider] invoke_with_trace error: {e}")
        return None


def is_llm_available_check():
    """Check if Gemini is available."""
    return GEMINI_AVAILABLE


def get_llm_type():
    """Get the current LLM type."""
    return _llm_type


def is_tracing_enabled():
    """Check if LangSmith tracing is enabled."""
    return LANGSMITH_API_KEY is not None


def reset_llm():
    """Reset the Gemini instance."""
    from backend.services import gemini_service
    gemini_service.reset_gemini()
    print("[LLM Provider] Gemini instance reset")


# Convenience functions that agents can use

def generate_response(messages, model_type: str = "flash", **kwargs):
    """
    Generate response using Gemini.
    
    Args:
        messages: List of messages
        model_type: "flash" or "pro"
        **kwargs: Additional parameters
    
    Returns:
        Generated response text or None
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        from backend.services import gemini_service
        
        return gemini_service.generate_response(
            messages=messages,
            model_type=model_type,
            **kwargs
        )
    except Exception as e:
        print(f"[LLM Provider] generate_response error: {e}")
        return None


def generate_response_simple(prompt: str, model_type: str = "flash", **kwargs):
    """
    Simple response generation using Gemini.
    
    Args:
        prompt: User prompt
        model_type: "flash" or "pro"
        **kwargs: Additional parameters
    
    Returns:
        Generated response text or None
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        from backend.services import gemini_service
        
        return gemini_service.generate_response_simple(
            prompt=prompt,
            model_type=model_type,
            **kwargs
        )
    except Exception as e:
        print(f"[LLM Provider] generate_response_simple error: {e}")
        return None


def generate_structured_json(prompt: str, model_type: str = "flash", **kwargs):
    """
    Generate structured JSON response using Gemini.
    
    Args:
        prompt: User prompt
        model_type: "flash" or "pro"
        **kwargs: Additional parameters
    
    Returns:
        Parsed JSON dictionary
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        from backend.services import gemini_service
        
        return gemini_service.generate_structured_json(
            prompt=prompt,
            model_type=model_type,
            **kwargs
        )
    except Exception as e:
        print(f"[LLM Provider] generate_structured_json error: {e}")
        return None
