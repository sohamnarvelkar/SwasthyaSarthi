"""Test multi-agent system interaction"""
import sys
sys.path.insert(0, '.')

from orchestration.graph import app_graph
from agents.state_schema import AgentState

# Create initial state with a test order
initial_state = {
    "user_input": "I want to buy 2 Omega-3 medicines",
    "user_id": "PAT001",
    "user_email": "test@example.com",
    "user_phone": "+1234567890",
    "user_address": "123 Test Street",
    "user_language": "en",
    "structured_order": {},
    "safety_result": {},
    "final_response": "",
    "is_proactive": False,
    "refill_alerts": []
}

print("=" * 60)
print("MULTI-AGENT SYSTEM TEST")
print("=" * 60)

# Run the workflow
try:
    print("\n1. Starting workflow with: 'I want to buy 2 Omega-3 medicines'")
    result = app_graph.invoke(initial_state)
    
    print("\n2. Agent Interaction Results:")
    print("-" * 40)
    
    # Check Pharmacist Agent output
    print("\n[PHARMACIST AGENT]")
    structured_order = result.get("structured_order", {})
    print(f"   Parsed Order: {structured_order}")
    
    # Check Safety Agent output
    print("\n[SAFETY AGENT]")
    safety_result = result.get("safety_result", {})
    print(f"   Safety Check: {safety_result}")
    
    # Check Execution Agent output
    print("\n[EXECUTION AGENT]")
    final_response = result.get("final_response", "")
    print(f"   Final Response: {final_response}")
    
    print("\n" + "=" * 60)
    print("AGENT INTERACTION TEST COMPLETE")
    print("=" * 60)
    
    # Write results to file
    with open('agent_test_result.txt', 'w') as f:
        f.write("MULTI-AGENT SYSTEM TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Input: {initial_state['user_input']}\n\n")
        f.write(f"Pharmacist Agent parsed: {structured_order}\n\n")
        f.write(f"Safety Agent result: {safety_result}\n\n")
        f.write(f"Execution Agent response: {final_response}\n\n")
        f.write("=" * 50 + "\n")
        if final_response:
            f.write("TEST PASSED - All agents interacted successfully\n")
        else:
            f.write("TEST FAILED\n")
    
    print("\nResults written to agent_test_result.txt")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    
    with open('agent_test_result.txt', 'w') as f:
        f.write("MULTI-AGENT SYSTEM TEST FAILED\n")
        f.write("=" * 50 + "\n")
        f.write(f"Error: {e}\n")
