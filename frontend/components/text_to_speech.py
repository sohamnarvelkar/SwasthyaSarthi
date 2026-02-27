"""
Text-to-Speech Module for SwasthyaSarthi Voice Agent.
Supports auto-play with Edge TTS and gTTS fallback.
Multilingual support for English, Hindi, and Marathi.
"""

import asyncio
import edge_tts
import tempfile
import os
import io
import base64
from typing import Optional, Dict, Callable
import streamlit as st
import time

# Try to import gTTS as fallback
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Voice mapping for different languages (Edge TTS)
EDGE_VOICES = {
    "English": {
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural",
        "default": "en-US-JennyNeural"
    },
    "Hindi": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
        "default": "hi-IN-SwaraNeural"
    },
    "Marathi": {
        "male": "mr-IN-ManoharNeural",
        "female": "mr-IN-AarohiNeural",
        "default": "mr-IN-AarohiNeural"
    }
}

# gTTS language codes
GTTS_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr"
}

# TTS language codes for edge-tts
TTS_CODES = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Marathi": "mr-IN"
}


class TextToSpeech:
    """
    Text-to-Speech with auto-play support.
    Uses Edge TTS primarily, gTTS as fallback.
    """
    
    def __init__(self, voice_type: str = "female", use_edge_tts: bool = True):
        """
        Initialize TTS.
        
        Args:
            voice_type: "male" or "female"
            use_edge_tts: Whether to use Edge TTS (better quality)
        """
        self.voice_type = voice_type
        self.use_edge_tts = use_edge_tts
        self.is_speaking = False
    
    async def generate_edge_tts_async(
        self, 
        text: str, 
        language: str = "English"
    ) -> Optional[bytes]:
        """
        Generate speech using Edge TTS asynchronously.
        
        Args:
            text: Text to convert to speech
            language: Language for speech
        
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            # Get the appropriate voice
            voice_config = EDGE_VOICES.get(language, EDGE_VOICES["English"])
            voice = voice_config.get(self.voice_type, voice_config["default"])
            
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
    
    def generate_edge_tts(self, text: str, language: str = "English") -> Optional[bytes]:
        """
        Synchronous wrapper for Edge TTS generation.
        """
        return asyncio.run(self.generate_edge_tts_async(text, language))
    
    def generate_gtts(self, text: str, language: str = "English") -> Optional[bytes]:
        """
        Generate speech using gTTS (fallback).
        
        Args:
            text: Text to convert to speech
            language: Language for speech
        
        Returns:
            Audio data as bytes or None if failed
        """
        if not GTTS_AVAILABLE:
            st.error("gTTS not installed. Run: pip install gtts")
            return None
        
        try:
            lang_code = GTTS_CODES.get(language, "en")
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            return mp3_fp.getvalue()
            
        except Exception as e:
            st.error(f"gTTS Error: {e}")
            return None
    
    def speak(
        self, 
        text: str, 
        language: str = "English",
        auto_play: bool = True
    ) -> Optional[bytes]:
        """
        Convert text to speech and return audio data.
        
        Args:
            text: Text to convert to speech
            language: Language for speech
            auto_play: Whether to auto-play (for Streamlit)
        
        Returns:
            Audio data as bytes or None if failed
        """
        if not text or not text.strip():
            return None
        
        self.is_speaking = True
        
        try:
            # Try Edge TTS first
            if self.use_edge_tts:
                audio_data = self.generate_edge_tts(text, language)
                if audio_data and len(audio_data) > 0:
                    self.is_speaking = False
                    return audio_data
                st.warning("Edge TTS failed, trying gTTS...")
            
            # Fallback to gTTS
            audio_data = self.generate_gtts(text, language)
            self.is_speaking = False
            return audio_data
            
        except Exception as e:
            st.error(f"TTS Error: {e}")
            self.is_speaking = False
            return None
    
    def speak_with_callback(
        self,
        text: str,
        language: str = "English",
        on_complete: Optional[Callable] = None
    ) -> Optional[bytes]:
        """
        Speak with completion callback.
        
        Args:
            text: Text to convert to speech
            language: Language for speech
            on_complete: Callback function when speech completes
        
        Returns:
            Audio data as bytes
        """
        audio_data = self.speak(text, language, auto_play=False)
        
        if audio_data and on_complete:
            # Estimate duration (rough approximation: 3 chars per second)
            duration = len(text) / 3
            time.sleep(duration)
            on_complete()
        
        return audio_data
    
    def is_currently_speaking(self) -> bool:
        """Check if TTS is currently generating/speaking."""
        return self.is_speaking


class StreamlitTTS:
    """
    Streamlit-friendly TTS wrapper with auto-play support.
    """
    
    def __init__(self, voice_type: str = "female"):
        self.tts = TextToSpeech(voice_type=voice_type)
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'tts_queue' not in st.session_state:
            st.session_state.tts_queue = []
        if 'tts_current' not in st.session_state:
            st.session_state.tts_current = None
        if 'tts_auto_play' not in st.session_state:
            st.session_state.tts_auto_play = True
    
    def speak(
        self, 
        text: str, 
        language: str = "English",
        key: Optional[str] = None
    ) -> bool:
        """
        Speak text and auto-play in Streamlit.
        
        Args:
            text: Text to speak
            language: Language for speech
            key: Unique key for the audio element
        
        Returns:
            True if successful, False otherwise
        """
        # Generate audio
        audio_data = self.tts.speak(text, language, auto_play=True)
        
        if audio_data is None:
            return False
        
        # Create unique key if not provided
        if key is None:
            key = f"tts_{int(time.time() * 1000)}"
        
        # Store in session state for auto-play
        st.session_state.tts_current = {
            "audio": audio_data,
            "key": key,
            "text": text
        }
        
        # Auto-play using Streamlit audio
        try:
            # Use HTML5 audio with autoplay
            audio_b64 = base64.b64encode(audio_data).decode()
            audio_html = f"""
                <audio autoplay="true" id="{key}">
                    <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                </audio>
                <script>
                    document.getElementById("{key}").play();
                </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            
            # Also show standard audio player as fallback
            st.audio(audio_data, format="audio/mp3", start_time=0)
            
            return True
            
        except Exception as e:
            st.error(f"Auto-play error: {e}")
            # Fallback to standard audio
            st.audio(audio_data, format="audio/mp3")
            return True
    
    def queue_speech(self, text: str, language: str = "English"):
        """Queue speech for sequential playback."""
        st.session_state.tts_queue.append({
            "text": text,
            "language": language
        })
    
    def process_queue(self):
        """Process queued speech items."""
        if st.session_state.tts_queue:
            item = st.session_state.tts_queue.pop(0)
            self.speak(item["text"], item["language"])
    
    def clear_queue(self):
        """Clear speech queue."""
        st.session_state.tts_queue = []


# Convenience functions
def speak_text(
    text: str, 
    language: str = "English",
    voice_type: str = "female",
    auto_play: bool = True
) -> Optional[bytes]:
    """
    Simple function to convert text to speech.
    
    Args:
        text: Text to convert
        language: Language for speech
        voice_type: "male" or "female"
        auto_play: Whether to auto-play
    
    Returns:
        Audio data as bytes
    """
    tts = TextToSpeech(voice_type=voice_type)
    return tts.speak(text, language, auto_play)


def create_streamlit_tts(voice_type: str = "female") -> StreamlitTTS:
    """
    Create a Streamlit-friendly TTS instance.
    
    Args:
        voice_type: "male" or "female"
    
    Returns:
        StreamlitTTS instance
    """
    return StreamlitTTS(voice_type=voice_type)


# Export
__all__ = [
    'TextToSpeech',
    'StreamlitTTS',
    'speak_text',
    'create_streamlit_tts',
    'EDGE_VOICES',
    'GTTS_CODES',
    'TTS_CODES'
]
