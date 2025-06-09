#!/usr/bin/env python3
"""
Simple lead deletion script for LMA
Usage: python delete_lead_script.py <lead_id>
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def delete_lead(lead_id):
    """Delete a lead and all related records"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host="localhost",
            port="15432",
            database="lma_db",
            user="lma_user",
            password="lma_password"
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if lead exists
            cur.execute("SELECT id, email, first_name, last_name FROM leads WHERE id = %s", (lead_id,))
            lead = cur.fetchone()
            
            if not lead:
                print(f"❌ Lead with ID {lead_id} not found")
                return False
            
            print(f"🔍 Found lead: {lead['first_name']} {lead['last_name']} ({lead['email']})")
            
            # Delete related records first (foreign key constraints)
            print("🗑️ Deleting related records...")
            
            # Delete score history
            cur.execute("DELETE FROM lead_score_history WHERE lead_id = %s", (lead_id,))
            score_deleted = cur.rowcount
            print(f"   - Deleted {score_deleted} score history records")
            
            # Delete activity logs
            cur.execute("DELETE FROM activity_logs WHERE lead_id = %s", (lead_id,))
            activity_deleted = cur.rowcount
            print(f"   - Deleted {activity_deleted} activity log records")
            
            # Delete the lead
            cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
            lead_deleted = cur.rowcount
            
            if lead_deleted > 0:
                conn.commit()
                print(f"✅ Successfully deleted lead {lead_id}")
                return True
            else:
                print(f"❌ Failed to delete lead {lead_id}")
                return False
                
    except Exception as e:
        print(f"❌ Error deleting lead: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_lead_script.py <lead_id>")
        sys.exit(1)
    
    try:
        lead_id = int(sys.argv[1])
        success = delete_lead(lead_id)
        sys.exit(0 if success else 1)
    except ValueError:
        print("Error: Lead ID must be a valid integer")
        sys.exit(1) 