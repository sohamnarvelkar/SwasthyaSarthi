"""
Pharmacist Agent - Parses user order requests into structured data and provides medicine information.
Uses unified LLM provider with LangSmith observability for traceability.
"""
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from tools.inventory_tool import get_medicine
import json
import re

# Language mapping for responses
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "ml": "Malayalam",
    "gu": "Gujarati"
}

# Human-friendly response templates
INFO_RESPONSES = {
    "en": "Sure! Let me check about {product} for you.",
    "hi": "ज़रूर! मैं {product} के बारे में देखता हूं।",
    "mr": "नक्की! मी {product} बद्दल पाहतो.",
    "bn": "অবশ্যই! আমি {product} সম্পর্কে দেখছি।",
    "ml": "തീര്‍ച്ചയായി! ഞാന്‍ {product} എന്നതിനെക്കുറിച്ച് പരിശോധിക്കാം.",
    "gu": "ખાતર! હું {product} વિશે જોઈશ."
}

def get_language_prompt_suffix(user_language: str) -> str:
    """Get the language-specific instruction for the LLM."""
    lang_name = LANGUAGE_NAMES.get(user_language, "English")
    if lang_name == "English":
        return "Respond in English in a friendly, conversational way."
    return f"Respond in {lang_name} in a friendly, conversational way."

def _is_order_intent(user_text: str) -> bool:
    """Check if the user wants to order medicine or just asking for information."""
    text_lower = user_text.lower()
    
    # Order intent keywords
    order_keywords = [
        "order", "buy", "purchase", "get", "want", "need",
        "place order", "order now", "buy now", "can i get",
        "i want to order", "i want to buy", "please order",
        "i need", "can i have", "give me", "arrange"
    ]
    
    # Information/query intent keywords  
    info_keywords = [
        "information", "info", "details", "tell me about",
        "what is", "what are", "how does", "explain",
        "price", "cost", "availability", "in stock",
        "do you have", "do you have any", "available",
        "prescription", "side effects", "uses", "benefits"
    ]
    
    # Check for order intent first (higher priority)
    for keyword in order_keywords:
        if keyword in text_lower:
            return True
    
    # Check if it's purely informational
    for keyword in info_keywords:
        if keyword in text_lower:
            # If combined with "just", "only", "know", etc. it's info intent
            if "just" in text_lower or "only" in text_lower or "know" in text_lower:
                return False
    
    # If unclear, assume order intent (they might want to buy)
    return True

def _get_info_response(user_language: str, product_name: str) -> str:
    """Get a friendly informational response in the user's language."""
    lang_code = user_language if user_language in INFO_RESPONSES else "en"
    template = INFO_RESPONSES.get(lang_code, INFO_RESPONSES["en"])
    return template.format(product=product_name)

def pharmacist_agent(state: AgentState) -> AgentState:
    """
    Parse the user's conversational request into structured order data OR
    provide medicine information if user is just asking.
    Uses LangSmith tracing to see chain of thoughts in dashboard.
    
    Handles two types of requests:
    1. Order requests: "I want to buy X" -> parse into structured order
    2. Information requests: "Tell me about X" -> provide medicine info
    """
    user_text = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    user_id = state.get("user_id")

    if not user_text:
        state["structured_order"] = {}
        state["is_info_request"] = False
        return state

    # Determine if user wants to order or just asking for info
    is_order = _is_order_intent(user_text)
    state["is_order_request"] = is_order

    # Try to use LLM for parsing with full observability
    llm = get_llm()

    if llm is None:
        # Fallback to rule-based parsing when no LLM is available
        print("[Pharmacist Agent] Using rule-based parsing (no LLM)")
        parsed = _rule_based_parse(user_text, is_order)
        state["structured_order"] = parsed
        return state

    if is_order:
        # Order intent - parse the order
        prompt = f'''You are a pharmacy assistant. Parse this customer's order request and extract structured information.

Customer said: "{user_text}"

Extract the following information:
1. product_name: The exact medicine/product name from our inventory
2. quantity: How many units/packs they want (default to 1 if not specified)
3. dosage: Any dosage instructions mentioned
4. patient_name: Any patient name mentioned
5. notes: Any special instructions

{get_language_prompt_suffix(user_language)}

Return ONLY a JSON object with these exact keys:
{{"product_name": "...", "quantity": 1, "dosage": "...", "patient_name": "...", "notes": "..."}}'''
    else:
        # Info intent - just acknowledge and let safety agent provide details
        prompt = f'''The user is asking for information about a medicine.

Customer said: "{user_text}"

Simply acknowledge their query in a friendly way. Return ONLY a JSON:
{{"acknowledgment": "Your friendly acknowledgment message", "product_name": "the medicine name they asked about"}}'''

    try:
        # Use invoke_with_trace for full LangSmith observability
        response_content = invoke_with_trace(prompt, agent_name="pharmacist")
        
        if response_content is None:
            response = llm.invoke(
                [SystemMessage(content=prompt)] if 'SystemMessage' in dir() else [HumanMessage(content=prompt)],
                config=_get_langsmith_config()
            )
            response_content = response.content.strip()

        content = response_content.strip()

        # Try to extract JSON from response
        try:
            parsed = json.loads(content)
        except:
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {"product_name": content, "quantity": 1, "dosage": "", "patient_name": "", "notes": ""}

        if not isinstance(parsed, dict):
            parsed = {"product_name": str(parsed), "quantity": 1, "dosage": "", "patient_name": "", "notes": ""}

        if is_order:
            # Clean up the product name
            if parsed.get("product_name"):
                product_name = parsed["product_name"].strip()
                parsed["product_name"] = _match_medicine_name(product_name)

            state["structured_order"] = {
                "product_name": parsed.get("product_name", ""),
                "quantity": parsed.get("quantity", 1),
                "dosage": parsed.get("dosage", ""),
                "patient_name": parsed.get("patient_name", ""),
                "notes": parsed.get("notes", "")
            }
            print(f"[Pharmacist Agent] Parsed order: {state['structured_order']}")
        else:
            # Info request - set up response
            product_name = parsed.get("product_name", "")
            if product_name:
                matched_name = _match_medicine_name(product_name)
                state["info_product"] = matched_name
                state["info_response"] = _get_info_response(user_language, matched_name)
            else:
                state["info_product"] = _rule_based_parse(user_text, True).get("product_name", "")
                state["info_response"] = _get_info_response(user_language, state["info_product"])
            print(f"[Pharmacist Agent] Info request for: {state['info_product']}")

    except Exception as e:
        print(f"Pharmacist agent error: {e}")
        parsed = _rule_based_parse(user_text, is_order)
        state["structured_order"] = parsed

    return state


def _rule_based_parse(user_text: str, is_order: bool = True) -> dict:
    """Rule-based parsing fallback when no LLM is available."""
    text_lower = user_text.lower()

    # Find quantity
    quantity = 1
    quantity_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    for word, num in quantity_words.items():
        if word in text_lower:
            quantity = num
            break

    digit_match = re.search(r'(\d+)', user_text)
    if digit_match:
        quantity = int(digit_match.group(1))

    product_name = _match_medicine_name(text_lower)

    return {
        "product_name": product_name,
        "quantity": quantity,
        "dosage": "",
        "patient_name": "",
        "notes": ""
    }


def _match_medicine_name(input_name: str) -> str:
    """
    Match user input to actual products in the database.
    Using medicines from data/products-export.xlsx
    """
    # Medicine mappings - mapped to actual products from dataset
    medicine_mappings = {
        # Pain/Headache/Fever
        "pain": "Nurofen 200 mg Schmelztabletten Lemon",
        "pain killer": "Nurofen 200 mg Schmelztabletten Lemon",
        "headache": "Nurofen 200 mg Schmelztabletten Lemon",
        "fever": "Paracetamol apodiscounter 500 mg Tabletten",
        "body pain": "Diclo-ratiopharm Schmerzgel",
        "joint pain": "Diclo-ratiopharm Schmerzgel",
        
        # Vitamins & Supplements
        "vitamin": "Centrum Vital+ Mentale Leistung",
        "multivitamin": "Centrum Vital+ Mentale Leistung",
        "vitamin d": "Vigantolvit 2000 I.E. Vitamin D3",
        "vitamin d3": "Vigantolvit 2000 I.E. Vitamin D3",
        "vitamin b": "Vitamin B-Komplex-ratiopharm",
        "b complex": "Vitamin B-Komplex-ratiopharm",
        "b12": "Vitasprint B12 Kapseln",
        
        # Omega-3
        "omega": "NORSAN Omega-3 Total",
        "omega-3": "NORSAN Omega-3 Total",
        "fish oil": "NORSAN Omega-3 Total",
        
        # Energy
        "energy": "Vitasprint Pro Energie",
        "tired": "Vitasprint Pro Energie",
        "fatigue": "Vitasprint Pro Energie",
        "tiredness": "Vitasprint Pro Energie",
        
        # Allergies
        "allergy": "Cetirizin HEXAL® Tropfen bei Allergien",
        "allergic": "Cetirizin HEXAL® Tropfen bei Allergien",
        "allergies": "Cetirizin HEXAL® Tropfen bei Allergien",
        "hay fever": "Cetirizin HEXAL® Tropfen bei Allergien",
        "sneezing": "Cetirizin HEXAL® Tropfen bei Allergien",
        
        # Eye
        "eye drops": "Vividrin® iso EDO® antiallergische Augentropfen",
        "eye": "Vividrin® iso EDO® antiallergische Augentropfen",
        "allergy eyes": "Vividrin® iso EDO® antiallergische Augentropfen",
        "red eyes": "Livocab® direkt Augentropfen, 0,05 % Augentropfen",
        "itchy eyes": "Vividrin® iso EDO® antiallergische Augentropfen",
        
        # Skin
        "skin": "Bepanthen WUND- UND HEILSALBE, 50 mg/g Salbe",
        "skin cream": "Bepanthen WUND- UND HEILSALBE, 50 mg/g Salbe",
        "dry skin": "Eucerin UreaRepair PLUS Lotion 10%",
        "wound": "Bepanthen WUND- UND HEILSALBE, 50 mg/g Salbe",
        "wounds": "Bepanthen WUND- UND HEILSALBE, 50 mg/g Salbe",
        "rash": "FeniHydrocort Creme 0,25 %",
        
        # Digestion
        "digestion": "Iberogast® Classic, Flüssigkeit zum Einnehmen",
        "stomach": "Iberogast® Classic, Flüssigkeit zum Einnehmen",
        "bloating": "Kijimea Reizdarm PRO",
        "ibs": "Kijimea Reizdarm PRO",
        "irritable bowel": "Kijimea Reizdarm PRO",
        
        # Constipation
        "constipation": "DulcoLax® Dragées, 5 mg magensaftresistente Tabletten",
        "constipated": "DulcoLax® Dragées, 5 mg magensaftresistente Tabletten",
        
        # Diarrhea
        "diarrhea": "Loperamid akut - 1 A Pharma®, 2 mg Hartkapseln",
        "loose motion": "Loperamid akut - 1 A Pharma®, 2 mg Hartkapseln",
        
        # Urinary
        "urinary": "Cystinol akut®",
        "uti": "Cystinol akut®",
        "bladder": "Aqualibra 80 mg/90 mg/180 mg Filmtabletten",
        
        # Probiotics
        "probiotic": "proBIO 6 Probiotik Kapseln APOMIA",
        "probiotics": "proBIO 6 Probiotik Kapseln APOMIA",
        "gut health": "MULTILAC Darmsynbiotikum",
        
        # Magnesium
        "magnesium": "Magnesium Verla® N Dragées",
        
        # Hair
        "hair loss": "Minoxidil BIO-H-TIN-Pharma 20 mg/ml Spray zur Anwendung auf der Haut",
        "hair": "Minoxidil BIO-H-TIN-Pharma 20 mg/ml Spray zur Anwendung auf der Haut",
        
        # Sleep
        "sleep": "Calmvalera Hevert Tropfen",
        "insomnia": "Calmvalera Hevert Tropfen",
        "sleeping": "Calmvalera Hevert Tropfen",
        "sleep problem": "Calmvalera Hevert Tropfen",
        
        # Cold/Cough
        "cold": "Mucosolvan 1 mal täglich Retardkapseln",
        "cough": "Mucosolvan 1 mal täglich Retardkapseln",
        "flu": "Mucosolvan 1 mal täglich Retardkapseln",
        "congestion": "Mucosolvan 1 mal täglich Retardkapseln",
        
        # Heart/Blood Pressure
        "blood pressure": "Ramipril - 1 A Pharma® 10 mg Tabletten",
        "heart": "Ramipril - 1 A Pharma® 10 mg Tabletten",
        
        # Prostate
        "prostate": "Prostata Men Kapseln",
        "prostatic": "Prostata Men Kapseln",
        
        # Bone/Joint
        "bone": "Calcium Verla® N Dragées",
        "calcium": "Calcium Verla® N Dragées",
        "joint": "Diclo-ratiopharm Schmerzgel",
        
        # Women's health
        "women": "GRANU FINK® femina",
        "feminine": "GRANU FINK® femina",
        
        # Intimate health
        "intimate": "Natural Intimate Creme",
        
        # Baby
        "baby": "frida baby FlakeFixer",
        "infant": "frida baby FlakeFixer",
    }

    input_lower = input_name.lower().strip()

    # Direct match
    if input_lower in medicine_mappings:
        return medicine_mappings[input_lower]

    # Partial match
    for key, value in medicine_mappings.items():
        if key in input_lower or input_lower in key:
            return value

    # Return original if no match
    return input_name
