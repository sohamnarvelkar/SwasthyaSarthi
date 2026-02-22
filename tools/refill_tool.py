# tools/refill_tool.py
import requests
API_URL = "http://localhost:8000"

def check_refills(days_ahead: int = 3):
    """Check for medicines that need refilling."""
    res = requests.get(f"{API_URL}/check-refills", params={"days_ahead": days_ahead})
    res.raise_for_status()
    return res.json()

def get_refill_alerts(status: str = None):
    """Get all refill alerts."""
    params = {}
    if status:
        params["status"] = status
    res = requests.get(f"{API_URL}/refill-alerts", params=params)
    res.raise_for_status()
    return res.json()

def create_refill_alert(patient_id: str, product_name: str, quantity: int, days_until_refill: int):
    """Create a refill alert."""
    res = requests.post(
        f"{API_URL}/refill-alerts",
        params={
            "patient_id": patient_id,
            "product_name": product_name,
            "quantity": quantity,
            "days_until_refill": days_until_refill
        }
    )
    res.raise_for_status()
    return res.json()

def update_refill_alert(alert_id: int, status: str):
    """Update a refill alert status."""
    res = requests.put(f"{API_URL}/refill-alerts/{alert_id}", params={"status": status})
    res.raise_for_status()
    return res.json()
