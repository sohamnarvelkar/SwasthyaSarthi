# tools/inventory_tool.py
import requests
API_URL = "http://localhost:8000"

def get_medicine(name: str):
    """Get medicine by name. Returns a single medicine dict or None."""
    res = requests.get(f"{API_URL}/medicine", params={"name": name})
    res.raise_for_status()
    data = res.json()
    
    # Handle case where API returns a list (when no name filter is used)
    if isinstance(data, list):
        if len(data) > 0:
            return data[0]  # Return first match
        return None
    return data

def get_all_medicines():
    """Get all medicines."""
    res = requests.get(f"{API_URL}/medicines")
    res.raise_for_status()
    data = res.json()
    
    # Ensure we return a list
    if data is None:
        return []
    return data if isinstance(data, list) else [data]

def search_medicines(query: str):
    """Search medicines by name. Returns a list of matches."""
    res = requests.get(f"{API_URL}/medicine", params={"name": query})
    res.raise_for_status()
    data = res.json()
    
    # Handle case where API returns a single item
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []
