"""
Speech-to-Text Module for SwasthyaSarthi Voice Agent.
Supports continuous listening mode with VAD (Voice Activity Detection).
Uses faster-whisper for local STT with multilingual support.
"""

import numpy as np
import tempfile
import os
import io
import wave
import time
import threading
from typing import Optional, Callable, Generator
from collections import deque
import streamlit as st

# Try to import optional dependencies
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'float32'
CHUNK_DURATION = 0.5  # Process audio in 0.5 second chunks
SILENCE_THRESHOLD = 0.01  # Energy threshold for silence detection
MIN_SPEECH_DURATION = 0.5  # Minimum speech to process
MAX_SILENCE_DURATION = 2.0  # Max silence before considering speech ended
PRE_SPEECH_BUFFER = 0.5  # Keep 0.5s before speech starts

# Language code mapping for Whisper
WHISPER_LANG_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Bengali": "bn",
    "Malayalam": "ml",
    "Gujarati": "gu"
}


class SpeechToText:
    """
    Continuous Speech-to-Text with Voice Activity Detection.
    Supports real-time listening and transcription.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize STT with Whisper model.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
        """
        self.model = None
        self.model_size = model_size
        self.device = device
        self.is_listening = False
        self.audio_buffer = deque(maxlen=int(PRE_SPEECH_BUFFER / CHUNK_DURATION))
        self.speech_buffer = []
        self.silence_duration = 0
        self.is_speaking = False
        
    def load_model(self) -> bool:
        """Load Whisper model if not already loaded."""
        if not FASTER_WHISPER_AVAILABLE:
            st.error("faster-whisper not installed. Run: pip install faster-whisper")
            return False
            
        if self.model is None:
            try:
                st.info("🔄 Loading Whisper model...")
                self.model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type="int8"
                )
                st.success("✅ Whisper model loaded!")
                return True
            except Exception as e:
                st.error(f"Error loading Whisper model: {e}")
                return False
        return True
    
    def calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculate audio energy for VAD."""
        return np.sqrt(np.mean(audio_chunk ** 2))
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Detect if audio chunk contains speech."""
        energy = self.calculate_energy(audio_chunk)
        return energy > SILENCE_THRESHOLD
    
    def save_audio_to_wav(self, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
        """Save numpy audio data to temporary WAV file."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode='wb')
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        return temp_file.name
    
    def transcribe(self, audio_data: np.ndarray, language: str = "English") -> str:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_data: Numpy array of audio samples
            language: Language for transcription
        
        Returns:
            Transcribed text
        """
        if self.model is None:
            if not self.load_model():
                return ""
        
        if audio_data is None or len(audio_data) == 0:
            return ""
        
        try:
            lang_code = WHISPER_LANG_CODES.get(language, "en")
            
            # Save audio to temporary file
            temp_path = self.save_audio_to_wav(audio_data)
            
            # Transcribe using Whisper
            segments, info = self.model.transcribe(
                temp_path, 
                language=lang_code,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Get the transcription
            transcription = " ".join([segment.text for segment in segments])
            
            # Cleanup
            os.unlink(temp_path)
            
            return transcription.strip()
            
        except Exception as e:
            st.error(f"Transcription error: {e}")
            return ""
    
    def listen_once(self, duration: float = 5.0, language: str = "English") -> str:
        """
        Listen for a single utterance (blocking).
        
        Args:
            duration: Maximum recording duration
            language: Expected language
        
        Returns:
            Transcribed text
        """
        if not SOUNDDEVICE_AVAILABLE:
            st.error("sounddevice not installed. Run: pip install sounddevice")
            return ""
        
        try:
            # Record audio
            st.info(f"🎤 Listening for {duration} seconds...")
            audio_data = sd.rec(
                int(duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE
            )
            sd.wait()
            
            # Check if we got any audio
            if len(audio_data) == 0:
                return ""
            
            # Transcribe
            st.info("🔄 Processing speech...")
            text = self.transcribe(audio_data.flatten(), language)
            
            return text
            
        except Exception as e:
            st.error(f"Recording error: {e}")
            return ""
    
    def listen_continuous(
        self, 
        callback: Callable[[str], None],
        language: str = "English",
        stop_event: Optional[threading.Event] = None
    ) -> None:
        """
        Continuous listening with VAD.
        Calls callback when speech is detected and transcribed.
        
        Args:
            callback: Function to call with transcribed text
            language: Expected language
            stop_event: Threading event to stop listening
        """
        if not SOUNDDEVICE_AVAILABLE:
            st.error("sounddevice not installed. Run: pip install sounddevice")
            return
        
        if not self.load_model():
            return
        
        self.is_listening = True
        self.audio_buffer.clear()
        self.speech_buffer = []
        self.silence_duration = 0
        self.is_speaking = False
        
        st.info("🎤 Continuous listening started. Speak now...")
        
        try:
            # Create input stream
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=int(SAMPLE_RATE * CHUNK_DURATION)
            ) as stream:
                
                while self.is_listening:
                    # Check stop event
                    if stop_event and stop_event.is_set():
                        break
                    
                    # Read audio chunk
                    audio_chunk, overflowed = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
                    audio_chunk = audio_chunk.flatten()
                    
                    # VAD processing
                    speech_detected = self.is_speech(audio_chunk)
                    
                    if speech_detected:
                        if not self.is_speaking:
                            # Speech started
                            self.is_speaking = True
                            self.silence_duration = 0
                            # Include pre-speech buffer
                            self.speech_buffer = list(self.audio_buffer) + [audio_chunk]
                        else:
                            # Continue speech
                            self.speech_buffer.append(audio_chunk)
                            self.silence_duration = 0
                    else:
                        if self.is_speaking:
                            # Potential end of speech
                            self.silence_duration += CHUNK_DURATION
                            self.speech_buffer.append(audio_chunk)
                            
                            if self.silence_duration >= MAX_SILENCE_DURATION:
                                # Speech ended
                                self.is_speaking = False
                                
                                # Process speech
                                if len(self.speech_buffer) > 0:
                                    audio_data = np.concatenate(self.speech_buffer)
                                    
                                    # Check minimum duration
                                    duration = len(audio_data) / SAMPLE_RATE
                                    if duration >= MIN_SPEECH_DURATION:
                                        # Transcribe
                                        text = self.transcribe(audio_data, language)
                                        if text:
                                            callback(text)
                                
                                # Reset buffers
                                self.speech_buffer = []
                                self.silence_duration = 0
                    
                    # Always add to pre-speech buffer
                    self.audio_buffer.append(audio_chunk)
                    
        except Exception as e:
            st.error(f"Continuous listening error: {e}")
        finally:
            self.is_listening = False
            st.info("🛑 Listening stopped.")
    
    def stop_listening(self):
        """Stop continuous listening."""
        self.is_listening = False


class StreamlitSTT:
    """
    Streamlit-friendly STT wrapper with session state management.
    """
    
    def __init__(self):
        self.stt = SpeechToText()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'stt_listening' not in st.session_state:
            st.session_state.stt_listening = False
        if 'stt_transcript' not in st.session_state:
            st.session_state.stt_transcript = ""
        if 'stt_stop_event' not in st.session_state:
            st.session_state.stt_stop_event = threading.Event()
    
    def start_listening(self, language: str = "English"):
        """Start continuous listening in a separate thread."""
        if st.session_state.stt_listening:
            return
        
        st.session_state.stt_listening = True
        st.session_state.stt_stop_event.clear()
        st.session_state.stt_transcript = ""
        
        def on_transcript(text: str):
            st.session_state.stt_transcript = text
            # Use Streamlit's experimental rerun
            st.rerun()
        
        # Start listening in thread
        import threading
        thread = threading.Thread(
            target=self.stt.listen_continuous,
            args=(on_transcript, language, st.session_state.stt_stop_event)
        )
        thread.daemon = True
        thread.start()
    
    def stop_listening(self) -> Optional[str]:
        """Stop listening and return final transcript."""
        st.session_state.stt_stop_event.set()
        st.session_state.stt_listening = False
        self.stt.stop_listening()
        
        transcript = st.session_state.stt_transcript
        st.session_state.stt_transcript = ""
        return transcript if transcript else None
    
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return st.session_state.stt_listening
    
    def get_transcript(self) -> str:
        """Get current transcript."""
        return st.session_state.stt_transcript


# Convenience functions for direct use
def listen_once(duration: float = 5.0, language: str = "English") -> str:
    """
    Simple function to listen once and return text.
    
    Args:
        duration: Recording duration in seconds
        language: Language for transcription
    
    Returns:
        Transcribed text
    """
    stt = SpeechToText()
    return stt.listen_once(duration, language)


def create_streamlit_stt() -> StreamlitSTT:
    """
    Create a Streamlit-friendly STT instance.
    
    Returns:
        StreamlitSTT instance
    """
    return StreamlitSTT()


# Export
__all__ = [
    'SpeechToText',
    'StreamlitSTT',
    'listen_once',
    'create_streamlit_stt',
    'WHISPER_LANG_CODES'
]
