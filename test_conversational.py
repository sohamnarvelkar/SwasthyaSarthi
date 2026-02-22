"""Test conversational ordering with the enhanced agents."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from orchestration.graph import app_graph

# Test cases for conversational ordering
test_cases = [
    {
        "name": "English - Simple order",
        "input": "I want to buy some Aspirin",
        "language": "en"
    },
    {
        "name": "Hindi - Simple order",
        "input": "मुझे Aspirin चाहिए",
        "language": "hi"
    },
    {
        "name": "English - With quantity",
        "input": "I need 2 packs of Vitamin D",
        "language": "en"
    },
    {
        "name": "English - Natural conversation",
        "input": "My head is aching, can you give me something for pain?",
        "language": "en"
    },
    {
        "name": "Marathi - Simple order",
        "input": "मला Omega-3 हवंय",
        "language": "mr"
    }
]

print("=" * 60)
print("TESTING CONVERSATIONAL ORDERING")
print("=" * 60)

for test in test_cases:
    print(f"\n--- Test: {test['name']} ---")
    print(f"Input: {test['input']}")
    print(f"Language: {test['language']}")
    
    try:
        initial_state = {
            "user_input": test["input"],
            "user_id": "TEST_PATIENT",
            "user_email": "test@example.com",
            "user_phone": "+919999999999",
            "user_address": "Test Address",
            "user_language": test["language"],
            "structured_order": {},
            "safety_result": {},
            "final_response": "",
            "is_proactive": False,
            "refill_alerts": []
        }
        
        result = app_graph.invoke(initial_state)
        
        print(f"Structured Order: {result.get('structured_order', {})}")
        print(f"Safety Result: {result.get('safety_result', {})}")
        print(f"Final Response: {result.get('final_response', '')[:200]}...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("TESTS COMPLETED")
print("=" * 60)
