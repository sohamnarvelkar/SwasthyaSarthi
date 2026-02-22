"""Debug agent interaction"""
import sys
sys.path.insert(0, '.')

from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import json

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key configured: {bool(api_key)}")

_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)

prompt = '''You are a pharmacy assistant. Parse this customer's order request and extract structured information.

Customer said: "I want to buy 2 Omega-3 medicines"

Return ONLY a JSON object with these exact keys:
{"product_name": "...", "quantity": 1, "dosage": "...", "patient_name": "...", "notes": "..."}'''

try:
    print("Calling Claude LLM...")
    response = _llm.invoke(prompt)
    print(f"Response type: {type(response)}")
    print(f"Response content: {response.content}")
    
    content = response.content.strip()
    try:
        parsed = json.loads(content)
        print(f"Parsed JSON: {parsed}")
    except Exception as e:
        print(f"JSON parse error: {e}")
        
except Exception as e:
    print(f"LLM error: {e}")
    import traceback
    traceback.print_exc()
