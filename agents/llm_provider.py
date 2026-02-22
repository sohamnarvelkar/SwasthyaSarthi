"""
Unified LLM Provider with LangSmith Observability.
Tries Anthropic first, then falls back to rule-based parsing if it fails.
Tracks all LLM calls with LangSmith for agent traceability.
"""
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
import os
import warnings

# Suppress LangSmith warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "swasthya-sarthi")

# Enable LangSmith tracing if API key is available
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"[Observability] LangSmith enabled - Project: {LANGSMITH_PROJECT}")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print("[Observability] LangSmith not configured - set LANGSMITH_API_KEY for tracing")

# Global LLM instance
_llm = None
_llm_type = None


def _get_langsmith_config():
    """Get LangSmith tracer configuration."""
    if LANGSMITH_API_KEY:
        return RunnableConfig(
            configurable={
                "tags": ["swasthya-sarthi", "pharmacy-agent"],
                "metadata": {
                    "project": "swasthya-sarthi",
                    "environment": "production"
                }
            }
        )
    return RunnableConfig()


def _get_anthropic_llm():
    """Get Anthropic LLM with LangSmith observability."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=api_key,
        temperature=0
    )


def _get_openai_llm():
    """Get OpenAI LLM with LangSmith observability."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=api_key
    )


def _get_ollama_llm():
    """Get Ollama LLM (local) - only if available."""
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model="llama3.2",
            temperature=0
        )
    except ImportError as e:
        print(f"[LLM Provider] Ollama import error: {e}")
        raise


def get_llm():
    """
    Get an LLM instance with automatic fallback.
    Tries Anthropic first, then OpenAI, then falls back to Ollama or rule-based.
    All LLM calls are traced via LangSmith.
    """
    global _llm, _llm_type
    
    if _llm is not None:
        return _llm
    
    # Try Anthropic first
    try:
        _llm = _get_anthropic_llm()
        _llm_type = "anthropic"
        
        # Test the LLM with a simple call
        test_response = _llm.invoke(
            [HumanMessage(content="Hi")],
            config=_get_langsmith_config()
        )
        print(f"[LLM Provider] Using Anthropic Claude with LangSmith tracing")
        return _llm
    except Exception as e:
        error_msg = str(e).lower()
        if "credit" in error_msg or "insufficient" in error_msg or "billing" in error_msg:
            print(f"[LLM Provider] Anthropic credits issue: {e}")
            print(f"[LLM Provider] Trying OpenAI...")
        elif "invalid_request_error" in error_msg:
            print(f"[LLM Provider] Anthropic error: {e}")
            print(f"[LLM Provider] Trying OpenAI...")
        else:
            print(f"[LLM Provider] Anthropic error: {e}")
            print(f"[LLM Provider] Trying OpenAI...")
    
    # Try OpenAI as fallback
    try:
        _llm = _get_openai_llm()
        _llm_type = "openai"
        
        # Test the LLM
        test_response = _llm.invoke(
            [HumanMessage(content="Hi")],
            config=_get_langsmith_config()
        )
        print(f"[LLM Provider] Using OpenAI GPT-4o with LangSmith tracing")
        return _llm
    except Exception as e:
        print(f"[LLM Provider] OpenAI error: {e}")
        print(f"[LLM Provider] Trying Ollama...")
    
    # Try Ollama as fallback
    try:
        _llm = _get_ollama_llm()
        _llm_type = "ollama"
        
        # Test the LLM
        test_response = _llm.invoke([HumanMessage(content="Hi")])
        print(f"[LLM Provider] Using Ollama (local)")
        return _llm
    except Exception as e:
        print(f"[LLM Provider] Ollama not available: {e}")
        print(f"[LLM Provider] Using rule-based fallback (no LLM)")
        _llm = None
        _llm_type = "none"
        return None


def invoke_with_trace(prompt: str, agent_name: str = "agent"):
    """
    Invoke LLM with full LangSmith tracing.
    Use this for agent steps to see chain of thoughts in LangSmith dashboard.
    """
    llm = get_llm()
    if llm is None:
        return None
    
    config = _get_langsmith_config()
    config["configurable"]["tags"].append(agent_name)
    
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config=config
        )
        return response.content
    except Exception as e:
        print(f"[invoke_with_trace] Error: {e}")
        return None


def is_llm_available():
    """Check if any LLM is available."""
    try:
        llm = get_llm()
        return llm is not None
    except:
        return False


def get_llm_type():
    """Get the current LLM type."""
    global _llm_type
    return _llm_type


def is_tracing_enabled():
    """Check if LangSmith tracing is enabled."""
    return LANGSMITH_API_KEY is not None


def reset_llm():
    """Reset the LLM instance (useful for testing)."""
    global _llm, _llm_type
    _llm = None
    _llm_type = None
