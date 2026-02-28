"""
Prescription Agent for SwasthyaSarthi.
Extracts and validates medicine names from prescription OCR text.
Uses Ollama LLM for medicine name extraction and dataset matching.

Workflow:
1. Receive OCR text from prescription
2. Use LLM to extract medicine names (with structured prompt)
3. Match extracted names with dataset products
4. Return structured order data with confidence scores

LangSmith tracing included for observability.
"""

import json
import re
from typing import List, Dict, Optional
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.services.dataset_matcher import (
    get_dataset_matcher,
    match_medicine,
    match_medicines,
    DEFAULT_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD
)

# Language-specific prompts
EXTRACTION_PROMPTS = {
    "en": """You are a pharmacy assistant. Extract medicine names from the prescription text below.

Return ONLY a JSON array of medicine names. Do NOT invent medicines.
If no medicines are found, return an empty array [].

Example output:
["Medicine Name 1", "Medicine Name 2"]

Prescription text:
""",
    
    "hi": """आप एक फार्मासिस्ट सहायक हैं। नीचे दी गई पर्चे से दवाओं के नाम निकालें।

केवल JSON array में दवाओं के नाम वापस करें। दवाएँ मत बनाइए।
यदि कोई दवा नहीं मिली, तो खाली array [] वापस करें।

उदाहरण आउटपुट:
["दवा का नाम 1", "दवा का नाम 2"]

पर्चे का टेक्स्ट:
""",
    
    "mr": """आपण एक फार्मसी असिस्टंट आहात. खाली दिलेल्या पदार्थातून औषधांची नावे काढा.

केवल JSON array मध्ये औषधांची नावे परत करा. औषधे शोधू नका.
जर कोणतीही औषधे सापडली नाहीत, तर रिकामा array [] परत करा.

उदाहरण आउटपुट:
["औषध नाव 1", "औषध नाव 2"]

पदार्थ टेक्स्ट:
"""
}

# Response templates for different languages
RESPONSE_TEMPLATES = {
    "en": {
        "success": "I found {count} medicine(s) in your prescription: {medicines}",
        "no_medicines": "I could not find any recognizable medicines in the prescription.",
        "unclear": "I could not clearly read the prescription. Please upload a clearer image.",
        "confirm_order": "Should I place an order for these medicines?",
        "detected": "Detected Medicines:"
    },
    "hi": {
        "success": "मैंने आपके पर्चे में {count} दवा(याँ) पाई: {medicines}",
        "no_medicines": "मैं पर्चे में कोई पहचानने योग्य दवा नहीं पा सका।",
        "unclear": "मैं पर्चे को स्पष्ट रूप से पढ़ नहीं सका। कृपया एक स्पष्ट छवि अपलोड करें।",
        "confirm_order": "क्या मैं इन दवाओं के लिए ऑर्डर दूँ?",
        "detected": "पता चली दवाएँ:"
    },
    "mr": {
        "success": "मी तुमच्या पदार्थात {count} औषधे शोधली: {medicines}",
        "no_medicines": "मी पदार्थात कोणतीही ओळखण्यायोग्य औषधे शोधू शकलो नाही.",
        "unclear": "मी पदार्थ स्पष्टपणे वाचू शकलो नाही. कृपया स्पष्ट चित्र अपलोड करा.",
        "confirm_order": "मी या औषधांसाठी ऑर्डर द्यावा?",
        "detected": "शोधलेली औषधे:"
    }
}


def extract_medicine_names(ocr_text: str, language: str = "en") -> List[str]:
    """
    Extract medicine names from OCR text using LLM.
    
    Args:
        ocr_text: Raw text from OCR
        language: Language of the prescription (en/hi/mr)
    
    Returns:
        List of extracted medicine names
    """
    if not ocr_text or not ocr_text.strip():
        return []
    
    # Get prompt based on language
    prompt_template = EXTRACTION_PROMPTS.get(language, EXTRACTION_PROMPTS["en"])
    full_prompt = prompt_template + ocr_text
    
    # Try to use LLM with tracing
    llm = get_llm()
    
    if llm is None:
        # Fallback: simple keyword extraction
        return _fallback_extraction(ocr_text)
    
    try:
        # Use invoke_with_trace for LangSmith observability
        if is_tracing_enabled():
            response_content = invoke_with_trace(
                f"{full_prompt}\n\nExtract medicine names. Return ONLY JSON array.",
                agent_name="prescription_agent"
            )
        else:
            response = llm.invoke(
                [HumanMessage(content=full_prompt)],
                config=_get_langsmith_config()
            )
            response_content = response.content.strip()
        
        # Parse JSON response
        if response_content:
            # Try to extract JSON array
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                try:
                    medicines = json.loads(json_match.group())
                    if isinstance(medicines, list):
                        # Clean up medicine names
                        return [m.strip() for m in medicines if isinstance(m, str) and m.strip()]
                except json.JSONDecodeError:
                    pass
        
        # Fallback if LLM response is not valid JSON
        return _fallback_extraction(ocr_text)
        
    except Exception as e:
        print(f"[Prescription Agent] Extraction error: {e}")
        return _fallback_extraction(ocr_text)


def _fallback_extraction(ocr_text: str) -> List[str]:
    """
    Fallback extraction using simple pattern matching.
    
    Args:
        ocr_text: Raw OCR text
    
    Returns:
        List of potential medicine names
    """
    # Common medicine patterns
    patterns = [
        r'[A-Z][a-z]+(?:|ine|ol|cin|ide|ate|ium|in|b|ol|x|z|p|mycin|pril|flox|nox|statin|profen)',
        r'(?:Tablets?|Capsules?|Syrup|Spray|Drops|Cream|Ointment|Gel)\s+[A-Z][a-z]+',
    ]
    
    medicines = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        medicines.update([m.strip() for m in matches if len(m.strip()) > 2])
    
    return list(medicines)[:10]  # Limit to 10


def match_with_dataset(medicine_names: List[str], threshold: float = DEFAULT_THRESHOLD) -> List[Dict]:
    """
    Match extracted medicine names with dataset products.
    
    Args:
        medicine_names: List of medicine names from extraction
        threshold: Minimum confidence threshold
    
    Returns:
        List of matched medicines with confidence scores
    """
    matcher = get_dataset_matcher()
    matches = matcher.find_matches(medicine_names, threshold)
    
    return matches


def prescription_agent(state: AgentState) -> AgentState:
    """
    Process prescription: extract medicines and match with dataset.
    Uses LangSmith tracing for full observability.
    
    Args:
        state: Agent state containing prescription data
    
    Returns:
        Updated agent state with detected medicines
    """
    # Initialize agent trace for observability
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    # Get prescription data from state
    ocr_text = state.get("prescription_ocr_text", "")
    user_language = state.get("user_language", "en")
    prescription_image = state.get("prescription_image", None)
    
    # Trace entry
    trace_entry = {
        "agent": "prescription_agent",
        "step": "process_prescription",
        "source": "prescription_image" if prescription_image else "text_input",
        "ocr_text_length": len(ocr_text) if ocr_text else 0
    }
    
    # If no OCR text, return error
    if not ocr_text or not ocr_text.strip():
        state["final_response"] = RESPONSE_TEMPLATES.get(user_language, RESPONSE_TEMPLATES["en"])["unclear"]
        trace_entry["result"] = "no_ocr_text"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Extract medicine names using LLM
    detected_language = state.get("detected_language", "English")
    lang_code = "en" if detected_language == "English" else ("hi" if detected_language == "Hindi" else "mr")
    
    extracted_medicines = extract_medicine_names(ocr_text, lang_code)
    trace_entry["extracted_medicines"] = extracted_medicines
    
    # If no medicines extracted
    if not extracted_medicines:
        state["final_response"] = RESPONSE_TEMPLATES.get(lang_code, RESPONSE_TEMPLATES["en"])["no_medicines"]
        trace_entry["result"] = "no_medicines_found"
        state["agent_trace"].append(trace_entry)
        return state
    
    # Match with dataset
    matched_medicines = match_with_dataset(extracted_medicines)
    trace_entry["matched_medicines"] = matched_medicines
    
    # Separate matched and unmatched medicines
    matched_names = [m["matched_name"] for m in matched_medicines]
    unmatched = [m for m in extracted_medicines if m not in matched_names]
    
    # Build response
    response_key = "success" if matched_medicines else "no_medicines"
    template = RESPONSE_TEMPLATES.get(lang_code, RESPONSE_TEMPLATES["en"])
    
    if matched_medicines:
        medicines_list = ", ".join(matched_names)
        response = template["success"].format(count=len(matched_medicines), medicines=medicines_list)
        response += "\n\n" + template["detected"] + "\n"
        
        for med in matched_medicines:
            confidence_pct = int(med["confidence"] * 100)
            check = "✔" if med["is_high_confidence"] else "○"
            response += f"{check} {med['matched_name']} ({confidence_pct}% match)\n"
        
        response += "\n" + template["confirm_order"]
    else:
        response = template["no_medicines"]
    
    # Store in state for downstream agents
    state["detected_medicines"] = matched_medicines
    state["unmatched_medicines"] = unmatched
    state["prescription_processed"] = True
    state["final_response"] = response
    state["requires_confirmation"] = True
    
    # Build structured order data for confirmed medicines
    if matched_medicines:
        structured_items = []
        for med in matched_medicines:
            product_info = med.get("product_info", {})
            structured_items.append({
                "product_name": med["matched_name"],
                "quantity": 1,
                "unit_price": product_info.get("price", 0) if product_info else 0,
                "confidence": med["confidence"]
            })
        
        state["structured_order_items"] = structured_items
        state["prescription_source"] = True
    
    # Trace result
    trace_entry["result"] = "success" if matched_medicines else "no_matches"
    trace_entry["confidence_scores"] = [m["confidence"] for m in matched_medicines]
    state["agent_trace"].append(trace_entry)
    
    # Add observability metadata
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["agent_name"] = "prescription_agent"
    state["metadata"]["action"] = "extract_and_match_medicines"
    state["metadata"]["source"] = "prescription_image" if prescription_image else "text_input"
    state["metadata"]["ocr_text_length"] = len(ocr_text)
    state["metadata"]["medicines_detected"] = len(matched_medicines)
    
    return state


def process_prescription_direct(ocr_text: str, language: str = "en") -> Dict:
    """
    Process prescription directly without agent state.
    Used for API endpoint.
    
    Args:
        ocr_text: Raw text from OCR
        language: Language code (en/hi/mr)
    
    Returns:
        Dictionary with detected medicines and metadata
    """
    result = {
        "success": False,
        "detected_medicines": [],
        "unmatched_medicines": [],
        "message": "",
        "raw_extracted": [],
        "ocr_confidence": 0.0
    }
    
    if not ocr_text or not ocr_text.strip():
        result["message"] = "No text provided for processing"
        return result
    
    # Extract medicines
    extracted = extract_medicine_names(ocr_text, language)
    result["raw_extracted"] = extracted
    
    if not extracted:
        result["message"] = "No medicines could be extracted from the text"
        return result
    
    # Match with dataset
    matched = match_with_dataset(extracted)
    
    result["detected_medicines"] = [
        {
            "name": m["input_name"],
            "matched_dataset_name": m["matched_name"],
            "confidence": m["confidence"],
            "is_high_confidence": m["is_high_confidence"],
            "product_info": m.get("product_info", {})
        }
        for m in matched
    ]
    
    result["unmatched_medicines"] = [
        m for m in extracted 
        if m not in [med["input_name"] for med in matched]
    ]
    
    result["success"] = len(result["detected_medicines"]) > 0
    result["message"] = f"Found {len(result['detected_medicines'])} medicines" if result["success"] else "No medicines matched with dataset"
    
    return result


# Export
__all__ = [
    'prescription_agent',
    'extract_medicine_names',
    'match_with_dataset',
    'process_prescription_direct',
    'EXTRACTION_PROMPTS',
    'RESPONSE_TEMPLATES'
]
