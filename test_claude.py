from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
print('API Key present:', bool(api_key))
print('API Key starts with:', api_key[:15] if api_key else 'None')

llm = ChatAnthropic(model='claude-3-5-sonnet-20241022', api_key=api_key)
response = llm.invoke('Hello, what is 2+2?')
print('Response:', response.content)
