"""Test script for the SwasthyaSarthi workflow."""
from orchestration.graph import app_graph

# Test 1: Order placement
print("=" * 50)
print("TEST 1: Placing an order for Omega-3")
print("=" * 50)

result = app_graph.invoke({
    'user_input': 'I want to buy some Omega-3',
    'user_id': 'PAT001',
    'user_email': 'test@example.com',
    'user_phone': '+1234567890',
    'user_address': 'Test Address',
    'user_language': 'en',
    'structured_order': {},
    'safety_result': {},
    'final_response': '',
    'is_proactive': False,
    'refill_alerts': []
})

print('Parsed Order:', result.get('structured_order'))
print('Safety Check:', result.get('safety_result'))
print('Response:', result.get('final_response'))
print()

# Test 2: Check out of stock
print("=" * 50)
print("TEST 2: Checking safety with out of stock")
print("=" * 50)

result2 = app_graph.invoke({
    'user_input': 'I need Aspirin',
    'user_id': 'PAT001',
    'user_email': 'test@example.com',
    'user_phone': '+1234567890',
    'user_address': 'Test Address',
    'user_language': 'en',
    'structured_order': {},
    'safety_result': {},
    'final_response': '',
    'is_proactive': False,
    'refill_alerts': []
})

print('Parsed Order:', result2.get('structured_order'))
print('Safety Check:', result2.get('safety_result'))
print('Response:', result2.get('final_response'))
print()

print("=" * 50)
print("All tests completed!")
print("=" * 50)
