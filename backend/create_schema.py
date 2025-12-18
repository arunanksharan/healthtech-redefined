
import sys
import os
from pathlib import Path

# Add backend directory to python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from shared.database.connection import init_db, engine
from sqlalchemy import inspect

if __name__ == "__main__":
    print("Creating database schema...")
    try:
        init_db()
        print("Schema created successfully!")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {len(tables)}")
        # print(tables) # reduce noise

    except Exception as e:
        print(f"Error creating schema: {e}")
        sys.exit(1)
