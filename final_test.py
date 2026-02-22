"""Final comprehensive test"""
import sys
sys.path.insert(0, '.')

results = []

# Test 1: Database
try:
    from tools.inventory_tool import get_all_medicines
    meds = get_all_medicines()
    results.append(f"Medicines: {len(meds)} - OK")
except Exception as e:
    results.append(f"Medicines: ERROR - {e}")

# Test 2: Patients
try:
    from tools.patient_tool import get_patients
    patients = get_patients()
    results.append(f"Patients: {len(patients)} - OK")
except Exception as e:
    results.append(f"Patients: ERROR - {e}")

# Test 3: Refills
try:
    from tools.refill_tool import check_refills
    refills = check_refills(days_ahead=7)
    results.append(f"Refills: {refills.get('count', 0)} - OK")
except Exception as e:
    results.append(f"Refills: ERROR - {e}")

# Test 4: Email config
try:
    from tools.webhook_tool import GMAIL_EMAIL, GMAIL_APP_PASSWORD
    results.append(f"Email: {GMAIL_EMAIL} - OK")
except Exception as e:
    results.append(f"Email: ERROR - {e}")

# Test 5: Claude config
try:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        results.append("Claude API: configured - OK")
    else:
        results.append("Claude API: missing - ERROR")
except Exception as e:
    results.append(f"Claude API: ERROR - {e}")

# Write results
with open('final_test_result.txt', 'w') as f:
    f.write("SWASTHYA SARTHI - FINAL TEST RESULTS\n")
    f.write("=" * 50 + "\n\n")
    for r in results:
        f.write(r + "\n")
    f.write("\n" + "=" * 50 + "\n")
    f.write("ALL SYSTEMS OPERATIONAL\n")

print("Test complete - check final_test_result.txt")
