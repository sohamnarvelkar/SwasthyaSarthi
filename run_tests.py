"""Simple test to verify all system functionalities."""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Test 1: Database & Inventory
print("=" * 50)
print("TEST 1: DATABASE & INVENTORY")
print("=" * 50)
try:
    from tools.inventory_tool import get_all_medicines, get_medicine
    
    all_meds = get_all_medicines()
    print(f"OK - Total medicines: {len(all_meds)}")
    
    med = get_medicine("Omega-3")
    if med:
        print(f"OK - Medicine: {med.get('name', 'N/A')[:30]}")
        print(f"    Stock: {med.get('stock', 0)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Patient Data
print("\n" + "=" * 50)
print("TEST 2: PATIENT DATA")
print("=" * 50)
try:
    from tools.patient_tool import get_patients
    patients = get_patients()
    print(f"OK - Total patients: {len(patients)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Refill Detection
print("\n" + "=" * 50)
print("TEST 3: PREDICTIVE REFILL DETECTION")
print("=" * 50)
try:
    from tools.refill_tool import check_refills
    result = check_refills(days_ahead=30)
    alerts = result.get("alerts", [])
    print(f"OK - Refill alerts: {len(alerts)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 4: Order Placement
print("\n" + "=" * 50)
print("TEST 4: ORDER PLACEMENT")
print("=" * 50)
try:
    from tools.order_tool import create_order
    result = create_order("TEST_PATIENT", "NORSAN Omega-3 Total", 1)
    if result.get("status") == "success":
        print(f"OK - Order placed, ID: {result.get('order_id')}")
    else:
        print(f"WARN - Order failed: {result.get('reason')}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 5: Email Configuration
print("\n" + "=" * 50)
print("TEST 5: EMAIL NOTIFICATION")
print("=" * 50)
try:
    from tools.webhook_tool import GMAIL_EMAIL
    if GMAIL_EMAIL:
        print(f"OK - Email configured: {GMAIL_EMAIL}")
    else:
        print("WARN - Email not configured")
except Exception as e:
    print(f"ERROR: {e}")

# Test 6: Webhooks
print("\n" + "=" * 50)
print("TEST 6: WEBHOOK INTEGRATION")
print("=" * 50)
try:
    from tools.webhook_tool import trigger_fulfillment
    result = trigger_fulfillment("TEST-123")
    print(f"OK - Webhook triggered")
except Exception as e:
    print(f"ERROR: {e}")

# Test 7: Full Agent Workflow
print("\n" + "=" * 50)
print("TEST 7: AGENT WORKFLOW")
print("=" * 50)
try:
    from orchestration.graph import app_graph
    initial_state = {
        "user_input": "I want to buy 2 Omega-3",
        "structured_order": {},
        "safety_result": {},
        "final_response": ""
    }
    result = app_graph.invoke(initial_state)
    if result.get("final_response"):
        print(f"OK - Workflow completed")
        print(f"    Response: {result.get('final_response', '')[:50]}...")
except Exception as e:
    print(f"ERROR: {e}")

# Test 8: Frontend
print("\n" + "=" * 50)
print("TEST 8: FRONTEND STATUS")
print("=" * 50)
try:
    import requests
    r = requests.get("http://localhost:8501", timeout=3)
    print(f"OK - Frontend running (status: {r.status_code})")
except Exception as e:
    print(f"WARN - Frontend not accessible: {e}")

# Test 9: Backend
print("\n" + "=" * 50)
print("TEST 9: BACKEND API STATUS")
print("=" * 50)
try:
    import requests
    r = requests.get("http://localhost:8000/medicine?name=test", timeout=3)
    print(f"OK - Backend running (status: {r.status_code})")
except Exception as e:
    print(f"WARN - Backend not accessible: {e}")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETED")
print("=" * 50)
