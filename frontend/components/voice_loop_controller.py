"""
Voice Loop Controller for SwasthyaSarthi Voice Agent.
Manages continuous voice conversation like human-to-human dialogue.
Integrates STT → Language Detection → LangGraph Agents → TTS → Auto-play.
"""

import threading
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import streamlit as st

# Import voice components
from frontend.components.speech_to_text import SpeechToText, listen_once
from frontend.components.text_to_speech import TextToSpeech, speak_text
from frontend.components.language_detector import detect_language, get_language_code, get_tts_language_code

# Import ElevenLabs service
try:
    from backend.services.elevenlabs_service import ElevenLabsService, get_elevenlabs_service, VOICE_MAP
    ELEVENTLABS_AVAILABLE = True
except ImportError:
    ELEVENTLABS_AVAILABLE = False
    print("[Warning] ElevenLabs service not available, using fallback TTS")

# Import LangGraph orchestration
from orchestration.graph import app_graph


class VoiceModeState(Enum):
    """States for voice conversation mode."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class VoiceInteraction:
    """Record of a voice interaction."""
    user_input: str
    detected_language: str
    agent_response: str
    agent_trace: list
    timestamp: float = field(default_factory=time.time)
    interaction_mode: str = "voice"


class VoiceLoopController:
    """
    Controller for continuous voice conversation.
    Manages the loop: Listen → STT → Agents → TTS → Speak → Repeat
    """
    
    def __init__(
        self,
        user_id: str = "default",
        user_email: str = "default",
        session_id: str = "default",
        voice_type: str = "female",
        use_continuous_listening: bool = True
    ):
        """
        Initialize voice loop controller.
        
        Args:
            user_id: User identifier
            user_email: User email
            session_id: Session identifier
            voice_type: "male" or "female"
            use_continuous_listening: Whether to use continuous VAD or single utterance
        """
        self.user_id = user_id
        self.user_email = user_email
        self.session_id = session_id
        self.voice_type = voice_type
        self.use_continuous_listening = use_continuous_listening
        
        # Components
        self.stt = SpeechToText()
        self.tts = TextToSpeech(voice_type=voice_type)
        
        # State
        self.state = VoiceModeState.IDLE
        self.is_active = False
        self.stop_event = threading.Event()
        self.current_language = "English"
        
        # Conversation history
        self.interactions: list[VoiceInteraction] = []
        
        # Callbacks
        self.on_state_change: Optional[Callable[[VoiceModeState], None]] = None
        self.on_interaction: Optional[Callable[[VoiceInteraction], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def _set_state(self, new_state: VoiceModeState):
        """Update state and trigger callback."""
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language from user input.
        Returns language name (English, Hindi, Marathi).
        """
        result = detect_language(text, use_llm_fallback=True)
        language = result.get("language", "English")
        self.current_language = language
        return language
    
    def _process_with_agents(self, user_input: str, language: str) -> Dict[str, Any]:
        """
        Process user input through LangGraph agents.
        
        Args:
            user_input: Transcribed user speech
            language: Detected language
        
        Returns:
            Agent response with final_response, agent_trace, etc.
        """
        try:
            # Prepare state for LangGraph
            lang_code = get_language_code(language)
            
            initial_state = {
                "user_input": user_input,
                "user_id": self.user_id,
                "user_email": self.user_email,
                "user_phone": None,
                "user_address": None,
                "user_language": lang_code,
                "intent_type": "GENERAL_CHAT",
                "current_intent": "GENERAL_CHAT",
                "detected_language": lang_code,
                "session_id": self.session_id,
                "identified_symptoms": [],
                "possible_conditions": [],
                "medical_advice": "",
                "recommended_medicines": [],
                "metadata": {
                    "agent_name": "voice_conversation",
                    "action": "process_voice_input",
                    "language": language,
                    "interaction_mode": "voice"  # For LangSmith observability
                },
                "agent_trace": [],
                "structured_order": {},
                "safety_result": {},
                "final_response": "",
                "is_proactive": False,
                "refill_alerts": [],
                "requires_confirmation": False,
                "confirmation_message": "",
                "user_confirmed": None,
                "pending_order_details": None,
                "is_order_request": True,
                "info_product": "",
                "info_response": ""
            }
            
            # Run through LangGraph
            result = app_graph.invoke(
                initial_state,
                config={"configurable": {"thread_id": f"{self.user_id}:{self.session_id}"}}
            )
            
            return {
                "response": result.get("final_response", ""),
                "agent_trace": result.get("agent_trace", []),
                "requires_confirmation": result.get("requires_confirmation", False),
                "pending_order": result.get("pending_order_details"),
                "intent": result.get("intent_type", "GENERAL_CHAT")
            }
            
        except Exception as e:
            error_msg = f"Agent processing error: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "agent_trace": [],
                "requires_confirmation": False,
                "pending_order": None,
                "intent": "ERROR"
            }
    
    def _speak_response(self, text: str, language: str) -> bool:
        """
        Convert response to speech and auto-play using ElevenLabs.
        
        Args:
            text: Response text to speak
            language: Language for speech
        
        Returns:
            True if successful
        """
        try:
            self._set_state(VoiceModeState.SPEAKING)
            
            audio_data = None
            
            # Try ElevenLabs first if available
            if ELEVENTLABS_AVAILABLE:
                try:
                    elevenlabs_service = get_elevenlabs_service()
                    audio_data = elevenlabs_service.generate_voice(text, language)
                    
                    if audio_data:
                        print(f"[Voice] Using ElevenLabs for {language}")
                    else:
                        print(f"[Voice] ElevenLabs failed, trying fallback TTS")
                        
                except Exception as e:
                    print(f"[Voice] ElevenLabs error: {e}")
            
            # Fallback to original TTS if ElevenLabs failed or unavailable
            if not audio_data:
                audio_data = self.tts.speak(text, language, auto_play=True)
                if audio_data:
                    print(f"[Voice] Using fallback TTS for {language}")
            
            if audio_data:
                # Estimate speech duration (rough: ~3 chars per second)
                duration = len(text) / 3
                time.sleep(duration)  # Wait for speech to complete
                
                self._set_state(VoiceModeState.WAITING)
                return True
            else:
                self._set_state(VoiceModeState.ERROR)
                return False
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"TTS error: {str(e)}")
            self._set_state(VoiceModeState.ERROR)
            return False
    
    def _handle_single_turn(self):
        """
        Handle a single conversation turn.
        Listen → Process → Speak
        """
        try:
            # Step 1: Listen
            self._set_state(VoiceModeState.LISTENING)
            
            # Listen for speech
            user_text = listen_once(duration=8.0, language=self.current_language)
            
            if not user_text or not user_text.strip():
                # No speech detected, continue listening
                return True
            
            # Step 2: Detect language
            detected_language = self._detect_language(user_text)
            
            # Step 3: Process with agents
            self._set_state(VoiceModeState.PROCESSING)
            
            agent_result = self._process_with_agents(user_text, detected_language)
            response_text = agent_result.get("response", "")
            
            # Step 4: Record interaction
            interaction = VoiceInteraction(
                user_input=user_text,
                detected_language=detected_language,
                agent_response=response_text,
                agent_trace=agent_result.get("agent_trace", [])
            )
            self.interactions.append(interaction)
            
            if self.on_interaction:
                self.on_interaction(interaction)
            
            # Step 5: Speak response
            if response_text:
                self._speak_response(response_text, detected_language)
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Turn error: {str(e)}")
            return False
    
    def start_conversation(self):
        """
        Start continuous voice conversation.
        Runs until stop_conversation() is called.
        """
        if self.is_active:
            return
        
        self.is_active = True
        self.stop_event.clear()
        self._set_state(VoiceModeState.LISTENING)
        
        # Welcome message
        welcome_text = "Hello! I'm SwasthyaSarthi, your pharmacy assistant. How can I help you today?"
        self._speak_response(welcome_text, "English")
        
        # Main conversation loop
        while self.is_active and not self.stop_event.is_set():
            try:
                success = self._handle_single_turn()
                
                if not success:
                    # Brief pause before retry
                    time.sleep(1)
                
                # Small delay between turns
                time.sleep(0.5)
                
            except Exception as e:
                if self.on_error:
                    self.on_error(f"Loop error: {str(e)}")
                time.sleep(1)
        
        self._set_state(VoiceModeState.IDLE)
    
    def stop_conversation(self):
        """Stop the voice conversation loop."""
        self.is_active = False
        self.stop_event.set()
        self._set_state(VoiceModeState.IDLE)
    
    def get_interactions(self) -> list[VoiceInteraction]:
        """Get conversation history."""
        return self.interactions
    
    def get_current_state(self) -> VoiceModeState:
        """Get current state."""
        return self.state
    
    def is_running(self) -> bool:
        """Check if conversation is active."""
        return self.is_active


class StreamlitVoiceController:
    """
    Streamlit-friendly wrapper for VoiceLoopController.
    Manages session state for UI integration.
    """
    
    def __init__(self, user_id: str, user_email: str):
        self.user_id = user_id
        self.user_email = user_email
        self.controller: Optional[VoiceLoopController] = None
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state."""
        if 'voice_active' not in st.session_state:
            st.session_state.voice_active = False
        if 'voice_state' not in st.session_state:
            st.session_state.voice_state = VoiceModeState.IDLE
        if 'voice_interactions' not in st.session_state:
            st.session_state.voice_interactions = []
        if 'voice_error' not in st.session_state:
            st.session_state.voice_error = None
        if 'voice_thread' not in st.session_state:
            st.session_state.voice_thread = None
    
    def _on_state_change(self, state: VoiceModeState):
        """Handle state changes."""
        st.session_state.voice_state = state
        # Use experimental rerun for UI updates
        try:
            st.rerun()
        except:
            pass
    
    def _on_interaction(self, interaction: VoiceInteraction):
        """Handle new interaction."""
        st.session_state.voice_interactions.append(interaction)
        try:
            st.rerun()
        except:
            pass
    
    def _on_error(self, error: str):
        """Handle errors."""
        st.session_state.voice_error = error
    
    def start_voice_mode(self, voice_type: str = "female"):
        """
        Start voice conversation mode.
        
        Args:
            voice_type: "male" or "female"
        """
        if st.session_state.voice_active:
            return
        
        # Create controller
        self.controller = VoiceLoopController(
            user_id=self.user_id,
            user_email=self.user_email,
            session_id=f"{self.user_id}:voice",
            voice_type=voice_type,
            use_continuous_listening=True
        )
        
        # Set callbacks
        self.controller.on_state_change = self._on_state_change
        self.controller.on_interaction = self._on_interaction
        self.controller.on_error = self._on_error
        
        # Start in thread
        st.session_state.voice_active = True
        st.session_state.voice_error = None
        
        import threading
        thread = threading.Thread(target=self.controller.start_conversation)
        thread.daemon = True
        thread.start()
        st.session_state.voice_thread = thread
    
    def stop_voice_mode(self):
        """Stop voice conversation mode."""
        if self.controller:
            self.controller.stop_conversation()
        
        st.session_state.voice_active = False
        st.session_state.voice_state = VoiceModeState.IDLE
    
    def is_voice_active(self) -> bool:
        """Check if voice mode is active."""
        return st.session_state.voice_active
    
    def get_voice_state(self) -> VoiceModeState:
        """Get current voice state."""
        return st.session_state.voice_state
    
    def get_interactions(self) -> list:
        """Get voice interactions."""
        return st.session_state.voice_interactions
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message."""
        return st.session_state.voice_error
    
    def clear_error(self):
        """Clear error message."""
        st.session_state.voice_error = None
    
    def clear_interactions(self):
        """Clear interaction history."""
        st.session_state.voice_interactions = []


# Convenience functions
def start_voice_conversation(
    user_id: str,
    user_email: str,
    voice_type: str = "female"
) -> StreamlitVoiceController:
    """
    Start a voice conversation session.
    
    Args:
        user_id: User identifier
        user_email: User email
        voice_type: "male" or "female"
    
    Returns:
        StreamlitVoiceController instance
    """
    controller = StreamlitVoiceController(user_id, user_email)
    controller.start_voice_mode(voice_type)
    return controller


def stop_voice_conversation(controller: StreamlitVoiceController):
    """Stop a voice conversation session."""
    controller.stop_voice_mode()


# Export
__all__ = [
    'VoiceLoopController',
    'StreamlitVoiceController',
    'VoiceInteraction',
    'VoiceModeState',
    'start_voice_conversation',
    'stop_voice_conversation'
]
