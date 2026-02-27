import requests
import sys

API_URL = 'http://localhost:8000'

# Test 1: Check backend
print('=== Test 1: Backend Health ===')
try:
    r = requests.get(f'{API_URL}/docs', timeout=5)
    print(f'[OK] Backend running: {r.status_code}')
except Exception as e:
    print(f'[FAIL] Backend not running: {e}')
    sys.exit(1)

# Test 2: Get medicines
print('\n=== Test 2: Get Medicines with Prices ===')
r = requests.get(f'{API_URL}/medicines', timeout=5)
if r.status_code == 200:
    meds = r.json()
    print(f'[OK] Found {len(meds)} medicines')
    if meds:
        print(f'  Sample: {meds[0]["name"]} - Rs.{meds[0]["price"]}')
else:
    print(f'[FAIL] Status: {r.status_code}')

# Test 3: Create order with price
print('\n=== Test 3: Create Order with Price ===')
order_data = {
    'patient_id': 'test_patient_001',
    'product_name': 'Panthenol Spray',
    'quantity': 2
}
r = requests.post(f'{API_URL}/create_order', params=order_data, timeout=10)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'[OK] Order created:')
    print(f'  Product: {result.get("product_name")}')
    print(f'  Quantity: {result.get("quantity")}')
    print(f'  Unit Price: Rs.{result.get("unit_price")}')
    print(f'  Total Price: Rs.{result.get("total_price")}')
else:
    print(f'[FAIL] Response: {r.text[:200]}')

# Test 4: Verify order in database
print('\n=== Test 4: Verify Order in Database ===')
r = requests.get(f'{API_URL}/orders', params={'patient_id': 'test_patient_001'}, timeout=5)
if r.status_code == 200:
    orders = r.json()
    if orders:
        latest = orders[0]
        print(f'[OK] Order in DB:')
        print(f'  ID: {latest.get("id")}')
        print(f'  Product: {latest.get("product_name")}')
        print(f'  Unit Price: Rs.{latest.get("unit_price")}')
        print(f'  Total Price: Rs.{latest.get("total_price")}')
    else:
        print('[FAIL] No orders found')
else:
    print(f'[FAIL] Status: {r.status_code}')

print('\n=== All Tests Complete ===')
