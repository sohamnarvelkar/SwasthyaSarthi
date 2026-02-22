import streamlit as st
import numpy as np
import tempfile
import os
import io
import wave

# Try to import optional dependencies
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    st.warning("sounddevice not installed. Run: pip install sounddevice")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

# Language code mapping for Whisper
LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Bengali": "bn",
    "Malayalam": "ml",
    "Gujarati": "gu"
}

# Initialize Whisper model (will be loaded on first use)
@st.cache_resource
def load_whisper_model():
    """Load Whisper model for speech recognition."""
    if not FASTER_WHISPER_AVAILABLE:
        return None
    try:
        return WhisperModel("base", device="cpu", compute_type="int8")
    except Exception as e:
        st.error(f"Error loading Whisper model: {e}")
        return None

def record_audio(duration=5, sample_rate=16000):
    """
    Record audio from microphone using sounddevice.
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate
    
    Returns:
        numpy array: Audio data
    """
    if not SOUNDDEVICE_AVAILABLE:
        return None
    
    try:
        st.info(f"🔴 Recording for {duration} seconds...")
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return audio_data.flatten()
    except Exception as e:
        st.error(f"Error recording audio: {e}")
        return None

def save_audio_to_wav(audio_data, sample_rate=16000):
    """Save numpy audio data to a temporary WAV file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode='wb')
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Convert float32 to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wf.writeframes(audio_int16.tobytes())
    return temp_file.name

def speech_to_text_whisper(audio_data, language="English"):
    """
    Convert speech to text using Faster Whisper.
    This is the BEST quality STT available.
    """
    if not FASTER_WHISPER_AVAILABLE:
        st.error("Faster Whisper not installed. Run: pip install faster-whisper")
        return ""
    
    if audio_data is None:
        return ""
    
    try:
        model = load_whisper_model()
        if model is None:
            return ""
            
        lang_code = LANGUAGE_CODES.get(language, "en")
        
        # Save audio to temporary file
        temp_path = save_audio_to_wav(audio_data)
        
        # Transcribe using Whisper
        segments, info = model.transcribe(temp_path, language=lang_code)
        
        # Get the transcription
        transcription = " ".join([segment.text for segment in segments])
        
        # Cleanup
        os.unlink(temp_path)
        
        return transcription if transcription else ""
    except Exception as e:
        st.error(f"Whisper STT Error: {e}")
        return ""

def record_voice(language="English", duration=5):
    """
    Main voice recording function - captures audio and converts to text.
    Uses Whisper for speech recognition.
    
    Args:
        language: Selected language (English, Hindi, Marathi, etc.)
        duration: Recording duration in seconds
    
    Returns:
        str: Transcribed text from speech
    """
    if not SOUNDDEVICE_AVAILABLE:
        st.error("🎤 Audio recording library not installed. Please run: pip install sounddevice")
        st.info("💡 You can still type your message in the text box below.")
        return ""
    
    st.info(f"🎤 Recording will start for {duration} seconds. Speak clearly!")
    
    # Record audio
    audio_data = record_audio(duration=duration)
    
    if audio_data is None:
        st.error("Failed to record audio. Please check your microphone.")
        return ""
    
    st.success("✓ Recording complete! Processing speech...")
    
    # Convert speech to text using Whisper
    text = speech_to_text_whisper(audio_data, language)
    
    if text:
        st.success(f"✓ Recognized: {text}")
        return text
    else:
        st.warning("Could not understand audio. Please try again or type your message.")
        return ""

def test_microphone():
    """
    Test if microphone is available and working.
    """
    if not SOUNDDEVICE_AVAILABLE:
        st.error("sounddevice not installed. Run: pip install sounddevice")
        return False
    
    try:
        # Try to get device info
        devices = sd.query_devices()
        st.success(f"✓ Microphone found! Device: {devices['name']}")
        
        # Try a short recording
        st.info("Testing recording...")
        audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1)
        sd.wait()
        st.success("✓ Recording test successful!")
        return True
    except Exception as e:
        st.error(f"✗ Microphone test failed: {e}")
        return False

# Export the main function
__all__ = ['record_voice', 'test_microphone', 'LANGUAGE_CODES']
