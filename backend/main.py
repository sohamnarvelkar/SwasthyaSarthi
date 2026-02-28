from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import Base, engine, SessionLocal
from .models import Medicine, Order, Patient, RefillAlert, User, ProcurementLog
from .seed_loader import seed_data
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import sys
import os
import tempfile
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
   , error_message)
 Returns (is_valid    """
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
        if med:
            return {"id": med.id, "product_id": med.product_id, "name": med.name, "price": med.price, 
                    "in_stock": med.stock > 0, "stock": med.stock, "prescription_required": med.prescription_required,
                    "description": med.description, "package_size": med.package_size}
        return None
    else:
        medicines = db.query(Medicine).all()
        return [{"id": m.id, "product_id": m.product_id, "name": m.name, "price": m.price, 
                 "in_stock": m.stock > 0, "stock": m.stock, "prescription_required": m.prescription_required,
                 "description": m.description, "package_size": m.package_size} for m in medicines]

@app.get("/medicines")
def get_all_medicines(db: Session = Depends(get_db)):
    """Return all medicines with stock info."""
    medicines = db.query(Medicine).all()
    return [{"id": m.id, "product_id": m.product_id, "name": m.name, "price": m.price, 
             "in_stock": m.stock > 0, "stock": m.stock, "prescription_required": m.prescription_required,
             "description": m.description, "package_size": m.package_size} for m in medicines]

@app.post("/create_order")
def create_order(patient_id: str, product_name: str, quantity: int, db: Session = Depends(get_db)):
    """Create an order, deducting stock. Price is fetched from dataset."""
    # Fetch medicine from database (price comes from products-export.xlsx)
    med = db.query(Medicine).filter(Medicine.name == product_name).first()
    
    # Validation: Medicine must exist
    if not med:
        return {"status": "failed", "reason": "medicine_not_found", "message": f"Medicine '{product_name}' not found in inventory"}
    
    # Validation: Price must be available from dataset
    if med.price is None or med.price <= 0:
        return {"status": "failed", "reason": "price_not_available", "message": f"Price not available for '{product_name}'. Cannot process order."}
    
    # Validation: Stock must be sufficient
    if med.stock < quantity:
        return {"status": "failed", "reason": "out_of_stock", "message": f"Insufficient stock for '{product_name}'. Available: {med.stock}, Requested: {quantity}"}
    
    # Calculate prices
    unit_price = med.price
    total_price = round(unit_price * quantity, 2)
    
    # Get patient info for email
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    # Deduct stock and create order with price details
    med.stock -= quantity
    order = Order(
        patient_id=patient_id, 
        product_name=product_name, 
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        status="CREATED"
    )
    db.add(order)
    db.commit()
    
    # Send order confirmation email if patient has email
    if patient and patient.email:
        order_details = {
            "order_id": order.id,
            "date": datetime.now().isoformat(),
            "items": [{"name": product_name, "quantity": quantity, "unit_price": unit_price, "total_price": total_price}],
            "unit_price": unit_price,
            "total_price": total_price,
            "address": patient.address or "N/A",
            "customer_email": patient.email
        }
        send_order_confirmation_email(patient.email, order_details)
    
    return {
        "status": "success", 
        "order_id": order.id, 
        "product_name": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price
    }


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
             "unit_price": o.unit_price, "total_price": o.total_price,
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
    
    # Send welcome/login notification email
    try:
        from tools.webhook_tool import send_login_notification_email
        email_result = send_login_notification_email(
            to_email=email,
            full_name=full_name,
            subject="Welcome to SwasthyaSarthi - Account Created!"
        )
        print(f"[Email] Login notification sent to {email}: {email_result}")
    except Exception as e:
        print(f"[Email] Failed to send login notification: {e}")
    
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
             "quantity": o.quantity, "unit_price": o.unit_price, "total_price": o.total_price,
             "status": o.status, 
             "order_date": o.order_date.isoformat() if o.order_date else None} for o in orders]


# ==================== PRESCRIPTION ENDPOINTS ====================

import base64
import uuid as uuid_module
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Prescription upload directory
PRESCRIPTION_DIR = tempfile.gettempdir() + "/swasthya_sarthi_prescriptions"
os.makedirs(PRESCRIPTION_DIR, exist_ok=True)


@app.post("/analyze-prescription")
async def analyze_prescription(
    file: UploadFile = File(...),
    language: str = Query("en", description="Language code: en, hi, mr")
):
    """
    Analyze a prescription image and extract medicines.
    
    Supports: jpg, jpeg, png, pdf
    
    Returns:
        JSON with detected medicines and confidence scores
    """
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
        content_type = file.content_type
        
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: jpg, jpeg, png, pdf"
            )
        
        # Read file content
        image_data = await file.read()
        
        # Check file size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB"
            )
        
        # Save prescription image
        file_ext = ".jpg" if content_type == "image/jpeg" else ".png"
        if content_type == "application/pdf":
            file_ext = ".pdf"
        
        prescription_filename = f"prescription_{uuid_module.uuid4().hex}{file_ext}"
        prescription_path = os.path.join(PRESCRIPTION_DIR, prescription_filename)
        
        with open(prescription_path, "wb") as f:
            f.write(image_data)
        
        print(f"[Prescription API] Saved: {prescription_filename}")
        
        # Perform OCR
        from backend.services.ocr_service import extract_prescription_text
        ocr_result = extract_prescription_text(image_data)
        
        if not ocr_result.get("success") or not ocr_result.get("text"):
            return JSONResponse({
                "success": False,
                "message": "Could not read prescription clearly. Please upload a clearer image.",
                "detected_medicines": [],
                "prescription_image": prescription_filename,
                "ocr_method": ocr_result.get("method", "none"),
                "ocr_confidence": ocr_result.get("confidence", 0)
            })
        
        # Extract and match medicines
        from agents.prescription_agent import process_prescription_direct
        processed = process_prescription_direct(
            ocr_text=ocr_result["text"],
            language=language
        )
        
        # Add prescription info to response
        processed["prescription_image"] = prescription_filename
        processed["ocr_method"] = ocr_result.get("method", "unknown")
        processed["ocr_confidence"] = ocr_result.get("confidence", 0)
        processed["ocr_text"] = ocr_result.get("text", "")[:500]  # First 500 chars
        
        print(f"[Prescription API] Found {len(processed['detected_medicines'])} medicines")
        
        return processed
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Prescription API] Error: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error processing prescription: {str(e)}",
            "detected_medicines": []
        })


@app.get("/prescriptions/{filename}")
async def get_prescription_image(filename: str):
    """Serve prescription images."""
    import fastapi
    
    prescription_path = os.path.join(PRESCRIPTION_DIR, filename)
    
    if not os.path.exists(prescription_path):
        raise HTTPException(status_code=404, detail="Prescription image not found")
    
    # Determine content type
    content_type = "image/jpeg"
    if filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif filename.endswith(".png"):
        content_type = "image/png"
    
    def iterfile():
        with open(prescription_path, mode="rb") as f:
            yield from f
    
    return fastapi.responses.StreamingResponse(
        iterfile(),
        media_type=content_type
    )


# ==================== PROCUREMENT ENDPOINTS ====================

@app.post("/auto-procurement")
def trigger_auto_procurement(threshold: int = Query(default=10, description="Stock threshold to trigger procurement")):
    """Trigger automatic procurement check for low stock items."""
    try:
        from tools.procurement_tool import check_and_trigger_procurement
        result = check_and_trigger_procurement(threshold=threshold)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/procurement-logs")
def get_procurement_logs(status: str = None, limit: int = 50):
    """Get procurement logs."""
    try:
        from tools.procurement_tool import get_procurement_logs
        logs = get_procurement_logs(status=status, limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        return {"error": str(e), "logs": []}

@app.put("/procurement-logs/{log_id}")
def update_procurement_log(log_id: int, status: str, notes: str = None):
    """Update procurement log status."""
    try:
        from tools.procurement_tool import update_procurement_status
        success = update_procurement_status(log_id, status, notes)
        return {"status": "success" if success else "failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== CHAT API ENDPOINTS ====================

import uuid
import hashlib
from datetime import datetime

# Audio cache directory
AUDIO_CACHE_DIR = tempfile.gettempdir() + "/swasthya_sarthi_audio"

# Ensure audio cache directory exists
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


def detect_language_from_text(text: str) -> str:
    """
    Detect language from text input.
    Uses simple script detection for multilingual support.
    """
    import re
    
    # Devanagari script detection (Hindi/Marathi)
    devanagari_range = r'[\u0900-\u097F]'
    if re.search(devanagari_range, text):
        # Simple keyword-based detection for Hindi vs Marathi
        hindi_common = ["है", "हैं", "मैं", "मुझे", "आप", "क्या", "हूँ", "जा", "के", "का", "को"]
        marathi_common = ["आहे", "मी", "मला", "तुम्ही", "काय", "आहे", "चे", "चा", "कोण"]
        
        hindi_count = sum(1 for word in hindi_common if word in text)
        marathi_count = sum(1 for word in marathi_common if word in text)
        
        if marathi_count > hindi_count:
            return "Marathi"
        return "Hindi"
    
    # Default to English for Latin script
    return "English"


def get_language_code(language: str) -> str:
    """Get ISO language code from language name."""
    code_map = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr"
    }
    return code_map.get(language, "en")


@app.post("/chat")
def chat_message(
    message: str = Query(..., description="User message"),
    user_id: str = Query("default"),
    user_email: str = Query("default@example.com"),
    language: str = Query(None),
    session_id: str = Query(None)
):
    """
    Chat API endpoint for text-based conversation.
    Uses fallback handler when LangGraph workflow fails.
    """
    print(f"[Chat API] Received message: {message}")
    
    # Auto-detect language if not provided
    if not language:
        detected = detect_language_from_text(message)
        language = detected
    
    lang_code = get_language_code(language)
    
    # Try the LangGraph workflow first
    try:
        # Create session ID if not provided
        if not session_id:
            session_id = f"{user_id}:{datetime.now().timestamp()}"
        
        # Import and run the agent graph
        from orchestration.graph import app_graph
        
        result = app_graph.invoke(
            {
                "user_input": message,
                "user_id": user_id,
                "user_email": user_email,
                "user_phone": None,
                "user_address": None,
                "user_language": lang_code,
                "detected_language": language,
                "session_id": session_id,
                "intent_type": "GENERAL_CHAT",
                "current_intent": "GENERAL_CHAT",
                "identified_symptoms": [],
                "possible_conditions": [],
                "medical_advice": "",
                "recommended_medicines": [],
                "structured_order": {},
                "safety_result": {},
                "final_response": "",
                "is_proactive": False,
                "refill_alerts": [],
                "requires_confirmation": False,
                "confirmation_message": "",
                "user_confirmed": None,
                "pending_order_details": None,
                "agent_trace": [],
                "is_order_request": True,
                "info_product": "",
                "info_response": "",
                "metadata": {
                    "agent_name": "chat_interface",
                    "action": "process_chat_input",
                    "language": language,
                    "interaction_mode": "chat",
                    "source": "frontend"
                }
            },
            config={"configurable": {"thread_id": session_id}}
        )
        
        response_text = result.get("final_response", "")
        
        # If we got a valid response, return it
        if response_text and len(response_text.strip()) > 0:
            requires_confirm = result.get("requires_confirmation", False)
            pending_details = result.get("pending_order_details")
            
            return {
                "text": response_text,
                "language": language,
                "requires_confirmation": requires_confirm,
                "pending_order": pending_details,
                "metadata": {
                    "mode": "chat",
                    "language": language,
                    "source": "frontend",
                    "intent": result.get("intent_type", "GENERAL_CHAT"),
                    "agent_trace": result.get("agent_trace", [])
                }
            }
        
    except Exception as e:
        print(f"[Chat API] LangGraph error: {e}")
    
    # Fallback to rule-based handler when LangGraph fails or returns empty
    try:
        from chat_fallback import process_message
        fallback_result = process_message(message, user_id, language)
        
        return {
            "text": fallback_result["text"],
            "language": language,
            "requires_confirmation": False,
            "pending_order": None,
            "metadata": {
                "mode": "chat",
                "language": language,
                "source": "fallback",
                "intent": fallback_result.get("intent", "UNKNOWN")
            }
        }
    except Exception as fallback_error:
        print(f"[Chat API] Fallback error: {fallback_error}")
        
        # Final fallback - return a simple response
        return {
            "text": "I didn't quite get that. Would you like to:\n\n🛒 Order medicines\n📋 Upload prescription\n📦 View your orders\n🔔 Check refill reminders\n\nPlease let me know how I can help!",
            "language": language or "English",
            "requires_confirmation": False,
            "pending_order": None,
            "metadata": {
                "mode": "chat",
                "language": language or "English",
                "source": "final_fallback",
                "intent": "FALLBACK"
            }
        }


@app.post("/voice")
def voice_message(
    transcript: str = Query(..., description="Voice transcript"),
    user_id: str = Query("default"),
    user_email: str = Query("default@example.com"),
    language: str = Query(None),
    session_id: str = Query(None)
):
    """
    Voice API endpoint for speech-based conversation.
    Returns both text and audio response.
    """
    try:
        # Auto-detect language if not provided
        if not language:
            detected = detect_language_from_text(transcript)
            language = detected
        
        lang_code = get_language_code(language)
        
        # Create session ID if not provided
        if not session_id:
            session_id = f"{user_id}:{datetime.now().timestamp()}"
        
        # Import and run the agent graph
        from orchestration.graph import app_graph
        
        result = app_graph.invoke(
            {
                "user_input": transcript,
                "user_id": user_id,
                "user_email": user_email,
                "user_phone": None,
                "user_address": None,
                "user_language": lang_code,
                "detected_language": language,
                "session_id": session_id,
                "intent_type": "GENERAL_CHAT",
                "current_intent": "GENERAL_CHAT",
                "identified_symptoms": [],
                "possible_conditions": [],
                "medical_advice": "",
                "recommended_medicines": [],
                "structured_order": {},
                "safety_result": {},
                "final_response": "",
                "is_proactive": False,
                "refill_alerts": [],
                "requires_confirmation": False,
                "confirmation_message": "",
                "user_confirmed": None,
                "pending_order_details": None,
                "agent_trace": [],
                "is_order_request": True,
                "info_product": "",
                "info_response": "",
                "metadata": {
                    "agent_name": "voice_interface",
                    "action": "process_voice_input",
                    "language": language,
                    "interaction_mode": "voice",
                    "source": "frontend"
                }
            },
            config={"configurable": {"thread_id": session_id}}
        )
        
        response_text = result.get("final_response", "")
        
        # Generate audio using ElevenLabs
        audio_url = None
        try:
            from backend.services.elevenlabs_service import generate_voice
            
            # Generate audio for the response
            audio_data = generate_voice(response_text, language)
            
            if audio_data:
                # Save audio to cache directory
                audio_filename = f"{uuid.uuid4().hex}.mp3"
                audio_path = os.path.join(AUDIO_CACHE_DIR, audio_filename)
                
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                
                audio_url = f"/audio/{audio_filename}"
        except Exception as tts_error:
            print(f"[TTS Error] {tts_error}")
            # Continue without audio if TTS fails
        
        requires_confirm = result.get("requires_confirmation", False)
        pending_details = result.get("pending_order_details")
        
        return {
            "text": response_text,
            "language": language,
            "audio_url": audio_url,
            "requires_confirmation": requires_confirm,
            "pending_order": pending_details,
            "metadata": {
                "mode": "voice",
                "language": language,
                "source": "frontend",
                "intent": result.get("intent_type", "GENERAL_CHAT"),
                "agent_trace": result.get("agent_trace", [])
            }
        }
        
    except Exception as e:
        print(f"[Voice API] LangGraph error: {e}")
    
    # Fallback to rule-based handler when LangGraph fails or returns empty
    try:
        from chat_fallback import process_message
        fallback_result = process_message(transcript, user_id, language)
        
        # Generate audio using ElevenLabs
        audio_url = None
        try:
            from backend.services.elevenlabs_service import generate_voice
            
            audio_data = generate_voice(fallback_result["text"], language)
            
            if audio_data:
                audio_filename = f"{uuid.uuid4().hex}.mp3"
                audio_path = os.path.join(AUDIO_CACHE_DIR, audio_filename)
                
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                
                audio_url = f"/audio/{audio_filename}"
        except Exception as tts_error:
            print(f"[TTS Error] {tts_error}")
        
        return {
            "text": fallback_result["text"],
            "language": language,
            "audio_url": audio_url,
            "requires_confirmation": False,
            "pending_order": None,
            "metadata": {
                "mode": "voice",
                "language": language,
                "source": "fallback",
                "intent": fallback_result.get("intent", "UNKNOWN")
            }
        }
    except Exception as fallback_error:
        print(f"[Voice API] Fallback error: {fallback_error}")
        
        # Final fallback - return a simple response
        return {
            "text": "I didn't quite get that. Would you like to:\n\n🛒 Order medicines\n📋 Upload prescription\n📦 View your orders\n🔔 Check refill reminders\n\nPlease let me know how I can help!",
            "language": language or "English",
            "audio_url": None,
            "requires_confirmation": False,
            "pending_order": None,
            "metadata": {
                "mode": "voice",
                "language": language or "English",
                "source": "final_fallback",
                "intent": "FALLBACK"
            }
        }


@app.get("/audio/{filename}")
def get_audio(filename: str):
    """Serve generated audio files."""
    import fastapi
    
    audio_path = os.path.join(AUDIO_CACHE_DIR, filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Return the audio file
    def iterfile():
        with open(audio_path, mode="rb") as f:
            yield from f
    
    return fastapi.responses.StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"inline; filename={filename}"
        }
    )


@app.get("/conversations/{user_id}")
def get_conversation_history(
    user_id: str,
    session_id: str = None,
    limit: int = 20
):
    """Get conversation history for a user."""
    try:
        from agents.conversation_memory import get_session, get_conversation_history
        
        if session_id:
            history = get_conversation_history(user_id, session_id, limit)
            return {"history": history, "session_id": session_id}
        else:
            # Get all sessions for user
            return {"history": [], "message": "Session ID required for now"}
    
    except Exception as e:
        return {"history": [], "error": str(e)}
