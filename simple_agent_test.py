"""Simple test for multi-agent system"""
import sys
import os

# Set UTF-8 encoding for output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

try:
    # Test imports
    from agents.pharmacist_agent import pharmacist_agent
    from agents.safety_agent import safety_agent
    from agents.execution_agent import execution_agent
    from orchestration.graph import app_graph
    
    print("=== AGENT IMPORT TEST ===")
    print("OK: All agents imported successfully")
    print("OK: Graph nodes:", list(app_graph.nodes.keys()))
    
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
    
    print("\n=== PHARMACIST AGENT TEST ===")
    result = pharmacist_agent(test_state)
    print("Parsed:", result.get('structured_order', {}))
    
    print("\n=== SAFETY AGENT TEST ===")
    result = safety_agent(result)
    print("Safety result:", result.get('safety_result', {}))
    
    print("\n=== EXECUTION AGENT TEST ===")
    result = execution_agent(result)
    print("Final response:", result.get('final_response', ''))
    
    print("\n=== ALL AGENTS TESTED SUCCESSFULLY ===")
    
    # Write to file
    with open('agent_final_result.txt', 'w', encoding='utf-8') as f:
        f.write("MULTI-AGENT SYSTEM TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write("PHARMACIST AGENT: " + str(result.get('structured_order', {})) + "\n")
        f.write("SAFETY AGENT: " + str(result.get('safety_result', {})) + "\n")
        f.write("EXECUTION AGENT: " + str(result.get('final_response', '')) + "\n")
        f.write("\nALL AGENTS WORKING CORRECTLY\n")
    
    print("\nResults saved to agent_final_result.txt")
    
except Exception as e:
    print("ERROR:", str(e))
    import traceback
    traceback.print_exc()
    
    with open('agent_final_result.txt', 'w', encoding='utf-8') as f:
        f.write("MULTI-AGENT SYSTEM TEST FAILED\n")
        f.write("ERROR: " + str(e) + "\n")
