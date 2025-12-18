#!/usr/bin/env python3
"""Reset database schema - drops all tables and recreates from models."""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, MetaData

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from shared.database.models import Base

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech")

def reset_database():
    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    print("Dropping all tables...")
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)
    print("All tables dropped.")

    print("Creating new schema from models...")
    Base.metadata.create_all(bind=engine)
    print("Schema created successfully!")

if __name__ == "__main__":
    reset_database()
