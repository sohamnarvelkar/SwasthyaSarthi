import sys
sys.path.insert(0, '.')

from agents.pharmacist_agent import pharmacist_agent

state = {'user_input': 'I want Omega-3', 'user_language': 'en', 'structured_order': {}}
result = pharmacist_agent(state)
print('Result:', result.get('structured_order'))
