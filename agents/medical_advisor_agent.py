"""
Medical Advisor Agent - Handles symptoms, diseases, and health questions.
Provides safe, dataset-grounded medical information using Ollama.

IMPORTANT: This agent does NOT diagnose - it explains possible conditions safely.
"""
from agents.llm_provider import get_llm, invoke_with_trace, is_tracing_enabled, _get_langsmith_config
from agents.state_schema import AgentState
from agents.conversation_memory import store_symptoms, get_session
from agents.prompt_templates import format_medical_advisor_prompt
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re


# Symptom to common condition mappings (safe, general knowledge)
SYMPTOM_CONDITIONS = {
    "fever": ["common flu", "viral infection", "body fighting infection"],
    "cough": ["common cold", "respiratory infection", "throat irritation"],
    "cold": ["common cold", "viral upper respiratory infection"],
    "headache": ["tension", "stress", "dehydration", "common migraine"],
    "stomach pain": ["indigestion", "gas", "food intolerance"],
    "vomiting": ["food poisoning", "stomach flu", "motion sickness"],
    "diarrhea": ["food intolerance", "stomach infection", "dietary change"],
    "allergy": ["allergic reaction", "seasonal allergies", "food allergy"],
    "tired": ["general fatigue", "lack of sleep", "stress"],
    "weak": ["general weakness", "nutritional deficiency", "illness recovery"],
    "body ache": ["muscle strain", "flu symptoms", "overexertion"],
    "sore throat": ["throat infection", "common cold", "tonsillitis"],
    "runny nose": ["common cold", "allergic rhinitis", "sinusitis"],
    "nausea": ["indigestion", "food poisoning", "pregnancy", "motion sickness"],
    "dizziness": ["low blood sugar", "dehydration", "inner ear issue"],
    "chest pain": ["heartburn", "muscle strain", "anxiety"],
    "breathing difficulty": ["asthma", "allergic reaction", "anxiety"],
}

# Medical advisor system prompt (Ollama optimized for safety)
# Now imported from prompt_templates for consistency
MEDICAL_ADVISOR_SYSTEM_PROMPT = """You are a healthcare assistant.

IMPORTANT RULES:
1. NEVER diagnose - always say "may indicate" or "commonly associated with"
2. NEVER prescribe - recommend seeing a doctor
3. Use safe, general medical knowledge
4. Keep responses short and helpful
5. Consider the user's language for response

User will describe symptoms. Your job is to:
1. Identify symptoms clearly
2. Explain possible common conditions safely
3. Give general health advice
4. Recommend seeing a doctor if serious

Always use phrases like:
- "may indicate"
- "commonly associated with"  
- "could be"
- "please consult a doctor"

Return JSON format:
{
  "symptoms": ["symptom1", "symptom2"],
  "possible_conditions": ["condition1", "condition2"],
  "advice": "general advice string"
}"""



def _extract_json_from_response(response: str) -> dict:
    """Extract JSON from LLM response."""
    response = response.strip()
    
    # Try direct JSON parse
    try:
        data = json.loads(response)
        return data
    except:
        pass
    
    # Try to find JSON in response
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Return fallback
    return {
        "symptoms": [],
        "possible_conditions": [],
        "advice": "Please consult a doctor for proper diagnosis."
    }


def _rule_based_symptom_analysis(user_input: str) -> dict:
    """Rule-based symptom analysis fallback."""
    text_lower = user_input.lower()
    symptoms = []
    conditions = []
    
    # Match symptoms from input
    for symptom, possible_conds in SYMPTOM_CONDITIONS.items():
        if symptom in text_lower:
            symptoms.append(symptom)
            conditions.extend(possible_conds)
    
    # Remove duplicates
    conditions = list(set(conditions))
    
    advice = "Please consult a doctor if symptoms persist. Rest and stay hydrated."
    
    return {
        "symptoms": symptoms,
        "possible_conditions": conditions[:3],  # Limit to 3
        "advice": advice
    }


def medical_advisor_agent(state: AgentState) -> AgentState:
    """
    Analyze user symptoms and provide safe medical information.
    
    Flow:
    1. Get user input (symptoms)
    2. Use LLM for analysis (or rule-based fallback)
    3. Store symptoms in conversation memory
    4. Return safe, helpful response
    """
    # Initialize trace
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    user_id = state.get("user_id", "default")
    session_id = state.get("session_id", "default")
    
    # Trace entry with observability metadata
    trace_entry = {
        "agent": "medical_advisor_agent",
        "agent_name": "medical_advisor_agent",
        "action": "analyze_symptoms",
        "step": "analyze_symptoms",
        "user_input": user_input[:50],
        "language": user_language
    }
    
    # Get LLM for analysis
    llm = get_llm()
    
    if llm is None or not user_input.strip():
        # Rule-based fallback
        analysis = _rule_based_symptom_analysis(user_input)
        trace_entry["analysis"] = analysis
        trace_entry["method"] = "rule_based"
        trace_entry["symptoms_found"] = len(analysis.get("symptoms", []))
        print(f"[Medical Advisor] Rule-based analysis: {analysis['symptoms']}")
    else:
        # Use LLM for analysis with Ollama-optimized prompt
        try:
            # Use formatted prompt from templates
            prompt = format_medical_advisor_prompt(user_input, user_language)
            
            response = llm.invoke(
                [HumanMessage(content=prompt)],
                config=_get_langsmith_config()
            )
            
            analysis = _extract_json_from_response(response.content)
            trace_entry["analysis"] = analysis
            trace_entry["method"] = "llm"
            trace_entry["llm_response"] = response.content[:200]
            trace_entry["symptoms_found"] = len(analysis.get("symptoms", []))
            trace_entry["language"] = user_language
            print(f"[Medical Advisor] LLM analysis: {analysis.get('symptoms', [])}")
            
        except Exception as e:
            print(f"[Medical Advisor] LLM error: {e}")
            analysis = _rule_based_symptom_analysis(user_input)
            trace_entry["analysis"] = analysis
            trace_entry["method"] = "fallback"
            trace_entry["symptoms_found"] = len(analysis.get("symptoms", []))

    
    # Store in conversation memory
    store_symptoms(
        user_id=user_id,
        session_id=session_id,
        symptoms=analysis.get("symptoms", []),
        conditions=analysis.get("possible_conditions", [])
    )
    
    # Update state
    state["identified_symptoms"] = analysis.get("symptoms", [])
    state["possible_conditions"] = analysis.get("possible_conditions", [])
    state["medical_advice"] = analysis.get("advice", "")
    
    # Generate response based on language
    response = _generate_symptom_response(analysis, user_language)
    state["final_response"] = response
    
    # Add observability metadata for LangSmith
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["agent_name"] = "medical_advisor_agent"
    state["metadata"]["action"] = "symptom_analysis"
    state["metadata"]["medical_advisor"] = "completed"
    state["metadata"]["symptoms_identified"] = len(analysis.get("symptoms", []))
    state["metadata"]["language"] = user_language
    
    state["agent_trace"].append(trace_entry)
    
    return state



def _generate_symptom_response(analysis: dict, language: str) -> str:
    """Generate symptom response in user's language."""
    symptoms = analysis.get("symptoms", [])
    conditions = analysis.get("possible_conditions", [])
    advice = analysis.get("advice", "")
    
    if not symptoms:
        # No symptoms detected
        responses = {
            "en": "I couldn't identify specific symptoms. Could you please describe how you're feeling?",
            "hi": "मुझे विशिष्ट लक्षण पहचानने में कठिनाई हुई। कृपया बताएं आप कैसा महसूस कर रहे हैं?",
            "mr": "मला विशिष्ट लक्षणे ओळखता आली नाही. कृपया सांगा तुम्हाला काय वाटते?",
            "bn": "আমি নির্দিষ্ট লক্ষণ চিহ্নিত করতে পারিনি। অনুগ্রহ করে বলুন আপনি কেমন অনুভব করছেন?",
            "gu": "મને વિશિષ્ટ લક્ષણો ઓળખવામાં આવ્યા નથી. કૃપા કરીને જણાવો તમે કેવી રીતે અનુભવો છો?"
        }
        return responses.get(language, responses["en"])
    
    # Build response
    symptom_list = ", ".join(symptoms)
    
    if conditions:
        condition_list = ", ".join(conditions[:3])
    else:
        condition_list = "various common conditions"
    
    # Generate response per language
    responses = {
        "en": f"""Based on what you've described ({symptom_list}), this may indicate {condition_list}.

{advice}

Would you like me to suggest medicines from our database that might help?""",
        
        "hi": f"""जो आपने बताया है ({symptom_list}), यह {condition_list} हो सकता है।

{advice}

क्या आप हमारे डेटाबेस से दवाओं के बारे में जानना चाहेंगे?""",
        
        "mr": f"""तुम्ही वर्णन केलेल्या ({symptom_list}) वरून, हे {condition_list} असू शकते.

{advice}

तुम्हाला आमच्या डेटाबेसमधून औषधे सुचवायची आहे?""",
        
        "bn": f"""আপনি যা বর্ণনা করেছেন ({symptom_list}), এটি {condition_list} নির্দেশ করতে পারে।

{advice}

আমি কি আমাদের ডেটাবেস থেকে ওষুধ প্রস্তাব করব?""",
        
        "gu": f"""તમારી વર્ણના ({symptom_list}) પરથી, આ {condition_list} હોઈ શકે છે.

{advice}

શું તમને અમારા ડેટાબેસમાંથી દવાઓ સુચવવી છે?"""
    }
    
    return responses.get(language, responses["en"])
