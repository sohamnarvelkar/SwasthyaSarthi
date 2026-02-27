import requests
API_URL = 'http://localhost:8001'

# Simple test
print('Testing create_order...')
r = requests.post(f'{API_URL}/create_order', params={
    'patient_id': 'test001',
    'product_name': 'Panthenol Spray, 46,3 mg/g Schaum zur Anwendung auf der Haut',
    'quantity': 2
}, timeout=10)
print(f'Status: {r.status_code}')
print(f'Response: {r.text[:500]}')
