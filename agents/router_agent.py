"""
Router Agent - Detects user intent and routes to appropriate handlers.
Handles: medicines list, prescription upload, order history, profile, refill reminders, orders.
"""
from agents.state_schema import AgentState
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled
from tools.inventory_tool import get_all_medicines
from tools.patient_tool import get_patient, get_patient_orders
import json
import re


# Intent keywords for rule-based detection
INTENT_KEYWORDS = {
    "SHOW_MEDICINES": [
        "show medicines", "list medicines", "available medicines", "what medicines",
        "browse medicines", "medicine catalog", "all medicines", "medicine list",
        "medicines available", "show available", "what do you have",
        " catalogue", "catalog of medicines", "medicine inventory"
    ],
    "UPLOAD_PRESCRIPTION": [
        "upload prescription", "prescription upload", "upload rx", "prescribe",
        "prescription image", "doctor prescription", "medical prescription",
        "attach prescription", "send prescription", "share prescription"
    ],
    "ORDER_HISTORY": [
        "order history", "my orders", "past orders", "previous orders",
        "order list", "my purchases", "order details", "order status",
        "ordered medicines", "what i ordered", "order records"
    ],
    "REFILL_REMINDERS": [
        "refill reminder", "refill alerts", "medicine reminder", "reminder",
        " refill", "when to refill", "next refill", "refill due",
        "renew medicine", "medicine renewal", "refill needed"
    ],
    "SHOW_PROFILE": [
        "my profile", "show profile", "my account", "my details",
        "profile", "account details", "my information", "my info",
        "personal details", "patient profile"
    ],
    "MEDICINE_ORDER": [
        "order", "buy", "purchase", "get", "want", "need", "place order",
        "order now", "buy now", "can i get", "i want to order", "i want to buy",
        "please order", "i need", "can i have", "give me", "arrange",
        "order medicine", "buy medicine", "purchase medicine"
    ],
    "GENERAL_CHAT": [
        "hello", "hi", "hey", "how are you", "thank", "thanks", "help",
        "what can you do", "who are you", "good morning", "good evening"
    ]
}


def detect_intent_rule_based(user_input: str) -> str:
    """Detect user intent using keyword matching."""
    text_lower = user_input.lower()
    
    # Define priority order - more specific intents first
    priority_intents = [
        "UPLOAD_PRESCRIPTION",  # Check prescription first (most specific)
        "SHOW_MEDICINES",
        "ORDER_HISTORY",
        "REFILL_REMINDERS",
        "SHOW_PROFILE",
        "GENERAL_CHAT",
        "MEDICINE_ORDER"  # Default fallback
    ]
    
    # Check intents in priority order
    for intent in priority_intents:
        keywords = INTENT_KEYWORDS.get(intent, [])
        for keyword in keywords:
            if keyword in text_lower:
                return intent
    
    # Default to MEDICINE_ORDER if unclear (they might want to buy something)
    return "MEDICINE_ORDER"


def detect_intent_llm(user_input: str, user_language: str = "en") -> str:
    """Detect user intent using LLM with rule-based pre-filtering."""
    text_lower = user_input.lower()
    
    # First check for explicit keywords that should always use rule-based
    # This prevents the LLM from misclassifying clear intents
    explicit_intents = {
        "prescription": "UPLOAD_PRESCRIPTION",
        "refill": "REFILL_REMINDERS",
        "reminder": "REFILL_REMINDERS",
        "order history": "ORDER_HISTORY",
        "my orders": "ORDER_HISTORY",
        "my profile": "SHOW_PROFILE",
        "show medicines": "SHOW_MEDICINES",
        "available medicines": "SHOW_MEDICINES",
        "list medicines": "SHOW_MEDICINES",
    }
    
    for keyword, intent in explicit_intents.items():
        if keyword in text_lower:
            print(f"[Router] Rule-based override: '{keyword}' detected as {intent}")
            return intent
    
    # Now use LLM for more ambiguous cases
    llm = get_llm()
    
    if llm is None:
        return detect_intent_rule_based(user_input)
    
    prompt = f"""You are a pharmacy assistant routing system. Classify the user's intent from this message: "{user_input}"

Available intents:
- SHOW_MEDICINES: User wants to see available medicines list
- UPLOAD_PRESCRIPTION: User wants to upload a prescription
- ORDER_HISTORY: User wants to see their order history
- REFILL_REMINDERS: User wants to check refill reminders
- SHOW_PROFILE: User wants to see their profile
- MEDICINE_ORDER: User wants to order/purchase a medicine
- GENERAL_CHAT: General greeting or conversation

Return ONLY the intent name, nothing else."""

    try:
        response = invoke_with_trace(prompt, agent_name="router", model_type="flash")
        if response:
            response = response.strip().upper()
            # Validate response is a known intent
            for intent in INTENT_KEYWORDS.keys():
                if intent in response:
                    return intent
    except Exception as e:
        print(f"[Router] LLM detection failed: {e}")
    
    # Fallback to rule-based
    return detect_intent_rule_based(user_input)


def router_agent(state: AgentState) -> AgentState:
    """
    Main router agent that detects user intent and routes appropriately.
    """
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    user_id = state.get("user_id", "default")
    user_email = state.get("user_email", "")
    
    if not user_input:
        state["current_intent"] = "GENERAL_CHAT"
        state["intent_type"] = "GENERAL_CHAT"
        state["final_response"] = "Hello! How can I help you today?"
        return state
    
    # Detect intent
    intent = detect_intent_llm(user_input, user_language)
    
    state["current_intent"] = intent
    state["intent_type"] = intent
    
    print(f"[Router] Detected intent: {intent} for input: {user_input}")
    
    # Route to appropriate handler
    if intent == "SHOW_MEDICINES":
        return _handle_show_medicines(state, user_language)
    elif intent == "UPLOAD_PRESCRIPTION":
        return _handle_prescription_upload(state, user_language)
    elif intent == "ORDER_HISTORY":
        return _handle_order_history(state, user_id, user_language)
    elif intent == "REFILL_REMINDERS":
        return _handle_refill_reminders(state, user_id, user_language)
    elif intent == "SHOW_PROFILE":
        return _handle_show_profile(state, user_id, user_email, user_language)
    elif intent == "MEDICINE_ORDER":
        # Let the existing flow handle this
        return state
    else:
        return _handle_general_chat(state, user_language)


def _handle_show_medicines(state: AgentState, user_language: str) -> AgentState:
    """Handle show medicines intent."""
    try:
        medicines = get_all_medicines()
        
        if not medicines:
            state["final_response"] = "Sorry, there are no medicines currently available in our inventory."
            return state
        
        # Format response based on language
        if user_language == "hi":
            response = "📋 यहां उपलब्ध दवाइयां हैं:\n\n"
        elif user_language == "mr":
            response = "📋 येथे उपलब्ध औषधे आहेत:\n\n"
        else:
            response = "📋 Here are the available medicines:\n\n"
        
        # Show first 10 medicines with key details
        for i, med in enumerate(medicines[:10], 1):
            name = med.get("name", "Unknown")
            price = med.get("price", 0)
            stock = med.get("stock", 0)
            in_stock = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
            
            if user_language == "hi":
                response += f"{i}. {name}\n   💰 ₹{price} | {in_stock}\n"
            elif user_language == "mr":
                response += f"{i}. {name}\n   💰 ₹{price} | {in_stock}\n"
            else:
                response += f"{i}. {name}\n   💰 ₹{price} | {in_stock}\n"
        
        if len(medicines) > 10:
            remaining = len(medicines) - 10
            if user_language == "hi":
                response += f"\n... और {remaining} दवाइयां उपलब्ध हैं।"
            elif user_language == "mr":
                response += f"\n... आणखी {remaining} औषधे उपलब्ध आहेत."
            else:
                response += f"\n... and {remaining} more medicines available."
        
        # Add query prompt
        if user_language == "hi":
            response += "\n\nक्या आप कोई दवा ऑर्डर करना चाहेंगे?"
        elif user_language == "mr":
            response += "\n\nतुम्हाला कौणतेही औषधाचा ऑर्डर करायचा आहे का?"
        else:
            response += "\n\nWould you like to order any of these medicines?"
        
        state["recommended_medicines"] = medicines[:10]
        state["final_response"] = response
        
    except Exception as e:
        print(f"[Router] Error getting medicines: {e}")
        state["final_response"] = "Sorry, I couldn't fetch the medicines list. Please try again."
    
    return state


def _handle_prescription_upload(state: AgentState, user_language: str) -> AgentState:
    """Handle prescription upload intent."""
    if user_language == "hi":
        response = """📤 महत्वपूर्ण: आपको अपलोड करने के लिए फ़ोटो/पीडीएफ़ चुनना होगा।

आप निम्नलिखित तरीकों से पर्चा अपलोड कर सकते हैं:
• स्क्रीनशॉट लें
• फोटो कैप्चर करें
• पीडीएफ़ फ़ाइल अटैच करें

कृपया अपना पर्चा अपलोड करें, और मैं दवाइयां निकाल दूंगा।"""
    elif user_language == "mr":
        response = """📤 महत्त्वाचे: तुम्हाला अपलोड करण्यासाठी फोटो/पीडीएफ निवडावा लागेल.

तुम्ही खालील पद्धतींनी पावती अपलोड करू शकता:
• स्क्रीनशॉट घ्या
• फोटो कॅप्चर करा
• पीडीएफ फाइल जोडा

कृपया तुमची पावती अपलोड करा, आणि मी औषधे काढून घेईन."""
    else:
        response = """📤 To upload a prescription, please use the prescription upload feature.

You can upload your prescription by:
• Taking a photo
• Selecting from gallery
• Attaching a PDF file

Click the upload button in the sidebar to proceed, and I'll extract the medicines for you."""

    state["final_response"] = response
    return state


def _handle_order_history(state: AgentState, user_id: str, user_language: str) -> AgentState:
    """Handle order history intent."""
    try:
        orders = get_patient_orders(user_id)
        
        if not orders:
            if user_language == "hi":
                state["final_response"] = "आपका कोई ऑर्डर इतिहास नहीं है। क्या आप कोई दवा ऑर्डर करना चाहेंगे?"
            elif user_language == "mr":
                state["final_response"] = "तुमचा कोणताही ऑर्डर इतिहास नाही. तुम्हाला कौणतेही औषध ऑर्डर करायचे आहे का?"
            else:
                state["final_response"] = "You don't have any order history yet. Would you like to order some medicines?"
            return state
        
        # Format order history
        if user_language == "hi":
            response = "📦 आपके ऑर्डर:\n\n"
        elif user_language == "mr":
            response = "📦 तुमचे ऑर्डर:\n\n"
        else:
            response = "📦 Your Orders:\n\n"
        
        for i, order in enumerate(orders[:5], 1):
            product = order.get("product_name", "Unknown")
            qty = order.get("quantity", 0)
            total = order.get("total_price", 0)
            status = order.get("status", "Unknown")
            date = order.get("order_date", "N/A")
            
            if user_language == "hi":
                response += f"{i}. {product}\n   मात्रा: {qty} | कुल: ₹{total}\n   स्थिति: {status} | दिनांक: {date}\n\n"
            elif user_language == "mr":
                response += f"{i}. {product}\n   प्रमाण: {qty} | एकूण: ₹{total}\n   स्थिती: {status} | तारीख: {date}\n\n"
            else:
                response += f"{i}. {product}\n   Qty: {qty} | Total: ₹{total}\n   Status: {status} | Date: {date}\n\n"
        
        if len(orders) > 5:
            remaining = len(orders) - 5
            if user_language == "hi":
                response += f"... और {remaining} और ऑर्डर।"
            elif user_language == "mr":
                response += f"... आणखी {remaining} ऑर्डर."
            else:
                response += f"... and {remaining} more orders."
        
        state["final_response"] = response
        
    except Exception as e:
        print(f"[Router] Error getting order history: {e}")
        if user_language == "hi":
            state["final_response"] = "मुझे आपका ऑर्डर इतिहास लाने में समस्या आ रही है।"
        elif user_language == "mr":
            state["final_response"] = "मला तुमचा ऑर्डर इतिहास आणण्यात समस्या येत आहे."
        else:
            state["final_response"] = "Sorry, I couldn't fetch your order history. Please try again."
    
    return state


def _handle_refill_reminders(state: AgentState, user_id: str, user_language: str) -> AgentState:
    """Handle refill reminders intent."""
    try:
        # Get patient's orders to calculate refill dates
        orders = get_patient_orders(user_id)
        
        if not orders:
            if user_language == "hi":
                state["final_response"] = "आपके पास कोई ऑर्डर नहीं है जिसके लिए रिफिल की आवश्यकता हो। क्या आप कोई दवा ऑर्डर करना चाहेंगे?"
            elif user_language == "mr":
                state["final_response"] = "तुमच्याकडे कोणताही ऑर्डर नाही ज्यासाठी रिफिल आवश्यक आहे. तुम्हाला औषध ऑर्डर करायचे आहे का?"
            else:
                state["final_response"] = "You don't have any orders that need refilling. Would you like to order some medicines?"
            return state
        
        # Calculate refill info based on last order dates
        from datetime import datetime, timedelta
        
        refill_items = []
        for order in orders:
            order_date = order.get("order_date")
            if order_date:
                try:
                    # Parse date (assuming ISO format)
                    if isinstance(order_date, str):
                        order_date = datetime.fromisoformat(order_date.replace("Z", "+00:00"))
                    
                    days_since = (datetime.now() - order_date).days
                    days_until_refill = 30 - days_since  # Assuming 30-day supply
                    
                    if days_until_refill <= 7:  # Within a week
                        refill_items.append({
                            "product": order.get("product_name"),
                            "days_until": days_until_refill
                        })
                except:
                    pass
        
        if not refill_items:
            if user_language == "hi":
                response = "✅ अभी आपको कोई रिफिल की आवश्यकता नहीं है। हम आपको समय पर याद दिलाएंगे!"
            elif user_language == "mr":
                response = "✅ सध्या तुम्हाला कोणत्याही रिफिलची गरज नाही. आमी तुम्हाला वेळेवर आठवण करू!"
            else:
                response = "✅ You don't have any refills due right now. We'll remind you in time!"
        else:
            if user_language == "hi":
                response = "🔔 आपकी आगामी रिफिल:\n\n"
            elif user_language == "mr":
                response = "🔔 तुमची आगामी रिफिल:\n\n"
            else:
                response = "🔔 Your upcoming refills:\n\n"
            
            for item in refill_items[:5]:
                if user_language == "hi":
                    response += f"• {item['product']} - {item['days_until']} दिनों में\n"
                elif user_language == "mr":
                    response += f"• {item['product']} - {item['days_until']} दिवसांमध्ये\n"
                else:
                    response += f"• {item['product']} - in {item['days_until']} days\n"
        
        state["refill_alerts"] = refill_items
        state["final_response"] = response
        
    except Exception as e:
        print(f"[Router] Error getting refill reminders: {e}")
        if user_language == "hi":
            state["final_response"] = "मुझे आपकी रिफिल जानकारी लाने में समस्या आ रही है।"
        elif user_language == "mr":
            state["final_response"] = "मला तुमची रिफिल माहिती आणण्यात समस्या येत आहे."
        else:
            state["final_response"] = "Sorry, I couldn't fetch your refill reminders. Please try again."
    
    return state


def _handle_show_profile(state: AgentState, user_id: str, user_email: str, user_language: str) -> AgentState:
    """Handle show profile intent."""
    try:
        patient = get_patient(user_id)
        
        if not patient:
            if user_language == "hi":
                response = "मुझे आपकी प्रोफाइल नहीं मिली। कृपया अपना ईमेल या फोन नंबर जांचें।"
            elif user_language == "mr":
                response = "मला तुमची प्रोफाइल सापडली नाही. कृपया तुमचा ईमेल किंवा फोन नंबर तपासा."
            else:
                response = "I couldn't find your profile. Please check your email or phone number."
            state["final_response"] = response
            return state
        
        name = patient.get("name", "N/A")
        age = patient.get("age", "N/A")
        gender = patient.get("gender", "N/A")
        phone = patient.get("phone", "N/A")
        email = patient.get("email", "N/A")
        address = patient.get("address", "N/A")
        
        if user_language == "hi":
            response = f"""👤 आपकी प्रोफाइल:

नाम: {name}
उम्र: {age}
लिंग: {gender}
फोन: {phone}
ईमेल: {email}
पता: {address}

क्या आपको कुछ और चाहिए?"""
        elif user_language == "mr":
            response = f"""👤 तुमची प्रोफाइल:

नाव: {name}
वय: {age}
लिंग: {gender}
फोन: {phone}
ईमेल: {email}
पत्ता: {address}

तुम्हाला काहीही हवे आहे का?"""
        else:
            response = f"""👤 Your Profile:

Name: {name}
Age: {age}
Gender: {gender}
Phone: {phone}
Email: {email}
Address: {address}

Is there anything else you need?"""
        
        state["final_response"] = response
        
    except Exception as e:
        print(f"[Router] Error getting profile: {e}")
        if user_language == "hi":
            state["final_response"] = "मुझे आपकी प्रोफाइल लाने में समस्या आ रही है।"
        elif user_language == "mr":
            state["final_response"] = "मला तुमची प्रोफाइल आणण्यात समस्या येत आहे."
        else:
            state["final_response"] = "Sorry, I couldn't fetch your profile. Please try again."
    
    return state


def _handle_general_chat(state: AgentState, user_language: str) -> AgentState:
    """Handle general chat intent."""
    user_input = state.get("user_input", "").lower()
    
    greetings = ["hello", "hi", "hey", "good morning", "good evening", "good night"]
    thanks = ["thank", "thanks", "thankyou"]
    help_requests = ["help", "what can you do", "who are you"]
    
    for word in greetings:
        if word in user_input:
            if user_language == "hi":
                state["final_response"] = "नमस्ते! मैं SwasthyaSarthi हूं, आपका फार्मेसी सहायक। मैं आपकी दवाइयां ऑर्डर करने, प्रिस्क्रिप्शन अपलोड करने, और आपके स्वास्थ्य की देखभाल में मदद कर सकता हूं। आपको क्या चाहिए?"
            elif user_language == "mr":
                state["final_response"] = "नमस्कार! मी SwasthyaSarthi आहे, तुमचा फार्मसी सहायक. मी तुमची औषधे ऑर्डर करण्यात, पावती अपलोड करण्यात आणि तुमच्या आरोग्याची काळजी घेण्यात मदत करू शकतो. तुम्हाला काय हवे आहे?"
            else:
                state["final_response"] = "Hello! I'm SwasthyaSarthi, your pharmacy assistant. I can help you order medicines, upload prescriptions, and manage your health. What would you like to do?"
            return state
    
    for word in thanks:
        if word in user_input:
            if user_language == "hi":
                state["final_response"] = "आपका स्वागत है! क्या आपको कुछ और चाहिए?"
            elif user_language == "mr":
                state["final_response"] = "तुमचे स्वागत आहे! तुम्हाला काहीही हवे आहे का?"
            else:
                state["final_response"] = "You're welcome! Is there anything else you need?"
            return state
    
    for phrase in help_requests:
        if phrase in user_input:
            if user_language == "hi":
                state["final_response"] = """मैं आपकी इनमें मदद कर सकता हूं:

🛒 दवाइयां ऑर्डर करें
📋 प्रिस्क्रिप्शन अपलोड करें
📦 अपने ऑर्डर देखें
🔔 रिफिल रिमाइंडर चेक करें
👤 अपनी प्रोफाइल देखें

आपको क्या चाहिए?"""
            elif user_language == "mr":
                state["final_response"] = """मी तुमची खालील गोष्टींमध्ये मदत करू शकतो:

🛒 औषधे ऑर्डर करा
📋 पावती अपलोड करा
📦 तुमचे ऑर्डर पहा
🔔 रिफिल रिमाइंडर तपासा
👤 तुमची प्रोफाइल पहा

तुम्हाला काय हवे आहे?"""
            else:
                state["final_response"] = """I can help you with:

🛒 Order medicines
📋 Upload prescription
📦 View your orders
🔔 Check refill reminders
👤 View your profile

What would you like to do?"""
            return state
    
    # Default response
    if user_language == "hi":
        state["final_response"] = "मुझे समझ नहीं आया। क्या आप दवाई ऑर्डर करना चाहेंगे, या कुछ और मदद चाहिए?"
    elif user_language == "mr":
        state["final_response"] = "मला समजले नाही. तुम्हाला औषध ऑर्डर करायचे आहे का, किंवा काहीही मदत हवी आहे?"
    else:
        state["final_response"] = "I didn't quite get that. Would you like to order some medicine, or is there something else I can help you with?"
    
    return state
