from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from datetime import datetime
from .database import Base

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True)
    name = Column(String, unique=True, index=True)
    pzn = Column(String)
    price = Column(Float)
    package_size = Column(String)
    description = Column(String)
    stock = Column(Integer, default=100)
    prescription_required = Column(Boolean, default=False)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String)
    product_name = Column(String)
    quantity = Column(Integer)
    status = Column(String)
    order_date = Column(DateTime, default=datetime.now)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    language = Column(String, default="en")

class RefillAlert(Base):
    __tablename__ = "refill_alerts"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    product_name = Column(String)
    quantity = Column(Integer)
    days_until_refill = Column(Integer)
    alert_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="pending")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
