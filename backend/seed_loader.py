import pandas as pd
from .database import SessionLocal
from .models import Medicine, Patient, Order
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def seed_data():
    db = SessionLocal()

    # Load Medicine Master (products-export.xlsx)
    products = pd.read_excel("data/products-export.xlsx")
    # Drop duplicates based on product name to avoid UNIQUE constraint errors
    products = products.drop_duplicates(subset=["product name"], keep="first")
    for _, row in products.iterrows():
        # Check if medicine already exists
        existing = db.query(Medicine).filter(Medicine.name == row["product name"]).first()
        if existing:
            continue  # Skip if already exists
        
        med = Medicine(
            product_id=int(row["product id"]),
            name=row["product name"],
            pzn=str(row["pzn"]),
            price=float(row["price rec"]) if not pd.isna(row["price rec"]) else 0.0,
            package_size=str(row["package size"]),
            description=str(row["descriptions"]),
            stock=100,
            prescription_required=False
        )
        db.add(med)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            continue
    db.commit()


    # Load Consumer Order History (skip header rows)
    history = pd.read_excel("data/Consumer Order History 1.xlsx", skiprows=4)
    history.columns = [
        "Patient ID", "Patient Age", "Patient Gender",
        "Purchase Date", "Product Name", "Quantity",
        "Total Price (EUR)", "Dosage Frequency", "Prescription Required"
    ]
    
    # Flag prescription requirements from history
    for _, row in history.iterrows():
        prod_name = row["Product Name"]
        pres_flag = str(row["Prescription Required"]).strip().lower()
        if pres_flag == "yes":
            med = db.query(Medicine).filter(Medicine.name == prod_name).first()
            if med:
                med.prescription_required = True
    db.commit()
    
    # Seed patients and orders from history
    seed_patients_and_orders(db, history)
    
    db.close()


def update_existing_patients(db, history_df):
    """Update existing patients with age and gender from history data."""
    try:
        # Get unique patients from history
        patient_ids = history_df["Patient ID"].dropna().unique()
        
        # Patient name mapping
        patient_data_map = {
            "PAT001": {"name": "Ramesh Kumar", "phone": "+919876543210", "email": "ramesh.kumar@example.com", "address": "Mumbai, Maharashtra", "language": "en"},
            "PAT002": {"name": "Sunita Devi", "phone": "+919876543211", "email": "sunita.devi@example.com", "address": "Delhi, NCR", "language": "hi"},
            "PAT003": {"name": "Amit Singh", "phone": "+919876543212", "email": "amit.singh@example.com", "address": "Pune, Maharashtra", "language": "en"},
            "PAT004": {"name": "Priya Sharma", "phone": "+919876543213", "email": "priya.sharma@example.com", "address": "Bangalore, Karnataka", "language": "en"},
            "PAT005": {"name": "Vijay Patel", "phone": "+919876543214", "email": "vijay.patel@example.com", "address": "Ahmedabad, Gujarat", "language": "gu"},
            "PAT006": {"name": "Lakshmi Nair", "phone": "+919876543215", "email": "lakshmi.nair@example.com", "address": "Kochi, Kerala", "language": "ml"},
            "PAT007": {"name": "Arun Joshi", "phone": "+919876543216", "email": "arun.joshi@example.com", "address": "Jaipur, Rajasthan", "language": "hi"},
            "PAT008": {"name": "Meera Gupta", "phone": "+919876543217", "email": "meera.gupta@example.com", "address": "Kolkata, West Bengal", "language": "bn"},
            "PAT009": {"name": "Suresh Reddy", "phone": "+919876543218", "email": "suresh.reddy@example.com", "address": "Chennai, Tamil Nadu", "language": "en"},
            "PAT010": {"name": "Anita Desai", "phone": "+919876543219", "email": "anita.desai@example.com", "address": "Surat, Gujarat", "language": "gu"},
        }
        
        updated_count = 0
        for patient_id in patient_ids:
            if pd.isna(patient_id):
                continue
            patient_id = str(patient_id).strip()
            
            # Get patient from database
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                continue
            
            # Get age and gender from history
            patient_rows = history_df[history_df["Patient ID"] == patient_id]
            if len(patient_rows) > 0:
                patient_row = patient_rows.iloc[0]
                age = int(patient_row["Patient Age"]) if not pd.isna(patient_row["Patient Age"]) else patient.age
                gender_raw = str(patient_row["Patient Gender"]) if not pd.isna(patient_row["Patient Gender"]) else patient.gender
                
                # Normalize gender to full form (swapped - dataset has F=Male, M=Female)
                gender_map = {"M": "Female", "F": "Male", "Male": "Male", "Female": "Female", "m": "Female", "f": "Male"}
                gender = gender_map.get(gender_raw.strip(), gender_raw)
                
                # Update patient data
                patient.age = age
                patient.gender = gender
                
                # Update other details if available in mapping
                data = patient_data_map.get(patient_id, {})
                if data:
                    patient.name = data.get("name", patient.name)
                    patient.phone = data.get("phone", patient.phone)
                    patient.email = data.get("email", patient.email)
                    patient.address = data.get("address", patient.address)
                    patient.language = data.get("language", patient.language)
                
                updated_count += 1
        
        db.commit()
        print(f"Updated {updated_count} patients with age and gender from history!")
        
    except Exception as e:
        print(f"Error updating patients: {e}")
        db.rollback()


def seed_patients_and_orders(db, history_df, force_update=False):
    """Load patients and orders from the consumer history DataFrame."""
    try:
        # Check if patients already exist
        existing_patients = db.query(Patient).count()
        if existing_patients > 0 and not force_update:
            print(f"Patients already seeded ({existing_patients} found), updating with latest data...")
            update_existing_patients(db, history_df)
            return
            
        # Get unique patients from history
        patient_ids = history_df["Patient ID"].dropna().unique()
        
        # Create realistic patient data based on history
        # Map Patient IDs to realistic Indian names
        patient_data_map = {
            "PAT001": {"name": "Ramesh Kumar", "age": 45, "gender": "Male", "phone": "+919876543210", "email": "ramesh.kumar@example.com", "address": "Mumbai, Maharashtra", "language": "en"},
            "PAT002": {"name": "Sunita Devi", "age": 62, "gender": "Female", "phone": "+919876543211", "email": "sunita.devi@example.com", "address": "Delhi, NCR", "language": "hi"},
            "PAT003": {"name": "Amit Singh", "age": 38, "gender": "Male", "phone": "+919876543212", "email": "amit.singh@example.com", "address": "Pune, Maharashtra", "language": "en"},
            "PAT004": {"name": "Priya Sharma", "age": 55, "gender": "Female", "phone": "+919876543213", "email": "priya.sharma@example.com", "address": "Bangalore, Karnataka", "language": "en"},
            "PAT005": {"name": "Vijay Patel", "age": 29, "gender": "Male", "phone": "+919876543214", "email": "vijay.patel@example.com", "address": "Ahmedabad, Gujarat", "language": "gu"},
            "PAT006": {"name": "Lakshmi Nair", "age": 35, "gender": "Female", "phone": "+919876543215", "email": "lakshmi.nair@example.com", "address": "Kochi, Kerala", "language": "ml"},
            "PAT007": {"name": "Arun Joshi", "age": 48, "gender": "Male", "phone": "+919876543216", "email": "arun.joshi@example.com", "address": "Jaipur, Rajasthan", "language": "hi"},
            "PAT008": {"name": "Meera Gupta", "age": 42, "gender": "Female", "phone": "+919876543217", "email": "meera.gupta@example.com", "address": "Kolkata, West Bengal", "language": "bn"},
            "PAT009": {"name": "Suresh Reddy", "age": 51, "gender": "Male", "phone": "+919876543218", "email": "suresh.reddy@example.com", "address": "Chennai, Tamil Nadu", "language": "en"},
            "PAT010": {"name": "Anita Desai", "age": 33, "gender": "Female", "phone": "+919876543219", "email": "anita.desai@example.com", "address": "Surat, Gujarat", "language": "gu"},
        }
        
        for patient_id in patient_ids:
            if pd.isna(patient_id):
                continue
            patient_id = str(patient_id).strip()
            
            # Get age and gender from history if available
            patient_row = history_df[history_df["Patient ID"] == patient_id].iloc[0]
            age = int(patient_row["Patient Age"]) if not pd.isna(patient_row["Patient Age"]) else 40
            gender = str(patient_row["Patient Gender"]) if not pd.isna(patient_row["Patient Gender"]) else "Unknown"
            
            # Use mapped data or create default
            data = patient_data_map.get(patient_id, {
                "name": f"Patient {patient_id}", "age": age, "gender": gender,
                "phone": "+919900000000", "email": f"{patient_id.lower()}@example.com",
                "address": "Unknown", "language": "en"
            })
            
            # Override with actual age/gender from history
            data["age"] = age
            data["gender"] = gender
            
            patient = Patient(
                patient_id=patient_id,
                name=data["name"],
                age=data["age"],
                gender=data["gender"],
                phone=data["phone"],
                email=data["email"],
                address=data["address"],
                language=data["language"]
            )
            db.add(patient)
        
        # Create orders from history
        orders_created = 0
        for _, row in history_df.iterrows():
            try:
                patient_id = row["Patient ID"]
                if pd.isna(patient_id):
                    continue
                    
                order = Order(
                    patient_id=str(patient_id).strip(),
                    product_name=row["Product Name"],
                    quantity=int(row["Quantity"]) if not pd.isna(row["Quantity"]) else 1,
                    status="DELIVERED",
                    order_date=pd.to_datetime(row["Purchase Date"])
                )
                db.add(order)
                orders_created += 1
            except Exception as e:
                print(f"Error adding order: {e}")
                continue
        
        db.commit()
        print(f"Seeded {len(patient_ids)} patients and {orders_created} orders successfully!")
        
    except Exception as e:
        print(f"Error seeding patients and orders: {e}")
        db.rollback()
