from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import Medicine, Order, Patient, RefillAlert
from .seed_loader import seed_data
from datetime import datetime, timedelta

# Initialize DB and seed data
Base.metadata.create_all(bind=engine)
seed_data()

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== MEDICINE ENDPOINTS ====================

@app.get("/medicine")
def get_medicine(name: str = None, db: Session = Depends(get_db)):
    """Return medicine info by name or all medicines."""
    if name:
        med = db.query(Medicine).filter(Medicine.name.ilike(f"%{name}%")).first()
        return med
    else:
        medicines = db.query(Medicine).all()
        return [{"id": m.id, "product_id": m.product_id, "name": m.name, "price": m.price, 
                 "stock": m.stock, "prescription_required": m.prescription_required,
                 "description": m.description, "package_size": m.package_size} for m in medicines]

@app.get("/medicines")
def get_all_medicines(db: Session = Depends(get_db)):
    """Return all medicines with stock info."""
    medicines = db.query(Medicine).all()
    return [{"id": m.id, "product_id": m.product_id, "name": m.name, "price": m.price, 
             "stock": m.stock, "prescription_required": m.prescription_required,
             "description": m.description, "package_size": m.package_size} for m in medicines]

@app.post("/create_order")
def create_order(patient_id: str, product_name: str, quantity: int, db: Session = Depends(get_db)):
    """Create an order, deducting stock."""
    med = db.query(Medicine).filter(Medicine.name == product_name).first()
    if not med or med.stock < quantity:
        return {"status": "failed", "reason": "out_of_stock_or_not_found"}
    med.stock -= quantity
    order = Order(patient_id=patient_id, product_name=product_name, quantity=quantity, status="CREATED")
    db.add(order)
    db.commit()
    return {"status": "success", "order_id": order.id, "price": round(med.price * quantity, 2)}

# ==================== PATIENT ENDPOINTS ====================

@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients."""
    patients = db.query(Patient).all()
    return [{"patient_id": p.patient_id, "name": p.name, "age": p.age, "gender": p.gender,
             "phone": p.phone, "email": p.email, "address": p.address, "language": p.language} for p in patients]

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient details by ID."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return {"error": "Patient not found"}
    return {"patient_id": patient.patient_id, "name": patient.name, "age": patient.age, 
            "gender": patient.gender, "phone": patient.phone, "email": patient.email, 
            "address": patient.address, "language": patient.language}

@app.get("/patients/{patient_id}/orders")
def get_patient_orders(patient_id: str, db: Session = Depends(get_db)):
    """Get order history for a patient."""
    orders = db.query(Order).filter(Order.patient_id == patient_id).order_by(Order.order_date.desc()).all()
    return [{"id": o.id, "product_name": o.product_name, "quantity": o.quantity, 
             "status": o.status, "order_date": o.order_date.isoformat() if o.order_date else None} for o in orders]

# ==================== REFILL ENDPOINTS ====================

@app.get("/check-refills")
def check_refills(days_ahead: int = Query(default=3, description="Days ahead to check for refills"), 
                  db: Session = Depends(get_db)):
    """Check for medicines that need refilling based on order history."""
    alerts = []
    now = datetime.now()
    
    # Get all patients
    patients = db.query(Patient).all()
    
    for patient in patients:
        # Get last order for each product for this patient
        orders = db.query(Order).filter(
            Order.patient_id == patient.patient_id
        ).order_by(Order.order_date.desc()).all()
        
        # Group by product and get most recent
        product_orders = {}
        for order in orders:
            if order.product_name not in product_orders:
                product_orders[order.product_name] = order
        
        for product_name, order in product_orders.items():
            # Get medicine details
            med = db.query(Medicine).filter(Medicine.name == product_name).first()
            if not med:
                continue
            
            # Calculate refill date (simplified - assumes 30 days supply)
            # In real app, would use dosage frequency from history
            days_since_order = (now - order.order_date).days if order.order_date else 0
            days_until_refill = 30 - days_since_order  # Assume 30 day supply
            
            if 0 <= days_until_refill <= days_ahead:
                alerts.append({
                    "patient_id": patient.patient_id,
                    "patient_name": patient.name,
                    "patient_phone": patient.phone,
                    "patient_email": patient.email,
                    "product_name": product_name,
                    "last_order_date": order.order_date.isoformat() if order.order_date else None,
                    "days_until_refill": days_until_refill,
                    "current_stock": med.stock
                })
    
    return {"alerts": alerts, "count": len(alerts)}

@app.post("/refill-alerts")
def create_refill_alert(patient_id: str, product_name: str, quantity: int, days_until_refill: int,
                        db: Session = Depends(get_db)):
    """Create a refill alert."""
    alert = RefillAlert(
        patient_id=patient_id,
        product_name=product_name,
        quantity=quantity,
        days_until_refill=days_until_refill,
        status="pending"
    )
    db.add(alert)
    db.commit()
    return {"status": "success", "alert_id": alert.id}

@app.get("/refill-alerts")
def get_refill_alerts(status: str = None, db: Session = Depends(get_db)):
    """Get all refill alerts, optionally filtered by status."""
    query = db.query(RefillAlert)
    if status:
        query = query.filter(RefillAlert.status == status)
    alerts = query.order_by(RefillAlert.alert_date.desc()).all()
    return [{"id": a.id, "patient_id": a.patient_id, "product_name": a.product_name,
             "quantity": a.quantity, "days_until_refill": a.days_until_refill,
             "alert_date": a.alert_date.isoformat(), "status": a.status} for a in alerts]

@app.put("/refill-alerts/{alert_id}")
def update_refill_alert(alert_id: int, status: str, db: Session = Depends(get_db)):
    """Update a refill alert status."""
    alert = db.query(RefillAlert).filter(RefillAlert.id == alert_id).first()
    if not alert:
        return {"error": "Alert not found"}
    alert.status = status
    db.commit()
    return {"status": "success"}

# ==================== ORDER ENDPOINTS ====================

@app.get("/orders")
def get_orders(patient_id: str = None, db: Session = Depends(get_db)):
    """Get all orders, optionally filtered by patient."""
    query = db.query(Order).order_by(Order.order_date.desc())
    if patient_id:
        query = query.filter(Order.patient_id == patient_id)
    orders = query.all()
    return [{"id": o.id, "patient_id": o.patient_id, "product_name": o.product_name,
             "quantity": o.quantity, "status": o.status, 
             "order_date": o.order_date.isoformat() if o.order_date else None} for o in orders]
