from tools.refill_tool import check_refills
from tools.patient_tool import get_patient
from agents.state_schema import AgentState
import requests
API_URL = "http://localhost:8000"

def refill_trigger_agent(state: AgentState) -> AgentState:
    """
    Check for medicines that need refilling and prepare proactive alerts.
    This agent runs in proactive mode to identify patients who need refills.
    """
    try:
        # Check for refills
        result = check_refills(days_ahead=3)
        alerts = result.get("alerts", [])
        
        # Prepare proactive messages
        proactive_messages = []
        
        for alert in alerts:
            patient = get_patient(alert["patient_id"])
            lang = patient.get("language", "en") if patient else "en"
            
            # Generate proactive message based on language
            if lang == "hi":
                message = f"नमस्ते {alert['patient_name']}! आपकी दवा {alert['product_name']} जल्द खत्म होने वाली है। क्या आप एक नया ऑर्डर देना चाहेंगे?"
            elif lang == "mr":
                message = f"नमस्कार {alert['patient_name']}! तुमची गोळी {alert['product_name']} लवकर संपणार आहे. तुम्हाला नवीन ऑर्डर घ्यायचा आहे का?"
            elif lang == "bn":
                message = f"নমস্কার {alert['patient_name']}! আপনার ওষুধ {alert['product_name']} শীঘ্রই শেষ হয়ে যাবে। আপনি কি নতুন অর্ডার দিতে চান?"
            elif lang == "ml":
                message = f"നമസ്കാരം {alert['patient_name']}! നിങ്ങളുടെ മരുന്ന് {alert['product_name']} വേഗത്തിൽ തീരാനുണ്ട്. നിങ്ങൾക്ക് പുതിയ ഓഡർ വേണമോ?"
            elif lang == "gu":
                message = f"નમસ્તે {alert['patient_name']}! તમારી દવા {alert['product_name']} જલ્દી સમાપ્ત થવા જઈ રહી છે. શું તમે નવો ઓર્ડર આપવા માંગો છો?"
            else:
                message = f"Hello {alert['patient_name']}! Your medicine {alert['product_name']} will need refilling soon. Would you like to place a new order?"
            
            proactive_messages.append({
                "patient_id": alert["patient_id"],
                "patient_name": alert["patient_name"],
                "phone": alert.get("patient_phone", ""),
                "email": alert.get("patient_email", ""),
                "product_name": alert["product_name"],
                "days_until_refill": alert["days_until_refill"],
                "message": message,
                "language": lang
            })
        
        state["refill_alerts"] = proactive_messages
        state["is_proactive"] = True
        
    except Exception as e:
        print(f"Error in refill trigger agent: {e}")
        state["refill_alerts"] = []
        state["is_proactive"] = False
    
    return state


def get_proactive_refill_summary() -> dict:
    """Get a summary of proactive refills for admin view."""
    try:
        result = check_refills(days_ahead=7)
        return {
            "total_alerts": result.get("count", 0),
            "alerts": result.get("alerts", [])
        }
    except Exception as e:
        return {"error": str(e), "total_alerts": 0, "alerts": []}
