# tools/order_tool.py
import requests
API_URL = "http://localhost:8000"

def create_order(patient_id: str, product_name: str, quantity: int):
    # Ensure patient_id has a default value
    if not patient_id:
        patient_id = "PAT001"
    
    res = requests.post(
        f"{API_URL}/create_order",
        params={"patient_id": patient_id, "product_name": product_name, "quantity": quantity}
    )
    res.raise_for_status()
    return res.json()
