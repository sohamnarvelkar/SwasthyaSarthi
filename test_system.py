"""Quick test to verify the system works after fixes."""
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 50)
print("Testing SwasthyaSarthi System")
print("=" * 50)

# Test 1: Get all medicines
print("\n1. Testing get_all_medicines()...")
try:
    from tools.inventory_tool import get_all_medicines
    meds = get_all_medicines()
    print(f"   [OK] Got {len(meds)} medicines")
    
    # Test filtering for low stock
    low_stock = [m for m in meds if m.get("stock", 0) < 10]
    print(f"   [OK] Low stock items: {len(low_stock)}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Get medicine by name
print("\n2. Testing get_medicine()...")
try:
    from tools.inventory_tool import get_medicine
    med = get_medicine("Omega-3")
    if med:
        print(f"   [OK] Found: {med.get('name', 'N/A')[:30]}... Stock: {med.get('stock', 0)}")
    else:
        print("   [WARN] No medicine found (may not exist)")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: Get patients
print("\n3. Testing get_patients()...")
try:
    from tools.patient_tool import get_patients
    patients = get_patients()
    print(f"   [OK] Got {len(patients)} patients")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 4: Check refills
print("\n4. Testing check_refills()...")
try:
    from tools.refill_tool import check_refills
    result = check_refills(days_ahead=30)
    alerts = result.get("alerts", [])
    print(f"   [OK] Found {len(alerts)} refill alerts")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 5: Create order (test order)
print("\n5. Testing create_order()...")
try:
    from tools.order_tool import create_order
    # Try with a medicine we know exists
    meds = get_all_medicines()
    if meds:
        test_med = meds[0].get("name", "")
        result = create_order("TEST_PATIENT", test_med, 1)
        print(f"   [OK] Order result: {result}")
    else:
        print("   [SKIP] No medicines available")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 50)
print("All tests completed!")
print("=" * 50)
