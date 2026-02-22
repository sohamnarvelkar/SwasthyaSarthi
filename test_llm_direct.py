"""Direct test of Claude API"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key exists: {bool(api_key)}")
print(f"API Key prefix: {api_key[:20] if api_key else 'None'}...")

if api_key:
    try:
        from langchain_anthropic import ChatAnthropic
        
        llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
        
        response = llm.invoke("Say hello")
        print(f"LLM Response: {response.content}")
        print("SUCCESS: Claude API is working!")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("ERROR: No API key found!")
