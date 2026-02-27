"""
Recommendation Agent - Dataset-grounded medicine recommendations.
Recommends medicines ONLY from products-export.xlsx based on symptoms.
Uses string similarity and keyword matching for accurate results.
"""
from agents.llm_provider import get_llm, _get_langsmith_config
from agents.state_schema import AgentState
from agents.conversation_memory import store_recommendations, get_session
from agents.prompt_templates import format_recommendation_prompt, format_dataset_search_prompt
from langchain_core.messages import HumanMessage
import pandas as pd
import os
import json

# Cache for medicines dataset
_medicines_cache = None


def load_medicines_dataset():
    """
    Load medicines from products-export.xlsx.
    Returns list of medicine dicts with name, description, price, stock info.
    """
    global _medicines_cache
    
    if _medicines_cache is not None:
        return _medicines_cache
    
    try:
        # Try different paths
        paths = [
            "data/products-export.xlsx",
            "../data/products-export.xlsx",
            os.path.join(os.path.dirname(__file__), "..", "data", "products-export.xlsx")
        ]
        
        df = None
        for path in paths:
            try:
                df = pd.read_excel(path)
                break
            except:
                continue
        
        if df is None:
            print("[Recommendation Agent] Could not load products-export.xlsx")
            return []
        
        # Extract relevant columns
        medicines = []
        for _, row in df.iterrows():
            # Try to extract medicine info from columns
            name = str(row.get("name", row.get("Product Name", row.get("product_name", ""))))
            description = str(row.get("description", row.get("Description", "")))
            price = row.get("price", row.get("Price", 0))
            stock = row.get("stock", row.get("Stock", 100))
            pzn = row.get("pzn", row.get("PZN", ""))
            
            if name and name != "nan":
                medicines.append({
                    "name": name,
                    "description": description,
                    "price": float(price) if price else 0,
                    "stock": int(stock) if stock else 100,
                    "pzn": str(pzn)
                })
        
        _medicines_cache = medicines
        print(f"[Recommendation Agent] Loaded {len(medicines)} medicines from dataset")
        return medicines
        
    except Exception as e:
        print(f"[Recommendation Agent] Error loading dataset: {e}")
        return []


def search_medicines_by_symptoms(symptoms: list, medicines: list = None) -> list:
    """
    Search medicines from dataset that match symptoms.
    Uses keyword matching on name and description.
    """
    if medicines is None:
        medicines = load_medicines_dataset()
    
    if not medicines:
        return []
    
    # Build symptom keywords
    symptom_keywords = []
    for symptom in symptoms:
        symptom_keywords.extend(symptom.lower().split())
        # Add common variations
        if symptom.lower() == "fever":
            symptom_keywords.extend(["febrile", "temperature", "pyrexia", "paracetamol", "acetaminophen"])
        elif symptom.lower() == "cough":
            symptom_keywords.extend(["antitussive", "expectorant", "cold", "flu", "respiratory"])
        elif symptom.lower() == "pain":
            symptom_keywords.extend(["analgesic", "painkiller", "relief", "ibuprofen", "diclofenac"])
        elif symptom.lower() == "headache":
            symptom_keywords.extend(["head", "migraine", "pain", "relief"])
        elif symptom.lower() == "cold":
            symptom_keywords.extend(["rhinitis", "nasal", "congestion", "flu", "cough"])
        elif symptom.lower() == "allergy":
            symptom_keywords.extend(["antihistamine", "allergic", "cetirizine", "hay fever"])
        elif symptom.lower() == "vomiting":
            symptom_keywords.extend(["antiemetic", "nausea", "stomach"])
        elif symptom.lower() == "diarrhea":
            symptom_keywords.extend(["antidiarrheal", "loperamide", "stomach"])
        elif symptom.lower() == "stomach pain":
            symptom_keywords.extend(["digestion", "gastric", "antacid", "stomach"])
        elif symptom.lower() == "tired" or symptom.lower() == "fatigue":
            symptom_keywords.extend(["energy", "vitamin", "supplement", "tiredness"])
        elif symptom.lower() == "weak":
            symptom_keywords.extend(["strength", "vitamin", "supplement", "nutrition"])
    
    # Score medicines
    scored = []
    for med in medicines:
        score = 0
        text = f"{med.get('name', '')} {med.get('description', '')}".lower()
        
        for keyword in symptom_keywords:
            if keyword in text:
                score += 1
        
        if score > 0:
            med["match_score"] = score
            scored.append(med)
    
    # Sort by score
    scored.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    return scored[:5]  # Top 5 recommendations


def _get_recommendation_prompt(symptoms: list, medicines: list) -> str:
    """Build prompt for LLM to select best medicines."""
    medicine_list = "\n".join([f"- {m['name']}: {m.get('description', 'N/A')}" for m in medicines[:10]])
    
    prompt = f"""You are a pharmacy assistant. Recommend medicines from this list based on symptoms:

Symptoms: {', '.join(symptoms)}

Available medicines:
{medicine_list}

Select the most appropriate medicines for these symptoms.
Return JSON:
{{"recommended_medicines": [{{"name": "medicine name", "reason": "why suitable"}}]}}"""
    
    return prompt


def recommendation_agent(state: AgentState) -> AgentState:
    """
    Recommend medicines from dataset based on symptoms.
    
    Flow:
    1. Get symptoms from state or conversation memory
    2. Load medicines from dataset
    3. Search for matching medicines
    4. Store recommendations in memory
    5. Return recommendation response
    """
    # Initialize trace
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    # Get symptoms from state or memory
    symptoms = state.get("identified_symptoms", [])
    
    # If no symptoms in state, check memory
    if not symptoms:
        from agents.conversation_memory import get_last_symptoms
        symptoms = get_last_symptoms(user_id, session_id)
    
    # Trace entry with observability metadata
    trace_entry = {
        "agent": "recommendation_agent",
        "agent_name": "recommendation_agent",
        "action": "recommend_medicines",
        "step": "recommend_medicines",
        "symptoms": symptoms,
        "language": user_language
    }
    
    # Load medicines from dataset
    medicines = load_medicines_dataset()
    
    if not medicines:
        state["final_response"] = _get_no_medicines_response(user_language)
        state["recommended_medicines"] = []
        trace_entry["medicines_found"] = 0
        trace_entry["method"] = "no_dataset"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Search for matching medicines
    recommendations = search_medicines_by_symptoms(symptoms, medicines)
    
    trace_entry["medicines_found"] = len(recommendations)
    trace_entry["method"] = "dataset_search"
    
    if not recommendations:
        state["final_response"] = _get_no_match_response(user_language)
        state["recommended_medicines"] = []
    else:
        # Store recommendations in memory
        store_recommendations(user_id, session_id, recommendations)
        
        # Generate response
        response = _generate_recommendation_response(recommendations, user_language)
        state["final_response"] = response
        state["recommended_medicines"] = recommendations
    
    # Add metadata for observability
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["agent_name"] = "recommendation_agent"
    state["metadata"]["action"] = "medicine_recommendation"
    state["metadata"]["recommendation_agent"] = "completed"
    state["metadata"]["medicines_recommended"] = len(recommendations)
    state["metadata"]["language"] = user_language
    
    state["agent_trace"].append(trace_entry)
    
    return state


def _generate_recommendation_response(medicines: list, language: str) -> str:
    """Generate recommendation response in user's language."""
    if not medicines:
        return _get_no_match_response(language)
    
    # Build medicine list
    med_list = []
    for i, med in enumerate(medicines[:5], 1):
        name = med.get("name", "Unknown")
        desc = med.get("description", "")
        price = med.get("price", 0)
        
        med_list.append(f"{i}. **{name}**")
        if desc and desc != "nan":
            med_list.append(f"   - {desc[:100]}")
        if price > 0:
            med_list.append(f"   - Price: ₹{price:.2f}")
        med_list.append("")
    
    meds_text = "\n".join(med_list)
    
    responses = {
        "en": f"""Based on your symptoms, here are medicines from our database that may help:

{meds_text}
Would you like to order any of these? Just say "I want to order [medicine name]".""",
        
        "hi": f"""आपके लक्षणों के आधार पर, यह दवाएं आपकी मदद कर सकती हैं:

{meds_text}
क्या आप इनमें से कोई दवा ऑर्डर करना चाहेंगे? बस कहें "मैं [दवा का नाम] ऑर्डर करना चाहता/चाहती हूं".""",
        
        "mr": f"""तुमच्या लक्षणांवर आधारित, या औषधे तुम्हाला मदद करू शकतात:

{meds_text}
तुम्हाला यापैकी कोणतेही औषध घ्यायचे आहे? फक्त सांगा "मला [औषधाचे नाव] हवे आहे".""",
        
        "bn": f"""আপনার লক্ষণের ভিত্তিতে, এই ওষুধগুলি আপনাকে সাহায্য করতে পারে:

{meds_text}
আপনি কি এগুলির মধ্যে কোনো ওষুধ অর্ডার করতে চান? বলুন "আমি [ওষুধের নাম] অর্ডার করতে চাই".""",
        
        "gu": f"""તમારા લક્ષણોના આધારે, આ દવાઓ તમને મદદ કરી શકે છે:

{meds_text}
શું તમે આમાંથી કોઈ દવા ઓર્ડર કરવા માંગો છો? ફક્ત કહો "હું [દવાનું નામ] ઓર્ડર કરવા માંગું છું"."""
    }
    
    return responses.get(language, responses["en"])


def _get_no_medicines_response(language: str) -> str:
    """Response when no medicines in database."""
    responses = {
        "en": "I'm sorry, I couldn't access the medicine database right now. Please try again later.",
        "hi": "मुझे खेद है, मैं दवा डेटाबेस तक नहीं पहुंच सका। कृपया बाद में पुनः प्रयास करें।",
        "mr": "मला दुख आहे, मी औषध डेटाबेसमध्ये प्रवेश करू शकलो नाही. कृपया नंतर पुन्हा प्रयास करा.",
        "bn": "দুঃখিত, আমি ওষুধের ডেটাবেস অ্যাক্সেস করতে পারিনি। পরে আবার চেষ্টা করুন।",
        "gu": "મને ખેદ છે, હું દવાના ડેટાબેસ સુધી પહોંચી શક્યો નથી. કૃપા કરીને પછી ફરીથી પ્રયત્ન કરો."
    }
    return responses.get(language, responses["en"])


def _get_no_match_response(language: str) -> str:
    """Response when no matching medicines found."""
    responses = {
        "en": "I couldn't find specific medicines in our database for your symptoms. Please consult a doctor for proper guidance.",
        "hi": "मुझे आपके लक्षणों के लिए हमारे डेटाबेस में विशिष्ट दवाएं नहीं मिलीं। कृपया उचित मार्गदर्शन के लिए डॉक्टर से मिलें।",
        "mr": "तुमच्या लक्षणांसाठी आमच्या डेटाबेसमध्ये विशिष्ट औषधे सापडली नाहीत. योग्य मार्गदर्शनासाठी कृपया डॉक्टरांना भेटा.",
        "bn": "আপনার লক্ষণের জন্য আমাদের ডেটাবেসে নির্দিষ্ট ওষুধ খুঁজে পাইনি। সঠিক গাইডেন্সের জন্য অনুগ্রহ করে একজন ডাক্তারের সাথে পরামর্শ করুন।",
        "gu": "તમારા લક્ષણો માટે અમારા ડેટાબેસમાં વિશિષ્ટ દવાઓ મળી નથી. યોગ્ય માર્ગદર્શન માટે કૃપા કરીને ડૉક્ટરને મળો."
    }
    return responses.get(language, responses["en"])
