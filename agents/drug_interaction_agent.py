"""
Drug Interaction Agent - Checks for potential drug interactions with patient's existing medicines.
Uses patient's order history to identify current medications and checks against new orders.

Demo: "SwasthyaSarthi doesn't just check stock. It checks patient safety."
"""
import json
import os
from typing import List, Dict, Optional
from agents.state_schema import AgentState
from tools.patient_tool import get_patient_orders, get_patient
from tools.history_tool import load_history
from difflib import SequenceMatcher

# Load drug interactions database
def _load_drug_interactions() -> dict:
    """Load the drug interactions database from JSON file."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    interactions_path = os.path.join(base_path, "data", "drug_interactions.json")
    
    try:
        with open(interactions_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Drug Interaction Agent] Warning: Could not load interactions database: {e}")
        return {"interactions": [], "categories": {}}

# Medicine name mappings for matching
MEDICINE_ALIASES = {
    # Pain relievers
    "nurofen": "Ibuprofen",
    "ibuprofen": "Ibuprofen",
    "advil": "Ibuprofen",
    "motrin": "Ibuprofen",
    "paracetamol": "Paracetamol",
    "acetaminophen": "Paracetamol",
    "tylenol": "Paracetamol",
    "aspirin": "Aspirin",
    "bayer": "Aspirin",
    "diclofenac": "Diclofenac",
    
    # Blood thinners
    "warfarin": "Warfarin",
    "coumadin": "Warfarin",
    
    # Heart medications
    "digoxin": "Digoxin",
    "lanoxin": "Digoxin",
    "verapamil": "Verapamil",
    "calan": "Verapamil",
    "amiodarone": "Amiodarone",
    "cordarone": "Amiodarone",
    "beta-blockers": "Beta-blockers",
    "metoprolol": "Beta-blockers",
    "atenolol": "Beta-blockers",
    "ace inhibitors": "ACE inhibitors",
    "lisinopril": "ACE inhibitors",
    "enalapril": "ACE inhibitors",
    
    # Antibiotics
    "ciprofloxacin": "Ciprofloxacin",
    "cipro": "Ciprofloxacin",
    
    # Asthma
    "theophylline": "Theophylline",
    
    # Mood stabilizers
    "lithium": "Lithium",
    
    # Antidepressants
    "ssri": "SSRI antidepressants",
    "prozac": "SSRI antidepressants",
    "zoloft": "SSRI antidepressants",
    
    # Cholesterol
    "simvastatin": "Simvastatin",
    "zocor": "Simvastatin",
    "lipitor": "Simvastatin",
}


def _normalize_medicine_name(name: str) -> str:
    """Normalize medicine name to standard drug name."""
    name_lower = name.lower().strip()
    
    # Check direct aliases first
    for alias, standard in MEDICINE_ALIASES.items():
        if alias in name_lower:
            return standard
    
    # Try to find a match in categories
    interactions_data = _load_drug_interactions()
    categories = interactions_data.get("categories", {})
    
    for category, drugs in categories.items():
        for drug in drugs:
            if drug.lower() in name_lower:
                return drug
    
    # Return original if no match
    return name


def _calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def _get_patient_current_medications(patient_id: str) -> List[str]:
    """
    Get patient's current medications from their order history.
    Returns list of medicine names the patient has ordered.
    """
    medications = []
    
    try:
        # Try to get from database first
        orders = get_patient_orders(patient_id)
        
        if orders:
            for order in orders:
                med_name = order.get("product_name", "")
                if med_name:
                    medications.append(med_name)
        
        # Also check from Excel history
        history_df = load_history()
        
        # Filter for this patient
        patient_history = history_df[history_df["Patient ID"] == patient_id]
        
        if not patient_history.empty:
            # Get recent orders (last 90 days)
            recent_date = pd.Timestamp.now() - pd.Timedelta(days=90)
            recent_orders = patient_history[patient_history["Purchase Date"] >= recent_date]
            
            for _, row in recent_orders.iterrows():
                med = row.get("Product Name", "")
                if med and med not in medications:
                    medications.append(med)
    
    except Exception as e:
        print(f"[Drug Interaction Agent] Error getting patient history: {e}")
    
    return medications


def _check_interaction(new_drug: str, existing_drugs: List[str]) -> Optional[Dict]:
    """
    Check if a new drug has interactions with any existing medications.
    Returns interaction details if found, None otherwise.
    """
    new_drug_normalized = _normalize_medicine_name(new_drug)
    interactions_data = _load_drug_interactions()
    interactions = interactions_data.get("interactions", [])
    
    for existing_drug in existing_drugs:
        existing_normalized = _normalize_medicine_name(existing_drug)
        
        # Check for direct interactions
        for interaction in interactions:
            drug1 = interaction.get("drug1", "").lower()
            drug2 = interaction.get("drug2", "").lower()
            
            new_lower = new_drug_normalized.lower()
            existing_lower = existing_normalized.lower()
            
            # Check both directions
            if (new_lower == drug1 and existing_lower == drug2) or \
               (new_lower == drug2 and existing_lower == drug1):
                return {
                    "existing_drug": existing_normalized,
                    "new_drug": new_drug_normalized,
                    "severity": interaction.get("severity", "unknown"),
                    "description": interaction.get("description", ""),
                    "recommendation": interaction.get("recommendation", "")
                }
        
        # Also check similarity for partial matches
        similarity = _calculate_similarity(new_drug_normalized, existing_normalized)
        if similarity > 0.7:  # 70% similar
            for interaction in interactions:
                drug1 = interaction.get("drug1", "").lower()
                drug2 = interaction.get("drug2", "").lower()
                
                new_lower = new_drug_normalized.lower()
                existing_lower = existing_normalized.lower()
                
                if (new_lower == drug1 and existing_lower == drug2) or \
                   (new_lower == drug2 and existing_lower == drug1):
                    return {
                        "existing_drug": existing_normalized,
                        "new_drug": new_drug_normalized,
                        "severity": interaction.get("severity", "unknown"),
                        "description": interaction.get("description", ""),
                        "recommendation": interaction.get("recommendation", "")
                    }
    
    return None


def _create_interaction_warning(interaction: Dict, user_language: str = "en") -> str:
    """Create a user-friendly warning message about the drug interaction."""
    severity_emoji = {
        "severe": "🚨",
        "moderate": "⚠️",
        "mild": "ℹ️"
    }
    
    severity_text = {
        "severe": "SEVERE INTERACTION",
        "moderate": "MODERATE INTERACTION",
        "mild": "MILD INTERACTION"
    }
    
    emoji = severity_emoji.get(interaction.get("severity", "moderate"), "⚠️")
    severity = severity_text.get(interaction.get("severity", "moderate"), "INTERACTION")
    
    messages = {
        "en": f"""
{emoji} **DRUG SAFETY ALERT - {severity}**

You are currently taking: **{interaction['existing_drug']}**

The medicine you're trying to order: **{interaction['new_drug']}**

⚕️ **Warning:** {interaction['description']}

💡 **Recommendation:** {interaction['recommendation']}

Please consult your doctor or pharmacist before proceeding with this order.
""",
        "hi": f"""
{emoji} **दवा सुरक्षा अलर्ट - {severity}**

आप वर्तमान में ले रहे हैं: **{interaction['existing_drug']}**

आप जो दवा ऑर्डर करना चाह रहे हैं: **{interaction['new_drug']}**

⚕️ **चेतावनी:** {interaction['description']}

💡 **सिफारिश:** {interaction['recommendation']}

कृपया इस ऑर्डर से पहले अपने डॉक्टर से सलाह लें।
""",
        "mr": f"""
{emoji} **औषध सुरक्षा अलर्ट - {severity}**

तुम्हाला सध्या घेत आहे: **{interaction['existing_drug']}**

तुम्ही ऑर्डर करू इच्छिता: **{interaction['new_drug']}**

⚕️ **इशारा:** {interaction['description']}

💡 **शिफारस:** {interaction['recommendation']}

कृपया या ऑर्डरपूर्वी आपल्या डॉक्टरांना विचारा.
"""
    }
    
    return messages.get(user_language, messages["en"])


def drug_interaction_agent(state: AgentState) -> AgentState:
    """
    Check for potential drug interactions when a patient places a new order.
    Uses patient order history to identify current medications and warns about conflicts.
    
    Demo Line: "SwasthyaSarthi doesn't just check stock. It checks patient safety."
    """
    # Initialize trace
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    patient_id = state.get("user_id", "PAT001")
    user_language = state.get("user_language", "en")
    
    # Get the ordered product
    order = state.get("structured_order", {})
    new_product = order.get("product_name", "")
    
    # Check if this is an order request
    is_order_request = state.get("is_order_request", True)
    
    # Trace entry
    trace_entry = {
        "agent": "drug_interaction_agent",
        "step": "check_interactions",
        "patient_id": patient_id,
        "new_product": new_product,
        "is_order_request": is_order_request
    }
    
    # Only check interactions for order requests
    if not is_order_request or not new_product:
        trace_entry["result"] = "skipped_not_order"
        state["agent_trace"].append(trace_entry)
        return state
    
    try:
        # Get patient's current medications
        current_meds = _get_patient_current_medications(patient_id)
        
        trace_entry["current_medications"] = current_meds
        
        if not current_meds:
            print(f"[Drug Interaction Agent] No current medications found for patient {patient_id}")
            trace_entry["result"] = "no_history"
            state["agent_trace"].append(trace_entry)
            return state
        
        print(f"[Drug Interaction Agent] Checking interactions for {new_product} against {len(current_meds)} current medications")
        
        # Check for interactions
        interaction = _check_interaction(new_product, current_meds)
        
        if interaction:
            print(f"[Drug Interaction Agent] ⚠️ INTERACTION DETECTED: {interaction['severity']} - {interaction['existing_drug']} + {interaction['new_drug']}")
            
            # Create warning message
            warning_message = _create_interaction_warning(interaction, user_language)
            
            # Update state with interaction warning
            state["drug_interaction_warning"] = {
                "detected": True,
                "severity": interaction["severity"],
                "existing_drug": interaction["existing_drug"],
                "new_drug": interaction["new_drug"],
                "description": interaction["description"],
                "recommendation": interaction["recommendation"],
                "warning_message": warning_message
            }
            
            # Block the order by updating safety result
            state["safety_result"] = {
                "approved": False,
                "reason": "drug_interaction",
                "interaction_details": interaction
            }
            
            # Update final response with warning
            state["final_response"] = warning_message + "\n\nYour safety is our priority. Please consult your healthcare provider."
            
            trace_entry["result"] = "interaction_detected"
            trace_entry["severity"] = interaction["severity"]
            trace_entry["interaction"] = interaction
        else:
            print(f"[Drug Interaction Agent] No interactions found for {new_product}")
            state["drug_interaction_warning"] = {"detected": False}
            trace_entry["result"] = "no_interaction"
    
    except Exception as e:
        print(f"[Drug Interaction Agent] Error: {e}")
        trace_entry["result"] = "error"
        trace_entry["error"] = str(e)
        # Don't block order on error, just log it
    
    state["agent_trace"].append(trace_entry)
    return state


# Import pandas for date handling
import pandas as pd
