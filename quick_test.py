import requests

# Test all endpoints
tests = [
    ('/medicines', None),
    ('/patients', None),
    ('/orders', None),
    ('/medicine?name=Omega-3', None),
    ('/patients/P001', None),
    ('/check-refills?days_ahead=7', None),
]

results = []
for path, _ in tests:
    try:
        r = requests.get('http://localhost:8000' + path)
        results.append(f"{path} -> {r.status_code}")
    except Exception as e:
        results.append(f"{path} -> ERROR: {e}")

for r in results:
    print(r)
