# tools/patient_tool.py
import requests
API_URL = "http://localhost:8000"

def get_patients():
    """Get all patients. Returns a list."""
    res = requests.get(f"{API_URL}/patients")
    res.raise_for_status()
    data = res.json()
    
    # Ensure we return a list
    if data is None:
        return []
    return data if isinstance(data, list) else [data]

def get_patient(patient_id: str):
    """Get patient details by ID. Returns a single patient dict or None."""
    res = requests.get(f"{API_URL}/patients/{patient_id}")
    res.raise_for_status()
    data = res.json()
    
    # Handle case where API returns an error dict
    if isinstance(data, dict) and "error" in data:
        return None
    return data

def get_patient_orders(patient_id: str):
    """Get order history for a patient. Returns a list."""
    res = requests.get(f"{API_URL}/patients/{patient_id}/orders")
    res.raise_for_status()
    data = res.json()
    
    # Ensure we return a list
    if data is None:
        return []
    return data if isinstance(data, list) else [data]

def get_patient_by_phone(phone: str):
    """Find patient by phone number. Returns a single patient dict or None."""
    patients = get_patients()
    if not patients:
        return None
    for p in patients:
        if p.get("phone") == phone:
            return p
    return None

def get_patient_by_email(email: str):
    """Find patient by email. Returns a single patient dict or None."""
    patients = get_patients()
    if not patients:
        return None
    for p in patients:
        if p.get("email") == email:
            return p
    return None
