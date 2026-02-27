#!/usr/bin/env python3
"""
Test script for Voice Agent Components
Tests: Critical-path and thorough testing
"""

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("SWASTHYASARTHI VOICE AGENT - COMPONENT TESTING")
print("=" * 60)

# Test 1: Import all voice components
print("\n=== TEST 1: Import Voice Components ===")
tests_passed = 0
tests_failed = 0

try:
    from frontend.components.language_detector import detect_language, get_language_code, get_tts_language_code
    print("✅ language_detector imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ language_detector import failed: {e}")
    tests_failed += 1

try:
    from frontend.components.speech_to_text import SpeechToText, listen_once, WHISPER_LANG_CODES
    print("✅ speech_to_text imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ speech_to_text import failed: {e}")
    tests_failed += 1

try:
    from frontend.components.text_to_speech import TextToSpeech, speak_text, EDGE_VOICES
    print("✅ text_to_speech imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ text_to_speech import failed: {e}")
    tests_failed += 1

try:
    from frontend.components.voice_loop_controller import VoiceLoopController, StreamlitVoiceController, VoiceModeState
    print("✅ voice_loop_controller imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ voice_loop_controller import failed: {e}")
    tests_failed += 1

try:
    from frontend.components.voice_agent import render_voice_mode_ui, is_voice_mode_active, stop_voice_mode, get_voice_input_text
    print("✅ voice_agent imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ voice_agent import failed: {e}")
    tests_failed += 1

# Test 2: Language Detection
print("\n=== TEST 2: Language Detection (Critical Path) ===")

test_cases = [
    ("Hello, I have a fever", "English"),
    ("मुझे बुखार है", "Hindi"),
    ("मला ताप आहे", "Marathi"),
    ("Mujhe fever hai", "English"),
    ("Kya aap doctor hain", "Hindi"),
    ("Mala doktar hava aahe", "Marathi"),
]

for text, expected in test_cases:
    try:
        result = detect_language(text, use_llm_fallback=False)
        detected = result.get('language', 'Unknown')
        method = result.get('method', 'unknown')
        if detected == expected:
            print(f"✅ \"{text[:30]}...\" → {detected} (method: {method})")
            tests_passed += 1
        else:
            print(f"⚠️ \"{text[:30]}...\" → {detected} (expected: {expected})")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Error detecting language for '{text[:30]}': {e}")
        tests_failed += 1

# Test 3: Language Codes
print("\n=== TEST 3: Language Codes ===")

try:
    en_code = get_language_code("English")
    hi_code = get_language_code("Hindi")
    mr_code = get_language_code("Marathi")
    
    print(f"✅ English code: {en_code}")
    print(f"✅ Hindi code: {hi_code}")
    print(f"✅ Marathi code: {mr_code}")
    
    if en_code == "en" and hi_code == "hi" and mr_code == "mr":
        tests_passed += 3
    else:
        print("⚠️ Language codes don't match expected values")
        tests_failed += 3
except Exception as e:
    print(f"❌ Language code test failed: {e}")
    tests_failed += 3

# Test 4: TTS Voices Configuration
print("\n=== TEST 4: TTS Voices Configuration ===")

try:
    print(f"✅ English voices: {list(EDGE_VOICES['English'].keys())}")
    print(f"✅ Hindi voices: {list(EDGE_VOICES['Hindi'].keys())}")
    print(f"✅ Marathi voices: {list(EDGE_VOICES['Marathi'].keys())}")
    tests_passed += 1
except Exception as e:
    print(f"❌ TTS voices test failed: {e}")
    tests_failed += 1

# Test 5: Whisper Language Codes
print("\n=== TEST 5: Whisper Language Codes ===")

try:
    print(f"✅ Whisper English: {WHISPER_LANG_CODES['English']}")
    print(f"✅ Whisper Hindi: {WHISPER_LANG_CODES['Hindi']}")
    print(f"✅ Whisper Marathi: {WHISPER_LANG_CODES['Marathi']}")
    tests_passed += 1
except Exception as e:
    print(f"❌ Whisper codes test failed: {e}")
    tests_failed += 1

# Test 6: Voice Mode States
print("\n=== TEST 6: Voice Mode States ===")

try:
    states = [VoiceModeState.IDLE, VoiceModeState.LISTENING, VoiceModeState.PROCESSING, 
              VoiceModeState.SPEAKING, VoiceModeState.WAITING, VoiceModeState.ERROR]
    for state in states:
        print(f"✅ State: {state.value}")
    tests_passed += 1
except Exception as e:
    print(f"❌ Voice mode states test failed: {e}")
    tests_failed += 1

# Test 7: TTS Class Initialization
print("\n=== TEST 7: TTS Class Initialization ===")

try:
    tts = TextToSpeech(voice_type="female", use_edge_tts=True)
    print(f"✅ TTS initialized with voice_type=female, use_edge_tts=True")
    tests_passed += 1
except Exception as e:
    print(f"❌ TTS initialization failed: {e}")
    tests_failed += 1

try:
    tts_male = TextToSpeech(voice_type="male", use_edge_tts=False)
    print(f"✅ TTS initialized with voice_type=male, use_edge_tts=False")
    tests_passed += 1
except Exception as e:
    print(f"❌ TTS male initialization failed: {e}")
    tests_failed += 1

# Test 8: STT Class Initialization
print("\n=== TEST 8: STT Class Initialization ===")

try:
    stt = SpeechToText(model_size="base", device="cpu")
    print(f"✅ STT initialized with model_size=base, device=cpu")
    tests_passed += 1
except Exception as e:
    print(f"❌ STT initialization failed: {e}")
    tests_failed += 1

# Test 9: Voice Loop Controller Initialization
print("\n=== TEST 9: Voice Loop Controller Initialization ===")

try:
    controller = VoiceLoopController(
        user_id="test_user",
        user_email="test@example.com",
        session_id="test_session",
        voice_type="female"
    )
    print(f"✅ VoiceLoopController initialized")
    print(f"   - User ID: {controller.user_id}")
    print(f"   - Current state: {controller.get_current_state().value}")
    tests_passed += 1
except Exception as e:
    print(f"❌ VoiceLoopController initialization failed: {e}")
    tests_failed += 1

# Test 10: Integration with LangGraph
print("\n=== TEST 10: LangGraph Integration ===")

try:
    from orchestration.graph import app_graph
    print(f"✅ LangGraph app_graph imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"❌ LangGraph import failed: {e}")
    tests_failed += 1

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Total Tests: {tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Voice Agent components are working correctly.")
else:
    print(f"\n⚠️ {tests_failed} test(s) failed. Please review the errors above.")

print("=" * 60)
