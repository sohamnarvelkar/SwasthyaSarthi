"""
Pharmacist Agent - Parses user order requests into structured data.
Uses unified LLM provider with LangSmith observability for traceability.
"""
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
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

def get_language_prompt_suffix(user_language: str) -> str:
    """Get the language-specific instruction for the LLM."""
    lang_name = LANGUAGE_NAMES.get(user_language, "English")
    if lang_name == "English":
        return "Respond in English."
    return f"Respond in {lang_name}."

def pharmacist_agent(state: AgentState) -> AgentState:
    """
    Parse the user's conversational request into structured order data.
    Uses LangSmith tracing to see chain of thoughts in dashboard.
    
    Handles messy, human-like dialogue and extracts:
    - product_name: medicine name
    - quantity: number of units
    - dosage: dosage instructions if mentioned
    - patient_id: patient identifier if mentioned
    """
    user_text = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    user_id = state.get("user_id")

    if not user_text:
        state["structured_order"] = {}
        return state

    # Try to use LLM for parsing with full observability
    llm = get_llm()

    if llm is None:
        # Fallback to rule-based parsing when no LLM is available
        print("[Pharmacist Agent] Using rule-based parsing (no LLM)")
        parsed = _rule_based_parse(user_text)
        state["structured_order"] = parsed
        return state

    # Enhanced prompt for better conversational understanding
    # This prompt and its response will be tracked in LangSmith
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

    try:
        # Use invoke_with_trace for full LangSmith observability
        # This will show the chain of thoughts in LangSmith dashboard
        response_content = invoke_with_trace(prompt, agent_name="pharmacist")
        
        if response_content is None:
            # Fallback if tracing fails
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

        # Ensure all keys exist
        if not isinstance(parsed, dict):
            parsed = {"product_name": str(parsed), "quantity": 1, "dosage": "", "patient_name": "", "notes": ""}

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

    except Exception as e:
        print(f"Pharmacist agent error: {e}")
        parsed = _rule_based_parse(user_text)
        state["structured_order"] = parsed

    return state


def _rule_based_parse(user_text: str) -> dict:
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
