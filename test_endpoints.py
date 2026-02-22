import requests
import json

results = []

# Test patients endpoint
r1 = requests.get('http://localhost:8000/patients')
results.append(f'Patients: {r1.status_code}, count: {len(r1.json())}')

# Test orders endpoint  
r2 = requests.get('http://localhost:8000/orders')
results.append(f'Orders: {r2.status_code}, count: {len(r2.json())}')

# Test refill alerts
r3 = requests.get('http://localhost:8000/refill-alerts')
results.append(f'Refill Alerts: {r3.status_code}, count: {len(r3.json())}')

# Test medicine search
r4 = requests.get('http://localhost:8000/medicine?name=Omega')
data = r4.json()
if isinstance(data, dict):
    results.append(f'Medicine Search: {r4.status_code}, found: {data.get("name", "Not found")[:40]}')
else:
    results.append(f'Medicine Search: {r4.status_code}, results: {len(data)}')

# Write to file
with open("endpoint_results.txt", "w") as f:
    f.write("\n".join(results))
    
print("Done - see endpoint_results.txt")
