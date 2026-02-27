import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
from orchestration.graph import app_graph

from agents.refill_trigger_agent import get_proactive_refill_summary
from tools.inventory_tool import get_medicine, get_all_medicines
from tools.refill_tool import check_refills

from frontend.components.chat_ui import display_chat
from frontend.components.admin_panel import show_admin_dashboard
from frontend.components.voice_input import record_voice, test_microphone
from frontend.components.tts_helper import text_to_speech, VOICE_MAP, LANGUAGE_CODE_MAP

# Voice Agent Components
from frontend.components.voice_agent import (
    render_voice_mode_ui, 
    is_voice_mode_active, 
    stop_voice_mode,
    get_voice_input_text
)
from frontend.components.language_detector import detect_language, get_language_code


# API Base URL
API_BASE_URL = "http://localhost:8001"

# MUST be the first Streamlit command
st.set_page_config(page_title="SwasthyaSarthi", layout="wide", page_icon="🩺")

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'pending_order' not in st.session_state:
    st.session_state.pending_order = None
if 'agent_trace' not in st.session_state:
    st.session_state.agent_trace = []
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'lang_choice' not in st.session_state:
    st.session_state.lang_choice = "English"
if 'interaction_mode' not in st.session_state:
    st.session_state.interaction_mode = "chat"  # "chat" or "voice"
if 'last_order_details' not in st.session_state:
    st.session_state.last_order_details = None

# Language code mapping (alias for use in app)
lang_code_map = LANGUAGE_CODE_MAP



def check_backend_connection():
    """Check if backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False


def login_user(email: str, password: str):
    """Login user via API"""
    try:
        if not check_backend_connection():
            return False, "Backend not running. Start with: uvicorn backend.main:app --reload"
        
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.user_email = email
            st.session_state.authenticated = True
            return True, "Login successful!"
        elif response.status_code == 401:
            return False, "Invalid email or password"
        else:
            return False, f"Login failed: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to backend. Is server running on port 8000?"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def register_user(email: str, password: str, full_name: str = None):
    """Register new user via API"""
    try:
        if not check_backend_connection():
            return False, "Backend not running. Start with: uvicorn backend.main:app --reload"
        
        response = requests.post(
            f"{API_BASE_URL}/register",
            params={"email": email, "password": password, "full_name": full_name}
        )
        if response.status_code == 201:
            return True, "Registration successful! Please login."
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return False, error_data.get("detail", "Registration failed")
            except:
                return False, "User already exists. Please login instead."
        else:
            return False, f"Registration failed: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to backend. Is server running on port 8000?"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def register_admin(email: str, password: str, full_name: str = None):
    """Register new admin via API"""
    try:
        if not check_backend_connection():
            return False, "Backend not running. Start with: uvicorn backend.main:app --reload"
        
        response = requests.post(
            f"{API_BASE_URL}/register-admin",
            params={"email": email, "password": password, "full_name": full_name}
        )
        if response.status_code == 201:
            return True, "Admin registration successful! Please login as admin."
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return False, error_data.get("detail", "Registration failed")
            except:
                return False, "Admin user already exists. Please login instead."
        else:
            return False, f"Registration failed: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to backend. Is server running on port 8000?"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def logout_user():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.access_token = None
    st.session_state.pending_order = None
    st.session_state.agent_trace = []
    st.session_state.last_order_details = None
    st.rerun()


def show_login_page():
    """Display login/signup page with User and Admin options"""
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
    }
    .stTitle {
        text-align: center;
        color: #2E86C1;
    }
    .admin-box {
        background-color: #1e3a5f;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .user-box {
        background-color: #2e7d32;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🩺 SwasthyaSarthi")
    st.markdown("### Your Friendly Pharmacy Assistant")
    
    # Choose login type
    st.markdown("## Choose Login Type:")
    login_type = st.radio("", ["👤 User Login", "🔐 Admin Login"], horizontal=True)
    
    if login_type == "👤 User Login":
        # User Login Section
        st.markdown("### 👤 User Portal")
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
        
        with tab1:
            st.markdown("#### Login to your account")
            login_email = st.text_input("Email", key="user_login_email", placeholder="your@email.com")
            login_password = st.text_input("Password", type="password", key="user_login_password")
            
            if st.button("Sign In as User", type="primary", key="user_login_btn"):
                if login_email and login_password:
                    success, message = login_user(login_email, login_password)
                    if success:
                        st.session_state.is_admin = False
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter email and password")
        
        with tab2:
            st.markdown("#### Create a new user account")
            signup_email = st.text_input("Email", key="user_signup_email", placeholder="your@email.com")
            signup_name = st.text_input("Full Name (Optional)", key="user_signup_name", placeholder="John Doe")
            signup_password = st.text_input("Password", type="password", key="user_signup_password")
            
            st.markdown("""
            **Password Requirements:**
            - At least 4 characters
            """)
            
            signup_confirm = st.text_input("Confirm Password", type="password", key="user_signup_confirm")
            
            if st.button("Sign Up as User", type="primary", key="user_signup_btn"):
                if signup_email and signup_password:
                    if signup_password != signup_confirm:
                        st.error("Passwords do not match!")
                    else:
                        success, message = register_user(signup_email, signup_password, signup_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter email and password")
    
    else:
        # Admin Login Section
        st.markdown("### 🔐 Admin Portal")
        
        tab1, tab2 = st.tabs(["🔑 Admin Sign In", "📝 Register Admin"])
        
        with tab1:
            st.markdown("#### Admin Login")
            admin_login_email = st.text_input("Admin Email", key="admin_login_email", placeholder="admin@email.com")
            admin_login_password = st.text_input("Admin Password", type="password", key="admin_login_password")
            
            if st.button("Sign In as Admin", type="primary", key="admin_login_btn"):
                if admin_login_email and admin_login_password:
                    success, message = login_user(admin_login_email, admin_login_password)
                    if success:
                        # Check if user is admin
                        try:
                            response = requests.get(
                                f"{API_BASE_URL}/me",
                                headers={"Authorization": f"Bearer {st.session_state.access_token}"}
                            )
                            if response.status_code == 200:
                                user_data = response.json()
                                if user_data.get("is_admin", False):
                                    st.session_state.is_admin = True
                                    st.success("Admin login successful!")
                                    st.rerun()
                                else:
                                    st.session_state.authenticated = False
                                    st.session_state.access_token = None
                                    st.error("Access denied. Only admin users can login here.")
                            else:
                                st.error("Failed to verify admin status")
                        except Exception as e:
                            st.error(f"Error verifying admin: {e}")
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter email and password")
            
            st.caption("⚠️ Only authorized administrators can access this portal.")
        
        with tab2:
            st.markdown("#### Register New Admin")
            st.caption("Note: This is for first-time admin setup. Use existing admin credentials to create new admins.")
            
            admin_signup_email = st.text_input("Admin Email", key="admin_signup_email", placeholder="admin@email.com")
            admin_signup_name = st.text_input("Full Name (Optional)", key="admin_signup_name", placeholder="Admin Name")
            admin_signup_password = st.text_input("Password", type="password", key="admin_signup_password")
            
            st.markdown("""
            **Password Requirements:**
            - At least 4 characters
            """)
            
            admin_signup_confirm = st.text_input("Confirm Password", type="password", key="admin_signup_confirm")
            
            if st.button("Register Admin", type="primary", key="admin_signup_btn"):
                if admin_signup_email and admin_signup_password:
                    if admin_signup_password != admin_signup_confirm:
                        st.error("Passwords do not match!")
                    else:
                        success, message = register_admin(admin_signup_email, admin_signup_password, admin_signup_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter email and password")
    
    st.markdown("---")
    st.caption("💊 SwasthyaSarthi - Your Pharmacy Assistant")

# Check if user is authenticated
if not st.session_state.authenticated:
    show_login_page()
else:
    st.title("🩺 SwasthyaSarthi – Your Friendly Pharmacy Assistant")
    
    # Show user info and logout in sidebar
    st.sidebar.header(f"👤 {st.session_state.user_email}")
    if st.session_state.is_admin:
        st.sidebar.markdown("🔐 **Admin Mode**")
    if st.sidebar.button("🚪 Logout"):
        logout_user()

    # --- Navbar Navigation ---
    # Check if user is admin
    try:
        if st.session_state.access_token and not st.session_state.is_admin:
            user_response = requests.get(
                f"{API_BASE_URL}/me",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"}
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                st.session_state.is_admin = user_data.get("is_admin", False)
    except:
        pass

    # Navigation options based on role
    nav_options = ["💬 User Dashboard"]
    if st.session_state.is_admin:
        nav_options.append("🏥 Admin Dashboard")
    
    selected_tab = st.radio("Go to", nav_options, horizontal=True)
    
    if selected_tab == "🏥 Admin Dashboard":
        show_admin_dashboard()
    else:
        # ==================== USER DASHBOARD - CHAT INTERFACE ====================
        
        # Mode Selection: Chat vs Voice
        st.markdown("### 🔄 Select Interaction Mode")
        mode_col1, mode_col2 = st.columns(2)
        
        with mode_col1:
            if st.button("💬 Chat Mode", 
                       type="primary" if st.session_state.interaction_mode == "chat" else "secondary",
                       key="mode_chat"):
                st.session_state.interaction_mode = "chat"
                # Stop voice mode if switching to chat
                if is_voice_mode_active():
                    stop_voice_mode()
                st.rerun()
        
        with mode_col2:
            if st.button("🎙️ Voice Mode", 
                       type="primary" if st.session_state.interaction_mode == "voice" else "secondary",
                       key="mode_voice"):
                st.session_state.interaction_mode = "voice"
                st.rerun()
        
        st.markdown("---")
        
        # Language Selection (only in chat mode or for voice language preference)
        st.markdown("### 🌍 Choose Your Language")
        col_lang1, col_lang2 = st.columns([1, 2])
        
        with col_lang1:
            lang_choice = st.selectbox(
                "Select Language",
                options=list(LANGUAGE_CODE_MAP.keys()),
                index=list(LANGUAGE_CODE_MAP.keys()).index(st.session_state.lang_choice),
                key="lang_selector"
            )
            st.session_state.lang_choice = lang_choice
        
        with col_lang2:
            st.info(f"💬 I'll speak with you in {lang_choice}!")
        
        st.markdown("---")
        
        # Initialize voice_active flag
        voice_active = False
        
        # ==================== VOICE MODE INTERFACE ====================
        if st.session_state.interaction_mode == "voice":
            st.subheader("🎙️ Voice Conversation")
            
            # Render voice agent UI
            voice_active = render_voice_mode_ui(
                user_id=st.session_state.user_email,
                user_email=st.session_state.user_email,
                voice_type="female"
            )
            
        # If voice mode is active, show voice interface only
        if voice_active:

            st.markdown("---")
            st.info("🎤 Voice mode is active. Speak naturally and I'll respond automatically.")
            
            # Show chat history from voice interactions
            voice_text = get_voice_input_text()
            if voice_text:
                st.markdown(f"**Last heard:** _{voice_text}_")
            
            # Footer for voice mode
            st.markdown("---")
            st.caption("🩺 SwasthyaSarthi - Your Friendly Pharmacy Assistant | Powered by AI Agents")
        
        # ==================== CHAT MODE INTERFACE ====================
        else:
            st.subheader("💬 Chat with SwasthyaSarthi")



        if 'history' not in st.session_state:
            st.session_state.history = []

        # Show pending order confirmation if exists
        pending_order = st.session_state.get("pending_order")
        
        if pending_order:
            st.info(f"📋 **Pending Order Confirmation:** {pending_order.get('product_name')} x{pending_order.get('quantity')} - ₹{pending_order.get('price', 0):.2f}")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("✅ Yes, Place My Order", key="confirm_order_btn"):
                    try:
                        with st.spinner("Placing your order..."):
                            result = app_graph.invoke(
                                {
                                    "user_input": "yes",
                                    "user_id": st.session_state.user_email,
                                    "user_phone": None,
                                    "user_email": st.session_state.user_email,
                                    "user_language": lang_code_map.get(lang_choice, "en"),
                                    "user_address": None,
                                    "structured_order": {"product_name": pending_order.get("product_name"), "quantity": pending_order.get("quantity")},
                                    "safety_result": {"approved": True},
                                    "final_response": "",
                                    "is_proactive": False,
                                    "refill_alerts": [],
                                    "requires_confirmation": True,
                                    "confirmation_message": "",
                                    "user_confirmed": True,
                                    "pending_order_details": pending_order,
                                    "agent_trace": st.session_state.agent_trace,
                                    "is_order_request": True,
                                    "info_product": "",
                                    "info_response": ""
                                },
                                config={"configurable": {"thread_id": f"{st.session_state.user_email}:session"}}
                            )

                            reply = result.get("final_response", "")
                            st.session_state.history.append(("SwasthyaSarthi", reply))
                            st.session_state.pending_order = None
                            st.session_state.agent_trace = result.get("agent_trace", [])
                            
                            # Store order details for price display
                            order_price_details = result.get("order_price_details")
                            if order_price_details:
                                st.session_state.last_order_details = order_price_details
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col_confirm2:
                if st.button("❌ No, Cancel Please", key="cancel_order_btn"):
                    st.session_state.history.append(("SwasthyaSarthi", "No problem! Your order has been cancelled. Is there anything else I can help you with?"))
                    st.session_state.pending_order = None
                    st.rerun()

        # Display price summary card for last confirmed order
        last_order = st.session_state.get("last_order_details")
        if last_order:
            st.markdown("""
                <div style="
                    background-color: #d4edda;
                    border: 2px solid #28a745;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 15px 0;
                ">
                    <h3 style="color: #155724; margin-top: 0;">✅ Order Confirmed</h3>
                    <table style="width: 100%; color: #155724;">
                        <tr>
                            <td><strong>Medicine:</strong></td>
                            <td>{}</td>
                        </tr>
                        <tr>
                            <td><strong>Quantity:</strong></td>
                            <td>{}</td>
                        </tr>
                        <tr>
                            <td><strong>Price per Unit:</strong></td>
                            <td>₹{:.2f}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Price:</strong></td>
                            <td><strong>₹{:.2f}</strong></td>
                        </tr>
                    </table>
                </div>
            """.format(
                last_order.get("product_name", "N/A"),
                last_order.get("quantity", 0),
                last_order.get("unit_price", 0),
                last_order.get("total_price", 0)
            ), unsafe_allow_html=True)
            
            # Clear the order details after displaying
            st.session_state.last_order_details = None

        # Text Input Section (Chat Mode Only)
        st.markdown("### ⌨️ Type your message")
        user_input = st.text_input("You:", key="text_input", 
                                   placeholder=f"Type your message here...")

        # Send button
        if st.button("Send 💬", type="primary") and user_input:
            final_input = user_input
            
            if final_input:
                st.session_state.history.append(("You", final_input))
                
                # Detect language from input for auto-response matching
                lang_detect = detect_language(final_input, use_llm_fallback=True)
                detected_lang = lang_detect.get("language", lang_choice)
                
                try:
                    with st.spinner("🤖 Let me help you with that..."):
                        result = app_graph.invoke(
                            {
                                "user_input": final_input,
                                "user_id": st.session_state.user_email,
                                "user_phone": None,
                                "user_email": st.session_state.user_email,
                                "user_language": lang_code_map.get(detected_lang, "en"),
                                "user_address": None,
                                "structured_order": {},
                                "safety_result": {},
                                "final_response": "",
                                "is_proactive": False,
                                "refill_alerts": [],
                                "requires_confirmation": False,
                                "confirmation_message": "",
                                "user_confirmed": None,
                                "pending_order_details": None,
                                "agent_trace": [],
                                "is_order_request": True,
                                "info_product": "",
                                "info_response": "",
                                "metadata": {
                                    "agent_name": "chat_interface",
                                    "action": "process_chat_input",
                                    "language": detected_lang,
                                    "interaction_mode": "chat"  # For LangSmith observability
                                }
                            },
                            config={"configurable": {"thread_id": f"{st.session_state.user_email}:session"}}
                        )

                        
                        st.session_state.agent_trace = result.get("agent_trace", [])
                        
                        reply = result.get("final_response", "")
                        
                        requires_confirm = result.get("requires_confirmation", False)
                        pending_details = result.get("pending_order_details")
                        
                        if requires_confirm and pending_details and not result.get("user_confirmed"):
                            st.session_state.pending_order = pending_details
                            reply = result.get("confirmation_message", "Would you like me to place this order for you?")
                            st.info("📋 Please confirm your order below!")
                        else:
                            st.success("✅ Got it! Let me know if you need anything else.")
                            
                            # Check if this was a successful order and store price details
                            order_price_details = result.get("order_price_details")
                            if order_price_details:
                                st.session_state.last_order_details = order_price_details
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Error: {error_msg}")
                    reply = "Sorry, I encountered an error. Please try again."
                
                st.session_state.history.append(("SwasthyaSarthi", reply))
                
                # CHAT MODE: No TTS - text only response
                # Voice responses only happen in Voice Mode

        # Display chat history
        st.markdown("### 📝 Chat History")
        for speaker, message in st.session_state.history:
            if speaker == "You":
                st.markdown(f"**👤 You:** {message}")
            else:
                st.markdown(f"**🩺 SwasthyaSarthi:** {message}")

        if st.session_state.history:
            if st.button("Clear Chat 🗑️"):
                st.session_state.history = []
                st.session_state.pending_order = None
                st.session_state.last_order_details = None
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
                        st.session_state.history.append(("System", "All medicines are in stock!"))
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

        # --- Footer for Chat Mode ---
        st.markdown("---")
        st.caption("🩺 SwasthyaSarthi - Your Friendly Pharmacy Assistant | Powered by AI Agents")
