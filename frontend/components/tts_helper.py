"""
High-Quality Text-to-Speech Helper using Microsoft Edge TTS.
Edge TTS provides natural-sounding voices for multiple languages.
"""

import streamlit as st
import asyncio
import edge_tts
import tempfile
import os
import io

# Voice mapping for different languages
VOICE_MAP = {
    "English": {
        "male": "en-US-AriaNeural",
        "female": "en-US-JennyNeural"
    },
    "Hindi": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural"
    },
    "Marathi": {
        "male": "mr-IN-ManoharNeural",
        "female": "mr-IN-AarohiNeural"
    },
    "Bengali": {
        "male": "bn-IN-BashkarNeural",
        "female": "bn-IN-TanishaaNeural"
    },
    "Malayalam": {
        "male": "ml-IN-MidhunNeural",
        "female": "ml-IN-SobhanaNeural"
    },
    "Gujarati": {
        "male": "gu-IN-DhwaniNeural",
        "female": "gu-IN-FemalaNeural"
    }
}

# Language code mapping for edge-tts
LANGUAGE_CODE_MAP = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Marathi": "mr-IN",
    "Bengali": "bn-IN",
    "Malayalam": "ml-IN",
    "Gujarati": "gu-IN"
}

# gTTS language codes
GTTS_LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Bengali": "bn",
    "Malayalam": "ml",
    "Gujarati": "gu"
}

async def generate_speech_async(text, language="English", voice_type="female"):
    """
    Generate speech using Edge TTS asynchronously.
    
    Args:
        text: Text to convert to speech
        language: Language (English, Hindi, Marathi, etc.)
        voice_type: "male" or "female"
    
    Returns:
        bytes: Audio data in MP3 format
    """
    try:
        # Get the appropriate voice
        voice = VOICE_MAP.get(language, {}).get(voice_type, "en-US-JennyNeural")
        
        # Create the TTS communicate object
        communicate = edge_tts.Communicate(text, voice)
        
        # Collect audio data
        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])
        
        return audio_data.getvalue()
    except Exception as e:
        st.error(f"Edge TTS Error: {e}")
        return None

def generate_speech(text, language="English", voice_type="female"):
    """
    Generate speech using Edge TTS (synchronous wrapper).
    
    Args:
        text: Text to convert to speech
        language: Language (English, Hindi, Marathi, etc.)
        voice_type: "male" or "female"
    
    Returns:
        bytes: Audio data in MP3 format
    """
    return asyncio.run(generate_speech_async(text, language, voice_type))

def get_available_voices():
    """
    Get list of available Edge TTS voices for display.
    """
    return VOICE_MAP

def text_to_speech(text, language="English", voice_type="female", use_edge_tts=True):
    """
    Convert text to speech with multiple TTS engine options.
    
    Args:
        text: Text to convert to speech
        language: Language selection
        voice_type: Voice gender preference
        use_edge_tts: If True, try Edge TTS first, fallback to gTTS
    
    Returns:
        bytes: Audio data
    """
    # Try Edge TTS first (better quality)
    if use_edge_tts:
        try:
            audio_data = generate_speech(text, language, voice_type)
            if audio_data and len(audio_data) > 0:
                return audio_data
        except Exception as e:
            st.warning(f"Edge TTS unavailable ({e}), using Google TTS instead...")
    
    # Fallback to gTTS (works everywhere)
    try:
        from gtts import gTTS
        lang_code = GTTS_LANG_MAP.get(language, "en")
        
        tts = gTTS(text=text, lang=lang_code)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        return mp3_fp.getvalue()
    except Exception as e:
        st.error(f"gTTS also failed: {e}")
        return None

# Export functions
__all__ = [
    'text_to_speech', 
    'generate_speech', 
    'get_available_voices',
    'VOICE_MAP',
    'LANGUAGE_CODE_MAP'
]
