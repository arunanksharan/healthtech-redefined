import sys
import os
from sqlalchemy import text, create_engine
from shared.database.connection import init_db

def force_reset():
    print("Forcing database reset...")
    
    # Create a dedicated engine with autocommit
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback for when running directly
        DATABASE_URL = "postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech"
        
    admin_engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    with admin_engine.connect() as conn:
        print("Dropping schema public cascade...")
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO healthtech;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        print("Schema reset complete.")

if __name__ == "__main__":
    try:
        force_reset()
        print("Re-initializing schema...")
        init_db()
        print("Database ready.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
