from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import Base, engine, SessionLocal
from .models import Medicine, Order, Patient, RefillAlert, User
from .seed_loader import seed_data
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.webhook_tool import send_order_confirmation_email

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against security rules.
    Returns (is_valid, error_message)
    """
    if len(password) < 4:
        return False, "Password must be at least 4 characters long"
    return True, ""

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Initialize DB and seed data
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Seed data disabled - uncomment if needed
# try:
#     seed_data()
# except Exception as e:
#     print(f"Warning: Could not seed data: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure the current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

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
    
    # Get patient info for email
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    med.stock -= quantity
    order = Order(patient_id=patient_id, product_name=product_name, quantity=quantity, status="CREATED")
    db.add(order)
    db.commit()
    
    # Send order confirmation email if patient has email
    if patient and patient.email:
        order_details = {
            "order_id": order.id,
            "date": datetime.now().isoformat(),
            "items": [{"name": product_name, "quantity": quantity, "price": med.price}],
            "total": round(med.price * quantity, 2),
            "address": patient.address or "N/A",
            "customer_email": patient.email
        }
        send_order_confirmation_email(patient.email, order_details)
    
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
            days_since_order = (now - order.order_date).days if order.order_date else 0
            days_until_refill = 30 - days_since_order
            
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

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(email: str, password: str, full_name: str = None, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    # Validate password strength
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Simple hash for testing - store password directly (not recommended for production)
    hashed_password = password  # Using plain password for testing
    
    # Create new user (regular user by default)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User registered successfully", "user_id": user.id, "email": user.email}

@app.post("/register-admin", status_code=status.HTTP_201_CREATED)
def register_admin(email: str, password: str, full_name: str = None, db: Session = Depends(get_db)):
    """Register a new admin user."""
    # Validate password strength
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = password
    
    # Create new admin user
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "Admin user registered successfully", "user_id": user.id, "email": user.email}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or form_data.password != user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

# ==================== ADMIN ENDPOINTS ====================

@app.get("/admin/users")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """Get all users (admin only)."""
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name,
             "is_active": u.is_active, "is_admin": u.is_admin,
             "created_at": u.created_at.isoformat() if u.created_at else None} for u in users]

@app.put("/admin/users/{user_id}/make-admin")
def make_user_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """Make a user an admin (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    return {"message": f"User {user.email} is now an admin"}

@app.put("/admin/users/{user_id}/remove-admin")
def remove_user_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """Remove admin privileges from a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = False
    db.commit()
    return {"message": f"Admin privileges removed from {user.email}"}

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
