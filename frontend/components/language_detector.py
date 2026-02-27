"""
Language Detection Module for SwasthyaSarthi Voice Agent.
Supports English, Hindi, and Marathi with lightweight detection.
Uses Devanagari script detection + LLM fallback for accuracy.
"""

import re
import json
from typing import Dict, Optional
import streamlit as st

# Devanagari Unicode range (for Hindi and Marathi)
DEVANAGARI_RANGE = r'[\u0900-\u097F]'

# Language-specific patterns
LANGUAGE_PATTERNS = {
    "Hindi": {
        "script": DEVANAGARI_RANGE,
        "common_words": [
            "है", "हैं", "मैं", "मुझे", "आप", "क्या", "कैसे", "कहाँ", "कब", "क्यों",
            "बुखार", "दर्द", "सिर", "पेट", "दवा", "दवाई", "औषधि", "चिकित्सक", "डॉक्टर"
        ],
        "code": "hi"
    },
    "Marathi": {
        "script": DEVANAGARI_RANGE,
        "common_words": [
            "आहे", "मी", "मला", "तुम्ही", "काय", "कसे", "कुठे", "केव्हा", "का",
            "ताप", "दुखणे", "डोक", "पोट", "औषध", "औषधी", "वैद्य", "डॉक्टर", "आजार"
        ],
        "code": "mr"
    },
    "English": {
        "script": r'[a-zA-Z]',
        "common_words": [
            "fever", "pain", "head", "stomach", "medicine", "doctor", "prescription",
            "order", "buy", "need", "have", "feel", "sick", "help", "what", "how"
        ],
        "code": "en"
    }
}


def detect_script(text: str) -> Optional[str]:
    """
    Detect script type from text.
    Returns 'devanagari' if Devanagari characters found, 'latin' for English.
    """
    if re.search(DEVANAGARI_RANGE, text):
        return "devanagari"
    elif re.search(r'[a-zA-Z]', text):
        return "latin"
    return None


def detect_by_keywords(text: str) -> Optional[str]:
    """
    Detect language by matching common keywords.
    Returns language name if confident, None otherwise.
    """
    text_lower = text.lower()
    
    scores = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for word in patterns["common_words"]:
            if word.lower() in text_lower:
                score += 1
        scores[lang] = score
    
    # Return language with highest score if above threshold
    if scores:
        max_lang = max(scores, key=scores.get)
        if scores[max_lang] > 0:
            return max_lang
    
    return None


def detect_language_llm(text: str, llm_provider=None) -> Dict[str, str]:
    """
    Use LLM for language classification as fallback.
    Returns JSON with detected language.
    """
    try:
        # Simple prompt for language classification
        classification_prompt = f"""Classify the language of the following text into one of: English, Hindi, Marathi.

Text: "{text}"

Return ONLY a JSON object in this exact format:
{{"language": "English"}} or {{"language": "Hindi"}} or {{"language": "Marathi"}}"""

        # Try to use Ollama if available
        if llm_provider is None:
            try:
                from agents.llm_provider import get_llm
                llm = get_llm()
                response = llm.invoke(classification_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                # Fallback: assume English if LLM fails
                return {"language": "English", "confidence": "low", "method": "fallback"}
        else:
            response_text = llm_provider.invoke(classification_prompt)
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "language": result.get("language", "English"),
                "confidence": "high",
                "method": "llm"
            }
        
    except Exception as e:
        pass
    
    return {"language": "English", "confidence": "low", "method": "fallback"}


def detect_language(text: str, use_llm_fallback: bool = True, llm_provider=None) -> Dict[str, str]:
    """
    Main language detection function.
    
    Priority order:
    1. Detect Devanagari script → Hindi/Marathi keyword matching
    2. Detect Latin script → English
    3. LLM classification fallback
    
    Args:
        text: Input text to analyze
        use_llm_fallback: Whether to use LLM if script detection is ambiguous
        llm_provider: Optional LLM provider for fallback
    
    Returns:
        Dict with language, confidence, and method used
    """
    if not text or not text.strip():
        return {"language": "English", "confidence": "high", "method": "default"}
    
    text = text.strip()
    
    # Step 1: Script detection
    script = detect_script(text)
    
    if script == "devanagari":
        # Step 2: Differentiate Hindi vs Marathi by keywords
        keyword_lang = detect_by_keywords(text)
        if keyword_lang:
            return {
                "language": keyword_lang,
                "confidence": "high",
                "method": "keywords"
            }
        
        # Ambiguous Devanagari - use LLM fallback if enabled
        if use_llm_fallback:
            return detect_language_llm(text, llm_provider)
        
        # Default to Hindi if Devanagari but can't determine
        return {"language": "Hindi", "confidence": "medium", "method": "script"}
    
    elif script == "latin":
        # Check if it might be English
        keyword_lang = detect_by_keywords(text)
        if keyword_lang == "English":
            return {
                "language": "English",
                "confidence": "high",
                "method": "keywords"
            }
        
        # Use LLM for Latin script that doesn't match English keywords
        if use_llm_fallback:
            return detect_language_llm(text, llm_provider)
        
        return {"language": "English", "confidence": "medium", "method": "script"}
    
    # No recognizable script - use LLM fallback
    if use_llm_fallback:
        return detect_language_llm(text, llm_provider)
    
    return {"language": "English", "confidence": "low", "method": "default"}


def get_language_code(language_name: str) -> str:
    """
    Get ISO language code from language name.
    """
    code_map = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr"
    }
    return code_map.get(language_name, "en")


def get_tts_language_code(language_name: str) -> str:
    """
    Get TTS-specific language code.
    """
    tts_map = {
        "English": "en-US",
        "Hindi": "hi-IN",
        "Marathi": "mr-IN"
    }
    return tts_map.get(language_name, "en-US")


# Export functions
__all__ = [
    'detect_language',
    'detect_script',
    'detect_by_keywords',
    'get_language_code',
    'get_tts_language_code',
    'LANGUAGE_PATTERNS'
]
