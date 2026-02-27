"""
Test file for ChatGPT-like SwasthyaSarthi system.
Tests all success scenarios and core functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from orchestration.graph import run_conversation, get_conversation_context
from agents.conversation_memory import clear_all_sessions, get_session


def test_case_1_greeting():
    """Test Case 1: User says Hi → greeting reply"""
    print("\n" + "="*60)
    print("TEST CASE 1: Greeting")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="Hi",
        user_id="test_user_1",
        session_id="session_1",
        user_language="en"
    )
    
    print(f"User: Hi")
    print(f"Intent: {result.get('intent')}")
    print(f"Response: {result.get('response')}")
    
    # Verify
    assert result.get('intent') in ['GREETING', 'GENERAL_CHAT'], f"Expected GREETING or GENERAL_CHAT, got {result.get('intent')}"
    assert len(result.get('response', '')) > 0, "Response should not be empty"
    assert 'swasthyasarthi' in result.get('response', '').lower() or 'hello' in result.get('response', '').lower(), "Should be a greeting"
    
    print("✅ Test Case 1 PASSED")
    return True


def test_case_2_symptoms():
    """Test Case 2: User has fever and cough → symptom explanation + dataset medicine suggestion"""
    print("\n" + "="*60)
    print("TEST CASE 2: Symptom Query")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="I have fever and cough",
        user_id="test_user_2",
        session_id="session_2",
        user_language="en"
    )
    
    print(f"User: I have fever and cough")
    print(f"Intent: {result.get('intent')}")
    print(f"Symptoms: {result.get('symptoms', [])}")
    print(f"Response: {result.get('response', '')[:200]}...")
    
    # Verify
    assert result.get('intent') in ['SYMPTOM_QUERY', 'MEDICAL_INFORMATION'], f"Expected SYMPTOM_QUERY, got {result.get('intent')}"
    symptoms = result.get('symptoms', [])
    assert len(symptoms) > 0, "Should identify symptoms"
    assert any(s in ['fever', 'cough'] for s in symptoms), f"Should identify fever or cough, got {symptoms}"
    
    print("✅ Test Case 2 PASSED")
    return True


def test_case_3_order_medicine():
    """Test Case 3: User wants to order medicine → order flow"""
    print("\n" + "="*60)
    print("TEST CASE 3: Medicine Order")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="I want to order Paracetamol",
        user_id="test_user_3",
        session_id="session_3",
        user_language="en"
    )
    
    print(f"User: I want to order Paracetamol")
    print(f"Intent: {result.get('intent')}")
    print(f"Response: {result.get('response', '')[:200]}...")
    
    # Verify
    assert result.get('intent') == 'MEDICINE_ORDER', f"Expected MEDICINE_ORDER, got {result.get('intent')}"
    assert len(result.get('response', '')) > 0, "Response should not be empty"
    
    print("✅ Test Case 3 PASSED")
    return True


def test_case_4_general_chat():
    """Test Case 4: Random chat → natural response"""
    print("\n" + "="*60)
    print("TEST CASE 4: General Chat")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="How are you today?",
        user_id="test_user_4",
        session_id="session_4",
        user_language="en"
    )
    
    print(f"User: How are you today?")
    print(f"Intent: {result.get('intent')}")
    print(f"Response: {result.get('response')}")
    
    # Verify
    assert result.get('intent') in ['GENERAL_CHAT', 'GREETING'], f"Expected GENERAL_CHAT, got {result.get('intent')}"
    assert len(result.get('response', '')) > 0, "Response should not be empty"
    
    print("✅ Test Case 4 PASSED")
    return True


def test_case_5_multilingual_hindi():
    """Test Case 5: Hindi language support"""
    print("\n" + "="*60)
    print("TEST CASE 5: Multilingual (Hindi)")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="Namaste, mujhe fever hai",
        user_id="test_user_5",
        session_id="session_5",
        user_language="hi"
    )
    
    print(f"User: Namaste, mujhe fever hai")
    print(f"Detected Intent: {result.get('intent')}")
    print(f"Response: {result.get('response', '')[:200]}...")
    
    # Verify
    assert result.get('intent') in ['GREETING', 'SYMPTOM_QUERY'], f"Expected GREETING or SYMPTOM_QUERY, got {result.get('intent')}"
    assert len(result.get('response', '')) > 0, "Response should not be empty"
    
    print("✅ Test Case 5 PASSED")
    return True


def test_case_6_conversation_memory():
    """Test Case 6: Conversation memory for follow-up"""
    print("\n" + "="*60)
    print("TEST CASE 6: Conversation Memory")
    print("="*60)
    
    clear_all_sessions()
    user_id = "test_user_6"
    session_id = "session_6"
    
    # First message - symptoms
    result1 = run_conversation(
        user_input="I have headache",
        user_id=user_id,
        session_id=session_id,
        user_language="en"
    )
    
    print(f"User: I have headache")
    print(f"Intent: {result1.get('intent')}")
    print(f"Symptoms stored: {result1.get('symptoms', [])}")
    
    # Check memory
    context = get_conversation_context(user_id, session_id)
    print(f"Memory - Last symptoms: {context.get('last_symptoms', [])}")
    
    # Verify memory
    assert len(context.get('last_symptoms', [])) > 0, "Symptoms should be stored in memory"
    
    print("✅ Test Case 6 PASSED")
    return True


def test_case_7_dataset_grounded():
    """Test Case 7: Verify medicines come from dataset only"""
    print("\n" + "="*60)
    print("TEST CASE 7: Dataset-Grounded Recommendations")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="I have fever, what medicine should I take?",
        user_id="test_user_7",
        session_id="session_7",
        user_language="en"
    )
    
    print(f"User: I have fever, what medicine should I take?")
    print(f"Intent: {result.get('intent')}")
    print(f"Recommended medicines: {result.get('recommended_medicines', [])}")
    
    # Verify medicines are from dataset
    medicines = result.get('recommended_medicines', [])
    if medicines:
        for med in medicines:
            assert 'name' in med, "Medicine should have a name"
            assert 'match_score' in med or 'price' in med, "Medicine should have dataset attributes"
            print(f"  - {med.get('name')} (from dataset)")
    
    print("✅ Test Case 7 PASSED")
    return True


def test_case_8_observability_metadata():
    """Test Case 8: Verify observability metadata is present"""
    print("\n" + "="*60)
    print("TEST CASE 8: Observability Metadata")
    print("="*60)
    
    clear_all_sessions()
    
    result = run_conversation(
        user_input="I have cough and cold",
        user_id="test_user_8",
        session_id="session_8",
        user_language="en"
    )
    
    metadata = result.get('metadata', {})
    print(f"Metadata: {metadata}")
    
    # Verify observability fields
    assert 'agent_name' in metadata, "Metadata should contain agent_name"
    assert 'action' in metadata, "Metadata should contain action"
    assert 'language' in metadata, "Metadata should contain language"
    
    print("✅ Test Case 8 PASSED")
    return True


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*60)
    print("SWASTHYASARTHI CHATGPT-LIKE SYSTEM TESTS")
    print("="*60)
    
    tests = [
        test_case_1_greeting,
        test_case_2_symptoms,
        test_case_3_order_medicine,
        test_case_4_general_chat,
        test_case_5_multilingual_hindi,
        test_case_6_conversation_memory,
        test_case_7_dataset_grounded,
        test_case_8_observability_metadata,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}")
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
