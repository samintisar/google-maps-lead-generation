import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import SessionLocal

def check_lead_data():
    """Check the actual data stored in the leads table."""
    db = SessionLocal()
    
    try:
        # Get the latest lead
        result = db.execute(text("SELECT * FROM leads ORDER BY id DESC LIMIT 1"))
        lead = result.fetchone()
        
        if lead:
            print("📊 Latest lead data from database:")
            # Get column names
            columns = result.keys()
            for i, column in enumerate(columns):
                print(f"  {column}: {lead[i]}")
        else:
            print("No leads found in database")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

def check_table_structure():
    """Check the current table structure."""
    db = SessionLocal()
    
    try:
        print("📋 Current leads table structure:")
        result = db.execute(text("PRAGMA table_info(leads)"))
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
    except Exception as e:
        print(f"Error checking table structure: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_table_structure()
    print()
    check_lead_data() 