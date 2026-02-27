"""
General Chat Agent - Handles greetings and casual conversation.
Provides friendly, conversational responses like ChatGPT.
"""
from agents.llm_provider import get_llm, _get_langsmith_config
from agents.state_schema import AgentState
from agents.prompt_templates import format_general_chat_prompt
from langchain_core.messages import HumanMessage


# Greeting responses by language
GREETING_RESPONSES = {
    "en": [
        "Hello! I'm SwasthyaSarthi, your friendly pharmacy assistant. How can I help you today?",
        "Hi there! I'm here to help with your health and medicine needs. What can I assist you with?",
        "Welcome! I'm your multilingual healthcare assistant. Ask me about medicines, symptoms, or anything health-related!"
    ],
    "hi": [
        "नमस्ते! मैं SwasthyaSarthi हूं, आपका फार्मेसी सहायक। आज मैं आपकी कैसे मदद कर सकता हूं?",
        "नमस्ते! मैं आपके स्वास्थ्य और दवाओं की जरूरतों में मदद के लिए यहां हूं।"
    ],
    "mr": [
        "नमस्कार! मी SwasthyaSarthi आहे, तुमचा फार्मसी सहायक. आज मी तुमची कशी मदत करू शकतो?",
        "नमस्कार! मी तुमच्या आरोग्य आणि औषधांच्या गरजेत मदत करण्यासाठी येथे आहे."
    ],
    "bn": [
        "নমস্কার! আমি SwasthyaSarthi, আপনার ফার্মেসি সহকারী। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "নমস্কার! আমি আপনার স্বাস্থ্য এবং ওষুধের প্রয়োজনে সাহায্য করতে এসেছি।"
    ],
    "gu": [
        "નમસ્તે! હું SwasthyaSarthi છું, તમારો ફાર્મસી સહાયક. આજે હું તમને કેવી રીતે મદદ કરી શકું?",
        "નમસ્તે! હું તમારા સ્વાસ્થ્ય અને દવાઓની જરૂરિયાતોમાં મદદ કરવા માટે અહીં છું."
    ]
}

# How are you responses
HOW_ARE_YOU_RESPONSES = {
    "en": [
        "I'm doing great, thank you for asking! I'm here and ready to help you with any health questions.",
        "I'm well, thanks! How can I assist you today?",
        "Doing well! I'm your pharmacy assistant, ready to help with medicines and health queries."
    ],
    "hi": [
        "मैं ठीक हूं, पूछने के लिए धन्यवाद! मैं आपके किसी भी स्वास्थ्य प्रश्न में मदद के लिए हूं।",
        "मैं ठीक हूं! आज मैं आपकी कैसे मदद कर सकता हूं?"
    ],
    "mr": [
        "मी ठीक आहे, विचारल्याबद्दल धन्यवाद! मी तुमच्या कोणत्याही आरोग्य प्रश्नांमध्ये मदत करण्यासाठी आहे.",
        "मी ठीक आहे! आज मी तुमची कशी मदत करू शकतो?"
    ]
}

# Thank you responses
THANK_YOU_RESPONSES = {
    "en": [
        "You're welcome! Is there anything else I can help you with?",
        "Happy to help! Feel free to ask if you need anything else.",
        "My pleasure! Let me know if you have more questions."
    ],
    "hi": [
        "आपका स्वागत है! क्या मैं आपकी किसी और मदद कर सकता हूं?",
        "खुशी होगी! अगर आपको और कुछ चाहिए तो बताएं।"
    ],
    "mr": [
        "तुमचे स्वागत आहे! मी तुम्हाला आणखी कशी मदत करू शकतो?",
        "मदत करून आनंद झाला! जर तुम्हाला आणखी काही हवे असेल तर सांगा."
    ]
}

# General chat system prompt - now imported from prompt_templates
GENERAL_CHAT_SYSTEM_PROMPT = """You are SwasthyaSarthi, a friendly multilingual healthcare assistant.

Your traits:
- Friendly, conversational, and helpful
- Keep responses short and human-like
- Support multiple languages (English, Hindi, Marathi, Bengali, Gujarati)
- Always offer to help with health/medicine questions
- Never give medical diagnoses, always suggest consulting a doctor

Respond naturally like a friendly assistant."""



def _get_random_response(responses: dict, language: str) -> str:
    """Get a random response from the appropriate language dict."""
    lang_responses = responses.get(language, responses["en"])
    import random
    return random.choice(lang_responses)


def _generate_llm_response(user_input: str, language: str, llm) -> str:
    """Generate response using LLM with Ollama-optimized prompt."""
    try:
        # Use formatted prompt from templates
        prompt = format_general_chat_prompt(user_input, language)
        
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config=_get_langsmith_config()
        )
        
        return response.content
    except Exception as e:
        print(f"[General Chat] LLM error: {e}")
        return None



def general_chat_agent(state: AgentState) -> AgentState:
    """
    Handle general conversation (greetings, casual chat).
    
    Flow:
    1. Detect type of chat (greeting, how are you, thanks, etc.)
    2. Use LLM for complex queries or template responses
    3. Return friendly response
    """
    # Initialize trace
    if "agent_trace" not in state:
        state["agent_trace"] = []
    
    user_input = state.get("user_input", "")
    user_language = state.get("user_language", "en")
    
    # Trace entry with observability metadata
    trace_entry = {
        "agent": "general_chat_agent",
        "agent_name": "general_chat_agent",
        "action": "handle_conversation",
        "step": "handle_conversation",
        "user_input": user_input[:30],
        "language": user_language
    }

    
    text_lower = user_input.lower()
    
    # Detect type of chat
    response = None
    
    # GREETING
    greeting_keywords = ["hi", "hello", "hey", "namaste", "namaskar", "good morning", "good evening", "good night", "salaam", "adab"]
    if any(kw in text_lower for kw in greeting_keywords) and len(text_lower) < 30:
        response = _get_random_response(GREETING_RESPONSES, user_language)
    
    # HOW ARE YOU
    elif any(phrase in text_lower for phrase in ["how are you", "how r u", "kaise ho", "kasa ahe", "kem cho"]):
        response = _get_random_response(HOW_ARE_YOU_RESPONSES, user_language)
    
    # THANK YOU
    thank_keywords = ["thank", "thanks", "dhanyavad", "shukriya", "abhari", "dhonnobad"]
    if any(kw in text_lower for kw in thank_keywords):
        response = _get_random_response(THANK_YOU_RESPONSES, user_language)
    
    # GOODBYE
    goodbye_keywords = ["bye", "goodbye", "see you", "later", "take care", "alvida"]
    if any(kw in text_lower for kw in goodbye_keywords):
        goodbye_responses = {
            "en": "Goodbye! Take care of your health. Feel free to come back anytime!",
            "hi": "अलविदा! अपने स्वास्थ्य का ध्यान रखें। कभी भी वापस आ सकते हैं!",
            "mr": "नमस्कार! आरोग्याची काळजी घ्या. कधीही परत या!",
            "bn": "বিদায়! আপনার স্বাস্থ্যের যত্ন নিন। যেকোনো সময় ফিরে আসুন!",
            "gu": "અલવિદા! તમારા સ્વાસ્થ્યની કાળજી રાખો. કોઈપણ સમયે પાછા આવો!"
        }
        response = goodbye_responses.get(user_language, goodbye_responses["en"])
    
    # Try LLM for other cases
    if not response:
        llm = get_llm()
        if llm:
            response = _generate_llm_response(user_input, user_language, llm)
    
    # Fallback response
    if not response:
        fallback = {
            "en": "I understand! I'm here to help with medicines and health questions. What would you like to know?",
            "hi": "मैं समझता हूं! मैं दवाओं और स्वास्थ्य प्रश्नों में मदद के लिए हूं। आप क्या जानना चाहेंगे?",
            "mr": "मी समजतो! मी औषधे आणि आरोग्य प्रश्नांमध्ये मदत करण्यासाठी आहे. तुम्हाला काय जाणून घ्यायचे आहे?",
            "bn": "আমি বুঝতে পারছি! আমি ওষুধ এবং স্বাস্থ্য প্রশ্নে সাহায্য করতে এসেছি। আপনি কী জানতে চান?",
            "gu": "હું સમજું છું! હું દવાઓ અને સ્વાસ્થ્ય પ્રશ્નોમાં મદદ કરવા માટે છું. તમે શું જાણવા માંગો છો?"
        }
        response = fallback.get(user_language, fallback["en"])
    
    # Update state
    state["final_response"] = response
    trace_entry["response"] = response[:50]
    
    # Add observability metadata for LangSmith
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["agent_name"] = "general_chat_agent"
    state["metadata"]["action"] = "general_conversation"
    state["metadata"]["general_chat"] = "completed"
    state["metadata"]["language"] = user_language
    
    state["agent_trace"].append(trace_entry)
    
    return state
