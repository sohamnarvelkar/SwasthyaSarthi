"""
Unified LLM Provider with Ollama (local).
Uses only Ollama for local LLM inference.
Tracks all LLM calls with LangSmith for agent traceability.
"""
from langchain_ollama import ChatOllama
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


def _get_ollama_llm():
    """Get Ollama LLM (local)."""
    return ChatOllama(
        model="llama3:8b",
        temperature=0
    )


def get_llm():
    """
    Get an LLM instance using Ollama (local).
    Returns None if Ollama is not available.
    """
    global _llm, _llm_type
    
    if _llm is not None:
        return _llm
    
    # Try Ollama (local LLM)
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
