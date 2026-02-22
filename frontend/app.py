import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from orchestration.graph import app_graph

from agents.refill_trigger_agent import get_proactive_refill_summary
from tools.inventory_tool import get_medicine, get_all_medicines
from tools.refill_tool import check_refills

from components.chat_ui import display_chat
from components.admin_panel import show_admin_dashboard
from components.voice_input import record_voice, test_microphone
from components.tts_helper import text_to_speech, VOICE_MAP


st.set_page_config(page_title="SwasthyaSarthi", layout="wide", page_icon="🩺")
st.title("🩺 SwasthyaSarthi – Multi-Lingual Pharmacy Voice Assistant")

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["💬 Chat", "🏥 Admin Dashboard"])

# --- Voice Settings Section (for Chat page) ---
st.sidebar.header("🎤 Voice Settings")

# Check microphone availability
if st.sidebar.button("Test Microphone"):
    test_microphone()

# Voice type selection
voice_type = st.sidebar.radio("Choose Voice Type", ["Female", "Male"], horizontal=True)

# Language Selection
lang_choice = st.sidebar.selectbox("🌐 Choose Language", ["English", "Hindi", "Marathi", "Bengali", "Malayalam", "Gujarati"])
lang_code_map = {"English": "en", "Hindi": "hi", "Marathi": "mr", "Bengali": "bn", "Malayalam": "ml", "Gujarati": "gu"}

# Show available voice for selected language
st.sidebar.info(f"🎙️ Voice: {VOICE_MAP.get(lang_choice, {}).get(voice_type.lower(), 'Not available')}")

# --- Page Routing ---
if page == "🏥 Admin Dashboard":
    show_admin_dashboard()
    
else:
    # ==================== CHAT INTERFACE ====================
    
    st.subheader("💬 Chat with SwasthyaSarthi")

    if 'history' not in st.session_state:
        st.session_state.history = []

    # Voice Input Section
    st.markdown("### 🎤 Voice Input")
    col_voice1, col_voice2 = st.columns([2, 1])

    with col_voice1:
        st.info(f"Click the button below and speak in {lang_choice}")
        
        # Voice input button
        if st.button(f"🎤 Speak in {lang_choice}", key="voice_input_btn"):
            with st.spinner("🎙️ Recording... Speak now!"):
                user_text = record_voice(lang_choice, duration=5)
                if user_text:
                    st.session_state.voice_input = user_text
                    st.rerun()

    # Display voice input result if available
    if 'voice_input' in st.session_state:
        st.success(f"🎤 You said: {st.session_state.voice_input}")

    # Text Input Section
    st.markdown("### ⌨️ Or type your message")
    user_input = st.text_input("You:", key="text_input", 
                               placeholder=f"Type your message in {lang_choice} or use voice input above...")

    # Send button
    if st.button("Send 💬", type="primary") or (user_input and 'voice_input' in st.session_state):
        # Use voice input if available, otherwise use text input
        final_input = st.session_state.get('voice_input', user_input) if user_input else st.session_state.get('voice_input', '')
        
        if final_input:
            # Clear voice input after use
            if 'voice_input' in st.session_state:
                del st.session_state.voice_input
                
            st.session_state.history.append(("You", final_input))
            
            # Invoke agents workflow
            try:
                with st.spinner("🤖 Processing your request..."):
                    result = app_graph.invoke({
                        "user_input": final_input,
                        "user_id": None,
                        "user_phone": None,
                        "user_email": None,
                        "user_language": lang_code_map.get(lang_choice, "en"),
                        "user_address": None,
                        "structured_order": {},
                        "safety_result": {},
                        "final_response": "",
                        "is_proactive": False,
                        "refill_alerts": []
                    })
                    reply = result.get("final_response", "")
                    st.success("✅ Request processed successfully!")
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ Error: {error_msg}")
                reply = "Sorry, I encountered an error. Please check the console for details."
            
            # Display text response
            st.session_state.history.append(("SwasthyaSarthi", reply))

            # Convert the reply to speech in chosen language
            with st.spinner("🔊 Converting response to speech..."):
                try:
                    audio_data = text_to_speech(
                        reply, 
                        language=lang_choice, 
                        voice_type=voice_type.lower(),
                        use_edge_tts=False  # Use gTTS for reliability
                    )
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                    else:
                        st.warning("⚠️ Could not generate audio. Showing text only.")
                except Exception as e:
                    st.warning(f"⚠️ TTS unavailable: {e}. Showing text only.")

    # Display chat history
    st.markdown("### 📝 Chat History")
    for speaker, message in st.session_state.history:
        if speaker == "You":
            st.markdown(f"**👤 You:** {message}")
        else:
            st.markdown(f"**🩺 SwasthyaSarthi:** {message}")

    # Clear chat button
    if st.session_state.history:
        if st.button("Clear Chat 🗑️"):
            st.session_state.history = []
            st.rerun()
    
    # --- Quick Actions Section ---
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Check My Refills"):
            with st.spinner("Checking for refill alerts..."):
                try:
                    result = check_refills(days_ahead=7)
                    alerts = result.get("alerts", [])
                    if alerts:
                        st.session_state.history.append(("System", f"🔔 You have {len(alerts)} medicines that need refilling soon!"))
                    else:
                        st.session_state.history.append(("System", "✅ No refills needed at this time."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("📦 View Inventory"):
            try:
                meds = get_all_medicines()
                low_stock = [m for m in meds if m.get("stock", 0) < 10]
                if low_stock:
                    st.session_state.history.append(("System", f"⚠️ {len(low_stock)} medicines are running low on stock!"))
                else:
                    st.session_state.history.append(("System", "✅ All medicines are in stock!"))
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col3:
        if st.button("💊 Search Medicine"):
            search_term = st.text_input("Enter medicine name", key="quick_search")
            if search_term:
                try:
                    med = get_medicine(search_term)
                    if med:
                        stock_status = "✅ In Stock" if med.get("stock", 0) > 0 else "❌ Out of Stock"
                        rx_status = "ℹ️ Prescription Required" if med.get("prescription_required") else "✅ No Prescription Needed"
                        info = f"**{med.get('name')}**\n- Stock: {med.get('stock', 0)}\n- Price: ₹{med.get('price', 0):.2f}\n- {rx_status}"
                        st.session_state.history.append(("System", info))
                    else:
                        st.session_state.history.append(("System", f"❌ Medicine '{search_term}' not found."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Footer ---
st.markdown("---")
st.caption("🩺 SwasthyaSarthi - Multi-Lingual Pharmacy Voice Assistant | Powered by AI Agents")
