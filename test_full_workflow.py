"""Test the full agent workflow."""
from orchestration.graph import app_graph

# Test the full workflow
initial_state = {
    'user_input': 'I need some pain tablets',
    'user_id': 'PAT001',
    'user_email': 'test@example.com',
    'user_language': 'en',
    'structured_order': {},
    'safety_result': {},
    'final_response': ''
}

result = app_graph.invoke(initial_state)
print('=== WORKFLOW RESULT ===')
print('Structured Order:', result.get('structured_order'))
print('Safety Result:', result.get('safety_result'))
print('Final Response:', result.get('final_response'))
print('SUCCESS: Full workflow completed!')
