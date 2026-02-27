#!/usr/bin/env python3
"""
Initialize database with new schema including price columns
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import Base, engine
from backend.seed_loader import seed_data

print("Creating database tables with new schema...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully")

print("\nSeeding data from products-export.xlsx...")
seed_data()
print("✅ Database seeded successfully")

print("\nDatabase initialization complete!")
