"""
Voice Agent UI Component for SwasthyaSarthi.
Provides Start/Stop voice mode controls and displays voice conversation status.
Integrates with the voice loop controller for continuous conversation.
"""

import streamlit as st
from typing import Optional
import time

# Import voice components
from frontend.components.voice_loop_controller import (
    StreamlitVoiceController, 
    VoiceModeState,
    start_voice_conversation,
    stop_voice_conversation
)
from frontend.components.language_detector import detect_language


def render_voice_status(status: VoiceModeState):
    """
    Render voice mode status indicator.
    
    Args:
        status: Current voice mode state
    """
    status_config = {
        VoiceModeState.IDLE: ("⚪", "gray", "Voice mode inactive"),
        VoiceModeState.LISTENING: ("🎤", "red", "Listening... Speak now"),
        VoiceModeState.PROCESSING: ("🤔", "blue", "Processing your request..."),
        VoiceModeState.SPEAKING: ("🔊", "green", "Speaking response..."),
        VoiceModeState.WAITING: ("⏳", "orange", "Waiting for your response..."),
        VoiceModeState.ERROR: ("❌", "red", "Error occurred")
    }
    
    icon, color, message = status_config.get(status, ("⚪", "gray", "Unknown"))
    
    st.markdown(f"""
        <div style="
            padding: 10px;
            border-radius: 10px;
            background-color: {color};
            color: white;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
        ">
            {icon} {message}
        </div>
    """, unsafe_allow_html=True)


def render_voice_controls(
    user_id: str,
    user_email: str,
    voice_type: str = "female"
) -> bool:
    """
    Render voice agent Start/Stop controls.
    
    Args:
        user_id: User identifier
        user_email: User email
        voice_type: Voice type preference
    
    Returns:
        True if voice mode is active
    """
    # Initialize controller in session state
    if 'voice_controller' not in st.session_state:
        st.session_state.voice_controller = None
    
    # Check if we need to create/recreate controller
    if st.session_state.voice_controller is None:
        st.session_state.voice_controller = StreamlitVoiceController(user_id, user_email)
    
    controller = st.session_state.voice_controller
    
    # Voice mode section
    st.markdown("---")
    st.markdown("### 🎙️ Voice Agent Mode")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        # Start Voice Agent button
        if not controller.is_voice_active():
            if st.button("🎙️ Start Voice Agent", type="primary", key="start_voice_btn"):
                with st.spinner("Initializing voice mode..."):
                    controller.start_voice_mode(voice_type)
                    st.success("Voice agent activated!")
                    time.sleep(0.5)
                    st.rerun()
    
    with col2:
        # Stop Voice Agent button
        if controller.is_voice_active():
            if st.button("⏹️ Stop Voice Agent", type="secondary", key="stop_voice_btn"):
                controller.stop_voice_mode()
                st.info("Voice agent stopped.")
                time.sleep(0.5)
                st.rerun()
    
    with col3:
        # Voice type selector (only when not active)
        if not controller.is_voice_active():
            voice_choice = st.selectbox(
                "Voice",
                options=["female", "male"],
                index=0 if voice_type == "female" else 1,
                key="voice_type_select"
            )
            if voice_choice != voice_type:
                voice_type = voice_choice
    
    # Show status if active
    if controller.is_voice_active():
        current_state = controller.get_voice_state()
        render_voice_status(current_state)
        
        # Show listening indicator
        if current_state == VoiceModeState.LISTENING:
            st.info("🎤 I'm listening... Speak clearly about your health concern or medicine needs.")
        
        # Show error if any
        error = controller.get_last_error()
        if error:
            st.error(f"⚠️ {error}")
            controller.clear_error()
    
    return controller.is_voice_active()


def render_voice_conversation_history():
    """
    Render voice conversation history.
    """
    if 'voice_controller' not in st.session_state or st.session_state.voice_controller is None:
        return
    
    controller = st.session_state.voice_controller
    interactions = controller.get_interactions()
    
    if interactions:
        st.markdown("### 📝 Voice Conversation History")
        
        for i, interaction in enumerate(interactions, 1):
            with st.expander(f"Turn {i}: {interaction.user_input[:50]}...", expanded=(i == len(interactions))):
                st.markdown(f"**🎤 You said ({interaction.detected_language}):**")
                st.info(interaction.user_input)
                
                st.markdown(f"**🔊 Agent responded:**")
                st.success(interaction.agent_response)
                
                if interaction.agent_trace:
                    with st.expander("View agent trace"):
                        for trace in interaction.agent_trace:
                            st.json(trace)
        
        # Clear history button
        if st.button("🗑️ Clear Voice History", key="clear_voice_history"):
            controller.clear_interactions()
            st.rerun()


def render_voice_mode_ui(
    user_id: str,
    user_email: str,
    voice_type: str = "female"
) -> bool:
    """
    Main function to render complete voice mode UI.
    
    Args:
        user_id: User identifier
        user_email: User email
        voice_type: Voice type preference
    
    Returns:
        True if voice mode is active
    """
    # Voice controls
    is_active = render_voice_controls(user_id, user_email, voice_type)
    
    # Conversation history
    if is_active:
        render_voice_conversation_history()
    
    # Instructions
    if not is_active:
        st.markdown("""
            <div style="
                background-color: #f0f2f6;
                padding: 15px;
                border-radius: 10px;
                margin-top: 10px;
            ">
                <h4>📖 How to use Voice Agent:</h4>
                <ol>
                    <li>Click <b>🎙️ Start Voice Agent</b> to activate</li>
                    <li>Speak naturally about your symptoms or medicine needs</li>
                    <li>The agent will listen, process, and respond automatically</li>
                    <li>Continue the conversation naturally - no button clicks needed</li>
                    <li>Click <b>⏹️ Stop Voice Agent</b> when done</li>
                </ol>
                <p><b>Supported languages:</b> English, Hindi, Marathi (auto-detected)</p>
            </div>
        """, unsafe_allow_html=True)
    
    return is_active


def get_voice_input_text() -> Optional[str]:
    """
    Get the latest voice input text if available.
    Used for integration with chat interface.
    
    Returns:
        Latest voice input text or None
    """
    if 'voice_controller' not in st.session_state or st.session_state.voice_controller is None:
        return None
    
    controller = st.session_state.voice_controller
    interactions = controller.get_interactions()
    
    if interactions:
        return interactions[-1].user_input
    
    return None


def is_voice_mode_active() -> bool:
    """
    Check if voice mode is currently active.
    
    Returns:
        True if voice mode is active
    """
    if 'voice_controller' not in st.session_state or st.session_state.voice_controller is None:
        return False
    
    return st.session_state.voice_controller.is_voice_active()


def stop_voice_mode():
    """
    Stop voice mode if active.
    """
    if 'voice_controller' in st.session_state and st.session_state.voice_controller:
        st.session_state.voice_controller.stop_voice_mode()


# Export
__all__ = [
    'render_voice_mode_ui',
    'render_voice_controls',
    'render_voice_conversation_history',
    'render_voice_status',
    'get_voice_input_text',
    'is_voice_mode_active',
    'stop_voice_mode',
    'VoiceModeState'
]
