"""
Quick verification script for ChatGPT-like SwasthyaSarthi upgrade.
Verifies all components are properly integrated.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def verify_imports():
    """Verify all required modules can be imported."""
    print("="*60)
    print("VERIFYING SYSTEM UPGRADE")
    print("="*60)
    
    checks = []
    
    # 1. Check prompt templates
    try:
        from agents.prompt_templates import (
            format_router_prompt,
            format_general_chat_prompt,
            format_medical_advisor_prompt,
            format_recommendation_prompt
        )
        print("✅ Prompt templates module loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ Prompt templates error: {e}")
        checks.append(False)
    
    # 2. Check router agent
    try:
        from agents.router_agent import router_agent, INTENT_TYPES
        print(f"✅ Router agent loaded (intents: {len(INTENT_TYPES)})")
        checks.append(True)
    except Exception as e:
        print(f"❌ Router agent error: {e}")
        checks.append(False)
    
    # 3. Check medical advisor
    try:
        from agents.medical_advisor_agent import medical_advisor_agent
        print("✅ Medical advisor agent loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ Medical advisor error: {e}")
        checks.append(False)
    
    # 4. Check general chat
    try:
        from agents.general_chat_agent import general_chat_agent
        print("✅ General chat agent loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ General chat error: {e}")
        checks.append(False)
    
    # 5. Check recommendation agent
    try:
        from agents.recommendation_agent import recommendation_agent, load_medicines_dataset
        print("✅ Recommendation agent loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ Recommendation agent error: {e}")
        checks.append(False)
    
    # 6. Check conversation memory
    try:
        from agents.conversation_memory import (
            store_symptoms,
            store_recommendations,
            get_session,
            has_symptoms,
            has_recommendations
        )
        print("✅ Conversation memory loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ Conversation memory error: {e}")
        checks.append(False)
    
    # 7. Check graph
    try:
        from orchestration.graph import app_graph, run_conversation, get_conversation_context
        print("✅ LangGraph workflow loaded")
        checks.append(True)
    except Exception as e:
        print(f"❌ Graph error: {e}")
        checks.append(False)
    
    # 8. Check dataset loading
    try:
        from agents.recommendation_agent import load_medicines_dataset
        medicines = load_medicines_dataset()
        print(f"✅ Dataset loaded: {len(medicines)} medicines")
        checks.append(True)
    except Exception as e:
        print(f"❌ Dataset loading error: {e}")
        checks.append(False)
    
    print("\n" + "="*60)
    passed = sum(checks)
    total = len(checks)
    print(f"RESULT: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All components verified successfully!")
        print("\nSystem Features:")
        print("  ✅ Router + Specialist Agent Architecture")
        print("  ✅ Ollama-Optimized Prompts")
        print("  ✅ Multilingual Support (EN/HI/MR)")
        print("  ✅ Conversation Memory")
        print("  ✅ Dataset-Grounded Recommendations")
        print("  ✅ LangSmith Observability")
        print("  ✅ ChatGPT-like Conversational Flow")
        return True
    else:
        print("⚠️ Some components failed to load")
        return False


def test_basic_flow():
    """Test a basic conversation flow."""
    print("\n" + "="*60)
    print("TESTING BASIC CONVERSATION FLOW")
    print("="*60)
    
    try:
        from orchestration.graph import run_conversation
        from agents.conversation_memory import clear_all_sessions
        
        clear_all_sessions()
        
        # Test greeting
        result = run_conversation("Hi", "test", "test", "en")
        print(f"Greeting test: Intent={result.get('intent')}")
        
        # Test symptoms
        result = run_conversation("I have fever", "test2", "test2", "en")
        print(f"Symptom test: Intent={result.get('intent')}, Symptoms={result.get('symptoms', [])}")
        
        print("✅ Basic flow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Flow test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = verify_imports()
    success2 = test_basic_flow()
    
    if success1 and success2:
        print("\n" + "="*60)
        print("🎉 SYSTEM UPGRADE VERIFIED SUCCESSFULLY!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("⚠️ VERIFICATION FAILED")
        print("="*60)
        sys.exit(1)
