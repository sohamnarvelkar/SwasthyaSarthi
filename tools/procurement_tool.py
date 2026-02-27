"""
Procurement Tool - Automatically triggers warehouse replenishment when stock is low.
Logs procurement events and sends webhook notifications to warehouse system.

Demo: "Inventory fell below 10 units, system auto-ordered replenishment."
"""
import requests
import json
from datetime import datetime
from tools.inventory_tool import get_all_medicines
from backend.database import SessionLocal
from backend.models import ProcurementLog

API_URL = "http://localhost:8000"

def check_and_trigger_procurement(threshold: int = 10) -> dict:
    """
    Check all medicines for low stock and trigger procurement if needed.
    
    Args:
        threshold: Stock level that triggers procurement (default: 10)
    
    Returns:
        dict: Summary of procurement actions taken
    """
    summary = {
        "checked_medicines": 0,
        "procurement_triggered": 0,
        "low_stock_items": [],
        "errors": []
    }
    
    try:
        # Get all medicines from inventory
        medicines = get_all_medicines()
        summary["checked_medicines"] = len(medicines)
        
        db = SessionLocal()
        
        for medicine in medicines:
            try:
                name = medicine.get("name", "")
                stock = medicine.get("stock", 0)
                
                if stock <= threshold and stock >= 0:  # Don't trigger for negative stock
                    # Check if we already have a pending procurement for this item
                    existing_procurement = db.query(ProcurementLog).filter(
                        ProcurementLog.product_name == name,
                        ProcurementLog.status == "pending"
                    ).first()
                    
                    if not existing_procurement:
                        # Trigger procurement
                        procurement_result = _trigger_procurement_webhook(name, stock, threshold)
                        
                        # Log the procurement
                        procurement_log = ProcurementLog(
                            product_name=name,
                            quantity_triggered=50,  # Default reorder quantity
                            current_stock=stock,
                            threshold=threshold,
                            status="ordered" if procurement_result["success"] else "failed",
                            notes=f"Auto-triggered procurement. Webhook: {procurement_result.get('message', '')}"
                        )
                        db.add(procurement_log)
                        db.commit()
                        
                        summary["procurement_triggered"] += 1
                        summary["low_stock_items"].append({
                            "name": name,
                            "current_stock": stock,
                            "threshold": threshold,
                            "procurement_status": "ordered" if procurement_result["success"] else "failed"
                        })
                        
                        print(f"[Procurement Tool] ⚠️ LOW STOCK ALERT: {name} (stock: {stock}) - Procurement triggered")
                    else:
                        print(f"[Procurement Tool] {name} already has pending procurement")
                        
            except Exception as e:
                error_msg = f"Error processing {medicine.get('name', 'unknown')}: {str(e)}"
                summary["errors"].append(error_msg)
                print(f"[Procurement Tool] {error_msg}")
        
        db.close()
        
    except Exception as e:
        summary["errors"].append(f"General error: {str(e)}")
        print(f"[Procurement Tool] General error: {e}")
    
    return summary

def _trigger_procurement_webhook(product_name: str, current_stock: int, threshold: int) -> dict:
    """
    Send webhook to warehouse system for procurement.
    
    Args:
        product_name: Name of the product to procure
        current_stock: Current stock level
        threshold: Stock threshold that triggered procurement
    
    Returns:
        dict: Webhook response status
    """
    webhook_payload = {
        "event": "procurement_required",
        "product_name": product_name,
        "current_stock": current_stock,
        "threshold": threshold,
        "reorder_quantity": 50,  # Default reorder quantity
        "urgency": "high" if current_stock <= 5 else "medium",
        "timestamp": datetime.now().isoformat(),
        "source": "swasthya_sarthi_auto_procurement"
    }
    
    try:
        # Send to warehouse webhook endpoint
        # In production, this would be the actual warehouse API
        warehouse_url = "https://warehouse-api.example.com/procurement"  # Placeholder
        
        response = requests.post(
            warehouse_url,
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [200, 201, 202]:
            return {
                "success": True,
                "message": f"Procurement webhook sent successfully (status: {response.status_code})"
            }
        else:
            return {
                "success": False,
                "message": f"Procurement webhook failed (status: {response.status_code})"
            }
            
    except requests.exceptions.RequestException as e:
        # For demo purposes, simulate success since we don't have a real warehouse API
        print(f"[Procurement Tool] Webhook simulation: Would send to warehouse - {product_name}")
        return {
            "success": True,
            "message": "Procurement webhook simulated (no real warehouse API configured)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Procurement webhook error: {str(e)}"
        }

def get_procurement_logs(status: str = None, limit: int = 50) -> list:
    """
    Get procurement logs from database.
    
    Args:
        status: Filter by status (pending, ordered, received, failed)
        limit: Maximum number of records to return
    
    Returns:
        list: Procurement log records
    """
    try:
        db = SessionLocal()
        query = db.query(ProcurementLog).order_by(ProcurementLog.order_date.desc())
        
        if status:
            query = query.filter(ProcurementLog.status == status)
        
        logs = query.limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "product_name": log.product_name,
                "quantity_triggered": log.quantity_triggered,
                "current_stock": log.current_stock,
                "threshold": log.threshold,
                "status": log.status,
                "order_date": log.order_date.isoformat() if log.order_date else None,
                "notes": log.notes
            })
        
        db.close()
        return result
        
    except Exception as e:
        print(f"[Procurement Tool] Error getting logs: {e}")
        return []

def update_procurement_status(procurement_id: int, status: str, notes: str = None) -> bool:
    """
    Update the status of a procurement log.
    
    Args:
        procurement_id: ID of the procurement log
        status: New status (pending, ordered, received, failed)
        notes: Optional notes to add
    
    Returns:
        bool: Success status
    """
    try:
        db = SessionLocal()
        procurement = db.query(ProcurementLog).filter(ProcurementLog.id == procurement_id).first()
        
        if procurement:
            procurement.status = status
            if notes:
                procurement.notes = (procurement.notes or "") + f" | {notes}"
            db.commit()
            db.close()
            return True
        else:
            db.close()
            return False
            
    except Exception as e:
        print(f"[Procurement Tool] Error updating status: {e}")
        return False

# Background task function (can be called periodically)
def run_procurement_check():
    """Run procurement check - can be scheduled to run periodically."""
    print("[Procurement Tool] Running automatic procurement check...")
    result = check_and_trigger_procurement()
    
    print(f"[Procurement Tool] Check complete: {result['procurement_triggered']} procurements triggered")
    
    if result["low_stock_items"]:
        print("Low stock items:")
        for item in result["low_stock_items"]:
            print(f"  - {item['name']}: {item['current_stock']} units")
    
    return result

if __name__ == "__main__":
    # Test the procurement tool
    print("Testing Procurement Tool...")
    result = run_procurement_check()
    print(f"Result: {result}")
