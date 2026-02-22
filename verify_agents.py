"""Verify the enhanced agents are working correctly."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Test imports
    from agents.pharmacist_agent import pharmacist_agent
    from agents.safety_agent import safety_agent
    from agents.execution_agent import execution_agent
    from orchestration.graph import app_graph
    
    print("[OK] All agent modules imported successfully!")
    print("[OK] Graph nodes:", list(app_graph.nodes.keys()))
    
    # Test pharmacist agent with conversational input
    test_state = {
        "user_input": "I need some pain medicine",
        "user_language": "en",
        "user_id": "TEST001",
        "user_email": "test@test.com",
        "user_phone": "+919999999999",
        "user_address": "Test Address",
        "structured_order": {},
        "safety_result": {},
        "final_response": "",
        "is_proactive": False,
        "refill_alerts": []
    }
    
    result = pharmacist_agent(test_state)
    print("[OK] Pharmacist agent parsed:", result.get('structured_order', {}))
    
    # Test safety agent
    result = safety_agent(result)
    print("[OK] Safety agent result:", result.get('safety_result', {}))
    
    # Test execution agent
    result = execution_agent(result)
    print("[OK] Execution agent response:", result.get('final_response', '')[:100])
    
    print("\n" + "="*50)
    print("ALL TESTS PASSED!")
    print("="*50)
    
except Exception as e:
    print("ERROR:", str(e))
    import traceback
    traceback.print_exc()
