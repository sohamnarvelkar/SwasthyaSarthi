"""
ElevenLabs AI Voice Service for SwasthyaSarthi.
Provides high-quality multilingual text-to-speech using ElevenLabs API.
"""

import os
import json
import time
import tempfile
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ElevenLabs API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Voice mapping based on language
# Using ElevenLabs multilingual voices for Hindi and Marathi
VOICE_MAP = {
    "English": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "name": "Rachel"
    },
    "Hindi": {
        "voice_id": "cgSgspJf0CmTYbNQCkgn",  # Multilingual voice
        "name": "Hindi_Multilingual"
    },
    "Marathi": {
        "voice_id": "cgSgspJfTlvDq8ikWAM",  # Using multilingual for Marathi
        "name": "Marathi_Multilingual"
    }
}

# Language code mapping for API
LANGUAGE_CODE_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr"
}

# Audio cache settings
CACHE_DIR = tempfile.gettempdir() + "/swasthya_sarthi_tts"
CACHE_MAX_SIZE_MB = 100
CACHE_MAX_FILES = 50


class ElevenLabsService:
    """
    ElevenLabs TTS Service with caching and LangSmith observability.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs service.
        
        Args:
            api_key: ElevenLabs API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.base_url = ELEVENLABS_BASE_URL
        self.cache_dir = Path(CACHE_DIR)
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache directory."""
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, text: str, language: str, voice_id: str) -> str:
        """Generate cache key for text."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{voice_id}_{language}_{text_hash}.mp3"
    
    def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Check if audio is cached and return it."""
        cache_file = self.cache_dir / cache_key
        if cache_file.exists():
            # Check file age (max 1 hour)
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < 3600:
                return cache_file.read_bytes()
            else:
                # Remove old cache file
                cache_file.unlink()
        return None
    
    def _save_to_cache(self, cache_key: str, audio_data: bytes):
        """Save audio to cache."""
        try:
            cache_file = self.cache_dir / cache_key
            cache_file.write_bytes(audio_data)
            self._cleanup_cache()
        except Exception:
            pass  # Cache failure is non-critical
    
    def _cleanup_cache(self):
        """Clean up old cache files if needed."""
        try:
            cache_files = sorted(
                self.cache_dir.glob("*.mp3"),
                key=lambda f: f.stat().st_mtime
            )
            
            # Remove oldest files if over limit
            if len(cache_files) > CACHE_MAX_FILES:
                for f in cache_files[:-CACHE_MAX_FILES]:
                    f.unlink()
        except Exception:
            pass
    
    def _log_to_langsmith(
        self,
        text: str,
        language: str,
        voice_id: str,
        success: bool,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """
        Log metadata to LangSmith for observability.
        In production, this would use langsmith.Client().
        For now, we log to console for visibility.
        """
        log_data = {
            "event": "elevenlabs_tts",
            "interaction_mode": "voice",
            "tts_provider": "elevenlabs",
            "language": language,
            "voice_id": voice_id,
            "text_length": len(text),
            "success": success,
            "duration_ms": duration_ms
        }
        
        if error:
            log_data["error"] = error
        
        # In production, use: langsmith.Client().run_created(...)
        print(f"[LangSmith] {json.dumps(log_data)}")
    
    def generate_voice(
        self,
        text: str,
        language: str = "English",
        voice_id: Optional[str] = None,
        auto_play: bool = True
    ) -> Optional[bytes]:
        """
        Generate voice audio using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            language: Language for voice selection
            voice_id: Optional custom voice ID
            auto_play: Not used in this service (kept for interface compatibility)
        
        Returns:
            Audio data as bytes or None if failed
        """
        if not text or not text.strip():
            return None
        
        start_time = time.time()
        
        # Validate API key
        if not self.api_key:
            error_msg = "ElevenLabs API key not configured"
            self._log_to_langsmith(text, language, "", False, error_msg)
            print(f"[ElevenLabs Error] {error_msg}")
            return None
        
        # Get voice configuration
        lang_voices = VOICE_MAP.get(language, VOICE_MAP["English"])
        selected_voice_id = voice_id or lang_voices["voice_id"]
        
        # Check cache first
        cache_key = self._get_cache_key(text, language, selected_voice_id)
        cached_audio = self._get_cached_audio(cache_key)
        if cached_audio:
            duration_ms = (time.time() - start_time) * 1000
            self._log_to_langsmith(text, language, selected_voice_id, True, duration_ms=duration_ms)
            return cached_audio
        
        # Prepare API request
        url = f"{self.base_url}/text-to-speech/{selected_voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.8
            }
        }
        
        try:
            # Make API request
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                audio_data = response.content
                
                # Save to cache
                self._save_to_cache(cache_key, audio_data)
                
                duration_ms = (time.time() - start_time) * 1000
                self._log_to_langsmith(text, language, selected_voice_id, True, duration_ms=duration_ms)
                
                return audio_data
            
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                self._log_to_langsmith(text, language, selected_voice_id, False, error_msg)
                print(f"[ElevenLabs Error] {error_msg}")
                return None
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self._log_to_langsmith(text, language, selected_voice_id, False, error_msg)
            print(f"[ElevenLabs Error] {error_msg}")
            return None
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._log_to_langsmith(text, language, selected_voice_id, False, error_msg)
            print(f"[ElevenLabs Error] {error_msg}")
            return None
    
    def generate_voice_with_fallback(
        self,
        text: str,
        language: str = "English",
        fallback_tts=None
    ) -> Optional[bytes]:
        """
        Generate voice with fallback to alternative TTS if ElevenLabs fails.
        
        Args:
            text: Text to convert to speech
            language: Language for voice selection
            fallback_tts: Fallback TTS function
        
        Returns:
            Audio data as bytes or None if failed
        """
        # Try ElevenLabs first
        audio_data = self.generate_voice(text, language)
        
        if audio_data:
            return audio_data
        
        # Fallback to alternative TTS
        if fallback_tts:
            print(f"[ElevenLabs] Falling back to alternative TTS for {language}")
            try:
                return fallback_tts(text, language)
            except Exception as e:
                print(f"[ElevenLabs Fallback Error] {e}")
        
        return None
    
    def get_available_voices(self) -> list[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs.
        
        Returns:
            List of voice dictionaries
        """
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("voices", [])
        except Exception as e:
            print(f"[ElevenLabs] Error fetching voices: {e}")
        
        return []


# Convenience function for easy import
_service_instance: Optional[ElevenLabsService] = None


def get_elevenlabs_service() -> ElevenLabsService:
    """Get or create ElevenLabs service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ElevenLabsService()
    return _service_instance


def generate_voice(text: str, language: str = "English") -> Optional[bytes]:
    """
    Generate voice audio (convenience function).
    
    Args:
        text: Text to convert to speech
        language: Language for voice selection
    
    Returns:
        Audio data as bytes or None if failed
    """
    service = get_elevenlabs_service()
    return service.generate_voice(text, language)


# Export
__all__ = [
    'ElevenLabsService',
    'get_elevenlabs_service',
    'generate_voice',
    'VOICE_MAP',
    'LANGUAGE_CODE_MAP'
]
