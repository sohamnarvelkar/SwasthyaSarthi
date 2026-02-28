"""
Gemini Service - Centralized LLM service for SwasthyaSarthi.
Uses Google Gemini models for AI processing.

Models:
- Gemini 1.5 Flash: Real-time conversations, routing, voice responses
- Gemini 1.5 Pro: Complex reasoning, medical advice, prescription analysis, multimodal

Key Features:
- Automatic model selection based on task complexity
- Multilingual support (English, Hindi, Marathi)
- Vision multimodal for prescription images
- Full observability with LangSmith tracing
"""
import google.generativeai as genai
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
import os
import json
import base64
import warnings
from typing import Optional, List, Dict, Any, Union

warnings.filterwarnings("ignore")
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "swasthya-sarthi")

# LangSmith configuration
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"[Gemini] LangSmith enabled - Project: {LANGSMITH_PROJECT}")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print("[Gemini] LangSmith not configured")

# Initialize Gemini client
_genai_configured = False
_flash_model = None
_pro_model = None


def _configure_genai():
    """Configure Google Generative AI with API key."""
    global _genai_configured, _flash_model, _pro_model
    
    if _genai_configured:
        return
    
    if not GOOGLE_API_KEY:
        print("[Gemini] WARNING: GOOGLE_API_KEY not set in environment")
        return
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        _flash_model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
        _pro_model = genai.GenerativeModel(GEMINI_PRO_MODEL)
        _genai_configured = True
        print(f"[Gemini] Configured - Flash: {GEMINI_FLASH_MODEL}, Pro: {GEMINI_PRO_MODEL}")
    except Exception as e:
        print(f"[Gemini] Configuration error: {e}")
        _genai_configured = False


def _get_langsmith_config(model_type: str = "flash"):
    """Get LangSmith configuration for tracing."""
    if LANGSMITH_API_KEY:
        return RunnableConfig(
            configurable={
                "tags": ["swasthya-sarthi", "pharmacy-agent", f"gemini_{model_type}"],
                "metadata": {
                    "project": "swasthya-sarthi",
                    "environment": "production",
                    "llm_provider": "gemini",
                    "model_type": model_type,
                    "model": GEMINI_FLASH_MODEL if model_type == "flash" else GEMINI_PRO_MODEL
                }
            }
        )
    return RunnableConfig()


# Language mapping for prompts
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi", 
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati"
}


def _add_language_instruction(system_prompt: str, language: Optional[str] = None) -> str:
    """Add multilingual instruction to system prompt."""
    if not language or language == "en":
        return system_prompt
    
    lang_name = LANGUAGE_MAP.get(language, "English")
    
    # Add language instruction to system prompt
    if "Respond in" not in system_prompt:
        system_prompt += f"\n\nIMPORTANT: Respond ONLY in {lang_name} language."
    
    return system_prompt


def _select_model(task_type: str) -> str:
    """
    Select appropriate model based on task type.
    
    Args:
        task_type: Type of task - "simple", "complex", "medical", "prescription", "voice"
    
    Returns:
        "flash" or "pro"
    """
    # Use Pro for complex medical tasks
    if task_type in ["complex", "medical", "prescription", "reasoning"]:
        return "pro"
    
    # Use Flash for simple tasks
    return "flash"


def generate_response(
    messages: List[Union[dict, HumanMessage, SystemMessage, AIMessage]],
    model_type: str = "flash",
    temperature: float = 0.4,
    max_tokens: int = 512,
    system_prompt: Optional[str] = None,
    language: Optional[str] = None
) -> Optional[str]:
    """
    Generate response using Gemini model.
    
    Args:
        messages: List of message dictionaries or LangChain message objects
        model_type: "flash" or "pro"
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        system_prompt: Optional system prompt
        language: Language code for response (en, hi, mr)
    
    Returns:
        Generated text response or None on error
    """
    _configure_genai()
    
    if not _genai_configured:
        print("[Gemini] Not configured - returning None")
        return None
    
    try:
        # Select model
        if model_type == "pro":
            model = _pro_model
        else:
            model = _flash_model
        
        # Build message list for Gemini
        gemini_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            system_prompt = _add_language_instruction(system_prompt, language)
            gemini_messages.append({"role": "user", "parts": [system_prompt]})
            # First message from model acknowledges the system
            gemini_messages.append({"role": "model", "parts": ["Understood. I will follow these instructions."]})
        
        # Add conversation history
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            elif isinstance(msg, HumanMessage):
                role = "user"
                content = msg.content
            elif isinstance(msg, AIMessage):
                role = "model"
                content = msg.content
            elif isinstance(msg, SystemMessage):
                # Skip system messages as we handle them separately
                continue
            else:
                role = "user"
                content = str(msg)
            
            gemini_messages.append({"role": role, "parts": [content]})
        
        # Generate response
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = model.generate_content(
            gemini_messages,
            generation_config=generation_config
        )
        
        if response and response.text:
            return response.text
        return None
        
    except Exception as e:
        print(f"[Gemini] Generate response error: {e}")
        return None


def generate_response_simple(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 512,
    model_type: str = "flash",
    language: Optional[str] = None
) -> Optional[str]:
    """
    Simple interface for generating a response from a single prompt.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        model_type: "flash" or "pro"
        language: Language code (en, hi, mr)
    
    Returns:
        Generated text response
    """
    _configure_genai()
    
    if not _genai_configured:
        print("[Gemini] Not configured - returning None")
        return None
    
    # Build system prompt with language instruction
    full_system = system_prompt or "You are a helpful pharmacy assistant."
    full_system = _add_language_instruction(full_system, language)
    
    messages = [
        {"role": "system", "content": full_system},
        {"role": "user", "content": prompt}
    ]
    
    return generate_response(
        messages=messages,
        model_type=model_type,
        temperature=temperature,
        max_tokens=max_tokens,
        language=language
    )


def generate_structured_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 512,
    model_type: str = "flash",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate structured JSON response.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        model_type: "flash" or "pro"
        language: Language code
    
    Returns:
        Parsed JSON dictionary
    """
    _configure_genai()
    
    if not _genai_configured:
        return {"error": "Gemini not configured"}
    
    # Build system prompt for JSON output
    json_system = system_prompt or "You are a structured data generator."
    json_system += " Return ONLY valid JSON with no additional text. Do not add explanations or markdown code blocks."
    json_system = _add_language_instruction(json_system, language)
    
    messages = [
        {"role": "system", "content": json_system},
        {"role": "user", "content": prompt}
    ]
    
    response = generate_response(
        messages=messages,
        model_type=model_type,
        temperature=temperature,
        max_tokens=max_tokens,
        language=language
    )
    
    if response:
        try:
            # Try to parse JSON
            # First, try direct parse
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # Try to find JSON in response
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
                return json.loads(json_str)
            
            return {"error": "No valid JSON found", "raw": response}
        except json.JSONDecodeError as e:
            print(f"[Gemini] JSON parse error: {e}")
            return {"error": "Failed to parse JSON", "raw": response}
    
    return {"error": "No response from Gemini"}


def analyze_image(
    image_data: bytes,
    prompt: str,
    system_prompt: Optional[str] = None,
    model_type: str = "pro",
    language: Optional[str] = None
) -> Optional[str]:
    """
    Analyze an image using Gemini Pro multimodal capabilities.
    
    Args:
        image_data: Image bytes
        prompt: Question about the image
        system_prompt: Optional system prompt
        model_type: Model to use (should be "pro" for images)
        language: Language code
    
    Returns:
        Text analysis of the image
    """
    _configure_genai()
    
    if not _genai_configured:
        print("[Gemini] Not configured - returning None")
        return None
    
    # Always use Pro for image analysis
    model = _pro_model
    
    try:
        # Build system prompt
        full_system = system_prompt or "You are a helpful pharmacy assistant that analyzes prescription images."
        full_system = _add_language_instruction(full_system, language)
        
        # Prepare image
        image_parts = [
            {"mime_type": "image/jpeg", "data": base64.b64encode(image_data).decode("utf-8")}
        ]
        
        # Build content with image and text
        content_parts = [prompt]
        
        response = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {"text": full_system},
                        {"inline_data": image_parts[0]}
                    ]
                }
            ]
        )
        
        if response and response.text:
            return response.text
        return None
        
    except Exception as e:
        print(f"[Gemini] Image analysis error: {e}")
        return None


def analyze_prescription_image(
    image_data: bytes,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Analyze a prescription image and extract medicines.
    
    Args:
        image_data: Image bytes
        language: Language code for response
    
    Returns:
        Dictionary with detected medicines and analysis
    """
    _configure_genai()
    
    if not _genai_configured:
        return {"success": False, "error": "Gemini not configured", "detected_medicines": []}
    
    # System prompt for prescription analysis
    system_prompt = """You are a pharmacy assistant specialized in reading prescriptions.
Analyze the prescription image and extract:
1. All medicines mentioned (with dosage if visible)
2. Any patient name or date
3. Doctor's name if visible

Return ONLY valid JSON in this exact format:
{
  "success": true,
  "detected_medicines": [{"name": "medicine name", "dosage": "dosage if visible", "confidence": 0.9}],
  "patient_name": "if visible",
  "doctor_name": "if visible",
  "date": "if visible",
  "raw_text": "any readable text from prescription"
}

If no medicines are clearly visible, return success: false with an explanation."""

    # Language instruction
    lang_name = LANGUAGE_MAP.get(language, "English")
    system_prompt += f"\n\nRespond in {lang_name} language."
    
    try:
        # Prepare image
        image_parts = {
            "mime_type": "image/jpeg", 
            "data": base64.b64encode(image_data).decode("utf-8")
        }
        
        prompt = "Analyze this prescription and extract all medicines, patient details, and doctor information."
        
        response = _pro_model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {"text": system_prompt},
                        {"inline_data": image_parts},
                        {"text": prompt}
                    ]
                }
            ]
        )
        
        if response and response.text:
            # Try to parse JSON response
            try:
                # First try direct parse
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Try to find JSON in response
                start_idx = response.text.find("{")
                end_idx = response.text.rfind("}")
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response.text[start_idx:end_idx+1]
                    try:
                        return json.loads(json_str)
                    except:
                        pass
            
            return {
                "success": True,
                "raw_response": response.text,
                "detected_medicines": []
            }
        
        return {"success": False, "error": "No response from Gemini", "detected_medicines": []}
        
    except Exception as e:
        print(f"[Gemini] Prescription analysis error: {e}")
        return {"success": False, "error": str(e), "detected_medicines": []}


def is_gemini_available() -> bool:
    """Check if Gemini API is available and configured."""
    _configure_genai()
    return _genai_configured


def get_gemini_info() -> Dict[str, Any]:
    """Get information about configured Gemini models."""
    _configure_genai()
    
    return {
        "provider": "gemini",
        "configured": _genai_configured,
        "flash_model": GEMINI_FLASH_MODEL,
        "pro_model": GEMINI_PRO_MODEL,
        "api_key_set": bool(GOOGLE_API_KEY)
    }


def stream_response(
    messages: List[Union[dict, HumanMessage]],
    model_type: str = "flash",
    temperature: float = 0.5,
    max_tokens: int = 512,
    language: Optional[str] = None
):
    """
    Stream response from Gemini (for real-time output).
    
    Args:
        messages: List of messages
        model_type: "flash" or "pro"
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        language: Language code
    
    Yields:
        Text chunks as they are generated
    """
    _configure_genai()
    
    if not _genai_configured:
        yield "Error: Gemini not configured"
        return
    
    try:
        # Select model
        if model_type == "pro":
            model = _pro_model
        else:
            model = _flash_model
        
        # Build messages for Gemini
        gemini_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            elif isinstance(msg, HumanMessage):
                role = "user"
                content = msg.content
            else:
                role = "user"
                content = str(msg)
            
            gemini_messages.append({"role": role, "parts": [content]})
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Generate streaming response
        response = model.generate_content(
            gemini_messages,
            generation_config=generation_config,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        print(f"[Gemini] Stream error: {e}")
        yield f"Error: {str(e)}"


# Convenience functions for model selection

def generate_with_routing(
    messages: List[Union[dict, HumanMessage]],
    task_type: str = "simple",
    temperature: float = 0.4,
    max_tokens: int = 512,
    system_prompt: Optional[str] = None,
    language: Optional[str] = None
) -> Optional[str]:
    """
    Generate response with automatic model selection.
    
    Args:
        messages: Conversation messages
        task_type: Type of task - "simple", "complex", "medical", "prescription"
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        system_prompt: Optional system prompt
        language: Language code
    
    Returns:
        Generated text response
    """
    model_type = _select_model(task_type)
    
    return generate_response(
        messages=messages,
        model_type=model_type,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        language=language
    )


def reset_gemini():
    """Reset Gemini configuration (useful for testing)."""
    global _genai_configured, _flash_model, _pro_model
    _genai_configured = False
    _flash_model = None
    _pro_model = None
    print("[Gemini] Configuration reset")
