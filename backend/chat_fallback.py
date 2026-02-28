"""
Fallback Chat Handler - Provides direct responses for common intents
without relying on the LangGraph agent workflow.
"""
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def get_all_medicines_direct():
    """Get all medicines directly from the database."""
    try:
        res = requests.get(f"{API_URL}/medicines", timeout=5)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Fallback] Error getting medicines: {e}")
        return []

def get_patient_orders_direct(patient_id: str):
    """Get patient orders directly."""
    try:
        res = requests.get(f"{API_URL}/patients/{patient_id}/orders", timeout=5)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Fallback] Error getting orders: {e}")
        return []

def get_patient_direct(patient_id: str):
    """Get patient details directly."""
    try:
        res = requests.get(f"{API_URL}/patients/{patient_id}", timeout=5)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, dict) and "error" in data:
            return None
        return data
    except Exception as e:
        print(f"[Fallback] Error getting patient: {e}")
        return None

def get_lang_code(language: str) -> str:
    """Convert language name to code."""
    lang_map = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr",
        "en": "en",
        "hi": "hi",
        "mr": "mr"
    }
    return lang_map.get(language, "en")

def handle_show_medicines(language: str = "English"):
    """Handle show medicines intent."""
    medicines = get_all_medicines_direct()
    lang_code = get_lang_code(language)
    
    if not medicines:
        return {
            "text": "Sorry, there are no medicines currently available in our inventory.",
            "intent": "SHOW_MEDICINES"
        }
    
    if lang_code == "hi":
        response = "📋 यहां उपलब्ध दवाइयां हैं:\n\n"
    elif lang_code == "mr":
        response = "📋 येथे उपलब्ध औषधे आहेत:\n\n"
    else:
        response = "📋 Here are the available medicines:\n\n"
    
    for i, med in enumerate(medicines[:10], 1):
        name = med.get("name", "Unknown")
        price = med.get("price", 0)
        stock = med.get("stock", 0)
        in_stock = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
        response += f"{i}. {name}\n   💰 ₹{price} | {in_stock}\n"
    
    if len(medicines) > 10:
        remaining = len(medicines) - 10
        if lang_code == "hi":
            response += f"\n... और {remaining} दवाइयां उपलब्ध हैं।"
        elif lang_code == "mr":
            response += f"\n... आणखी {remaining} औषधे उपलब्ध आहेत."
        else:
            response += f"\n... and {remaining} more medicines available."
    
    if lang_code == "hi":
        response += "\n\nक्या आप कोई दवा ऑर्डर करना चाहेंगे?"
    elif lang_code == "mr":
        response += "\n\nतुम्हाला कौणतेही औषधाचा ऑर्डर करायचा आहे का?"
    else:
        response += "\n\nWould you like to order any of these medicines?"
    
    return {"text": response, "intent": "SHOW_MEDICINES"}

def handle_order_history(patient_id: str, language: str = "English"):
    """Handle order history intent."""
    orders = get_patient_orders_direct(patient_id)
    lang_code = get_lang_code(language)
    
    if not orders:
        if lang_code == "hi":
            return {"text": "आपका कोई ऑर्डर इतिहास नहीं है। क्या आप कोई दवा ऑर्डर करना चाहेंगे?", "intent": "ORDER_HISTORY"}
        elif lang_code == "mr":
            return {"text": "तुमचा कोणताही ऑर्डर इतिहास नाही. तुम्हाला कौणतेही औषध ऑर्डर करायचे आहे का?", "intent": "ORDER_HISTORY"}
        else:
            return {"text": "You don't have any order history yet. Would you like to order some medicines?", "intent": "ORDER_HISTORY"}
    
    if lang_code == "hi":
        response = "📦 आपके ऑर्डर:\n\n"
    elif lang_code == "mr":
        response = "📦 तुमचे ऑर्डर:\n\n"
    else:
        response = "📦 Your Orders:\n\n"
    
    for i, order in enumerate(orders[:5], 1):
        product = order.get("product_name", "Unknown")
        qty = order.get("quantity", 0)
        total = order.get("total_price", 0)
        status = order.get("status", "Unknown")
        date = order.get("order_date", "N/A")
        
        if lang_code == "hi":
            response += f"{i}. {product}\n   मात्रा: {qty} | कुल: ₹{total}\n   स्थिति: {status} | दिनांक: {date}\n\n"
        elif lang_code == "mr":
            response += f"{i}. {product}\n   प्रमाण: {qty} | एकूण: ₹{total}\n   स्थिती: {status} | तारीख: {date}\n\n"
        else:
            response += f"{i}. {product}\n   Qty: {qty} | Total: ₹{total}\n   Status: {status} | Date: {date}\n\n"
    
    if len(orders) > 5:
        remaining = len(orders) - 5
        if lang_code == "hi":
            response += f"... और {remaining} और ऑर्डर।"
        elif lang_code == "mr":
            response += f"... आणखी {remaining} ऑर्डर."
        else:
            response += f"... and {remaining} more orders."
    
    return {"text": response, "intent": "ORDER_HISTORY"}

def handle_refill_reminders(patient_id: str, language: str = "English"):
    """Handle refill reminders intent."""
    orders = get_patient_orders_direct(patient_id)
    lang_code = get_lang_code(language)
    
    if not orders:
        if lang_code == "hi":
            return {"text": "आपके पास कोई ऑर्डर नहीं है जिसके लिए रिफिल की आवश्यकता हो। क्या आप कोई दवा ऑर्डर करना चाहेंगे?", "intent": "REFILL_REMINDERS"}
        elif lang_code == "mr":
            return {"text": "तुमच्याकडे कोणताही ऑर्डर नाही ज्यासाठी रिफिल आवश्यक आहे. तुम्हाला औषध ऑर्डर करायचे आहे का?", "intent": "REFILL_REMINDERS"}
        else:
            return {"text": "You don't have any orders that need refilling. Would you like to order some medicines?", "intent": "REFILL_REMINDERS"}
    
    refill_items = []
    for order in orders:
        order_date = order.get("order_date")
        if order_date:
            try:
                if isinstance(order_date, str):
                    order_date = datetime.fromisoformat(order_date.replace("Z", "+00:00"))
                
                days_since = (datetime.now() - order_date).days
                days_until_refill = 30 - days_since
                
                if days_until_refill <= 7 and days_until_refill >= 0:
                    refill_items.append({
                        "product": order.get("product_name"),
                        "days_until": days_until_refill
                    })
            except:
                pass
    
    if not refill_items:
        if lang_code == "hi":
            return {"text": "✅ अभी आपको कोई रिफिल की आवश्यकता नहीं है। हम आपको समय पर याद दिलाएंगे!", "intent": "REFILL_REMINDERS"}
        elif lang_code == "mr":
            return {"text": "✅ सध्या तुम्हाला कोणत्याही रिफिलची गरज नाही. आमी तुम्हाला वेळेवर आठवण करू!", "intent": "REFILL_REMINDERS"}
        else:
            return {"text": "✅ You don't have any refills due right now. We'll remind you in time!", "intent": "REFILL_REMINDERS"}
    
    if lang_code == "hi":
        response = "🔔 आपकी आगामी रिफिल:\n\n"
    elif lang_code == "mr":
        response = "🔔 तुमची आगामी रिफिल:\n\n"
    else:
        response = "🔔 Your upcoming refills:\n\n"
    
    for item in refill_items[:5]:
        if lang_code == "hi":
            response += f"• {item['product']} - {item['days_until']} दिनों में\n"
        elif lang_code == "mr":
            response += f"• {item['product']} - {item['days_until']} दिवसांमध्ये\n"
        else:
            response += f"• {item['product']} - in {item['days_until']} days\n"
    
    return {"text": response, "intent": "REFILL_REMINDERS"}

def handle_show_profile(patient_id: str, language: str = "English"):
    """Handle show profile intent."""
    patient = get_patient_direct(patient_id)
    lang_code = get_lang_code(language)
    
    if not patient:
        if lang_code == "hi":
            return {"text": "मुझे आपकी प्रोफाइल नहीं मिली। कृपया अपना ईमेल या फोन नंबर जांचें।", "intent": "SHOW_PROFILE"}
        elif lang_code == "mr":
            return {"text": "मला तुमची प्रोफाइल सापडली नाही. कृपया तुमचा ईमेल किंवा फोन नंबर तपासा.", "intent": "SHOW_PROFILE"}
        else:
            return {"text": "I couldn't find your profile. Please check your email or phone number.", "intent": "SHOW_PROFILE"}
    
    name = patient.get("name", "N/A")
    age = patient.get("age", "N/A")
    gender = patient.get("gender", "N/A")
    phone = patient.get("phone", "N/A")
    email = patient.get("email", "N/A")
    address = patient.get("address", "N/A")
    
    if lang_code == "hi":
        response = f"""👤 आपकी प्रोफाइल:

नाम: {name}
उम्र: {age}
लिंग: {gender}
फोन: {phone}
ईमेल: {email}
पता: {address}

क्या आपको कुछ और चाहिए?"""
    elif lang_code == "mr":
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
    
    return {"text": response, "intent": "SHOW_PROFILE"}

def handle_prescription_upload(language: str = "English"):
    """Handle prescription upload intent."""
    lang_code = get_lang_code(language)
    
    if lang_code == "hi":
        response = """📤 महत्वपूर्ण: आपको अपलोड करने के लिए फ़ोटो/पीडीएफ़ चुनना होगा।

आप निम्नलिखित तरीकों से पर्चा अपलोड कर सकते हैं:
• स्क्रीनशॉट लें
• फोटो कैप्चर करें
• पीडीएफ़ फ़ाइल अटैच करें

कृपया अपना पर्चा अपलोड करें, और मैं दवाइयां निकाल दूंगा।"""
    elif lang_code == "mr":
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
    
    return {"text": response, "intent": "UPLOAD_PRESCRIPTION"}

def handle_greeting(language: str = "English"):
    """Handle greeting intent."""
    lang_code = get_lang_code(language)
    
    if lang_code == "hi":
        response = "नमस्ते! मैं SwasthyaSarthi हूं, आपका फार्मेसी सहायक। मैं आपकी दवाइयां ऑर्डर करने, प्रिस्क्रिप्शन अपलोड करने, और आपके स्वास्थ्य की देखभाल में मदद कर सकता हूं। आपको क्या चाहिए?"
    elif lang_code == "mr":
        response = "नमस्कार! मी SwasthyaSarthi आहे, तुमचा फार्मसी सहायक. मी तुमची औषधे ऑर्डर करण्यात, पावती अपलोड करण्यात आणि तुमच्या आरोग्याची काळजी घेण्यात मदत करू शकतो. तुम्हाला काय हवे आहे?"
    else:
        response = "Hello! I'm SwasthyaSarthi, your pharmacy assistant. I can help you order medicines, upload prescriptions, and manage your health. What would you like to do?"
    
    return {"text": response, "intent": "GREETING"}

def handle_help(language: str = "English"):
    """Handle help intent."""
    lang_code = get_lang_code(language)
    
    if lang_code == "hi":
        response = """मैं आपकी इनमें मदद कर सकता हूं:

🛒 दवाइयां ऑर्डर करें
📋 प्रिस्क्रिप्शन अपलोड करें
📦 अपने ऑर्डर देखें
🔔 रिफिल रिमाइंडर चेक करें
👤 अपनी प्रोफाइल देखें

आपको क्या चाहिए?"""
    elif lang_code == "mr":
        response = """मी तुमची खालील गोष्टींमध्ये मदत करू शकतो:

🛒 औषधे ऑर्डर करा
📋 पावती अपलोड करा
📦 तुमचे ऑर्डर पहा
🔔 रिफिल रिमाइंडर तपासा
👤 तुमची प्रोफाइल पहा

तुम्हाला काय हवे आहे?"""
    else:
        response = """I can help you with:

🛒 Order medicines
📋 Upload prescription
📦 View your orders
🔔 Check refill reminders
👤 View your profile

What would you like to do?"""
    
    return {"text": response, "intent": "HELP"}

def handle_thanks(language: str = "English"):
    """Handle thanks intent."""
    lang_code = get_lang_code(language)
    
    if lang_code == "hi":
        response = "आपका स्वागत है! क्या आपको कुछ और चाहिए?"
    elif lang_code == "mr":
        response = "तुमचे स्वागत आहे! तुम्हाला काहीही हवे आहे का?"
    else:
        response = "You're welcome! Is there anything else you need?"
    
    return {"text": response, "intent": "THANKS"}

def handle_unknown(language: str = "English"):
    """Handle unknown intent."""
    lang_code = get_lang_code(language)
    
    if lang_code == "hi":
        response = "मुझे समझ नहीं आया। क्या आप दवाई ऑर्डर करना चाहेंगे, या कुछ और मदद चाहिए?"
    elif lang_code == "mr":
        response = "मला समजले नाही. तुम्हाला औषध ऑर्डर करायचे आहे का, किंवा काहीही मदत हवी आहे?"
    else:
        response = "I didn't quite get that. Would you like to order some medicine, or is there something else I can help you with?"
    
    return {"text": response, "intent": "UNKNOWN"}

def process_message(message: str, user_id: str = "default", language: str = "English"):
    """
    Process a chat message and return a response.
    Uses rule-based intent detection and direct API calls.
    """
    message_lower = message.lower().strip()
    
    # Show medicines intent
    medicine_keywords = ["show medicines", "list medicines", "available medicines", "what medicines", 
                       "browse medicines", "medicine catalog", "all medicines", "medicine list",
                       "medicines available", "what do you have"]
    if any(kw in message_lower for kw in medicine_keywords):
        return handle_show_medicines(language)
    
    # Order history intent
    order_keywords = ["order history", "my orders", "past orders", "previous orders", 
                     "order list", "my purchases", "order details"]
    if any(kw in message_lower for kw in order_keywords):
        return handle_order_history(user_id, language)
    
    # Refill reminders intent
    refill_keywords = ["refill reminder", "refill alerts", "medicine reminder", "reminder",
                     "refill", "when to refill", "next refill", "refill due", "renew medicine"]
    if any(kw in message_lower for kw in refill_keywords):
        return handle_refill_reminders(user_id, language)
    
    # Profile intent
    profile_keywords = ["my profile", "show profile", "my account", "my details",
                      "profile", "account details", "my information", "my info"]
    if any(kw in message_lower for kw in profile_keywords):
        return handle_show_profile(user_id, language)
    
    # Prescription upload intent
    prescription_keywords = ["upload prescription", "prescription upload", "upload rx", "prescribe",
                          "prescription image", "doctor prescription", "medical prescription"]
    if any(kw in message_lower for kw in prescription_keywords):
        return handle_prescription_upload(language)
    
    # Greeting intent
    greeting_keywords = ["hello", "hi", "hey", "good morning", "good evening", "good night"]
    if any(kw in message_lower for kw in greeting_keywords):
        return handle_greeting(language)
    
    # Help intent
    help_keywords = ["help", "what can you do", "who are you"]
    if any(kw in message_lower for kw in help_keywords):
        return handle_help(language)
    
    # Thanks intent
    thanks_keywords = ["thank", "thanks", "thankyou"]
    if any(kw in message_lower for kw in thanks_keywords):
        return handle_thanks(language)
    
    # Default to unknown
    return handle_unknown(language)
