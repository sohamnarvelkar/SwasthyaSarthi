"""Test API endpoints"""
import requests

print("=" * 50)
print("Testing Live API Endpoints")
print("=" * 50)

# Test 1: Get all medicines
print("\n[1] GET /medicines")
r = requests.get('http://localhost:8000/medicines')
print(f"    Status: {r.status_code}")
print(f"    Count: {len(r.json())}")
if r.json():
    print(f"    First: {r.json()[0]['name'][:50]}...")

# Test 2: Get all patients
print("\n[2] GET /patients")
r = requests.get('http://localhost:8000/patients')
print(f"    Status: {r.status_code}")
print(f"    Count: {len(r.json())}")
if r.json():
    print(f"    First: {r.json()[0]['name']} (ID: {r.json()[0]['patient_id']})")

# Test 3: Get orders
print("\n[3] GET /orders")
r = requests.get('http://localhost:8000/orders')
print(f"    Status: {r.status_code}")
print(f"    Count: {len(r.json())}")
if r.json():
    print(f"    First: {r.json()[0]['product_name'][:30]}...")

# Test 4: Search medicine by name
print("\n[4] GET /medicine?name=Omega-3")
r = requests.get('http://localhost:8000/medicine', params={'name': 'Omega-3'})
print(f"    Status: {r.status_code}")
data = r.json()
if isinstance(data, list) and data:
    print(f"    Found: {data[0]['name'][:40]}... Stock: {data[0]['stock']}")
elif isinstance(data, dict):
    print(f"    Found: {data.get('name', 'N/A')}")

# Test 5: Get patient by ID
print("\n[5] GET /patients/P001")
r = requests.get('http://localhost:8000/patients/P001')
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    Patient: {r.json()['name']}, Age: {r.json()['age']}")

# Test 6: Check refills
print("\n[6] GET /check-refills?days_ahead=7")
r = requests.get('http://localhost:8000/check-refills', params={'days_ahead': 7})
print(f"    Status: {r.status_code}")
data = r.json()
print(f"    Alerts: {data.get('count', 0)}")

# Test 7: Create an order
print("\n[7] POST /create_order")
r = requests.post('http://localhost:8000/create_order', params={
    'patient_id': 'P001',
    'product_name': 'NORSAN Omega-3 Total',
    'quantity': 1
})
print(f"    Status: {r.status_code}")
print(f"    Result: {r.json()}")

print("\n" + "=" * 50)
print("All API Tests Complete!")
print("=" * 50)
