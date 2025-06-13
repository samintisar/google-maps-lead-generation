"""
Database initialization script.
Run this to create the database tables and optionally add sample data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import create_tables, reset_database
from app.db.models import *
from sqlalchemy.orm import sessionmaker
from app.db.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_sample_data():
    """Create sample data for testing."""
    db = SessionLocal()
    
    try:
        # Create sample organization
        org = Organization(
            name="Sample Organization",
            description="A sample organization for testing"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Create sample user
        user = User(
            organization_id=org.id,
            email="admin@example.com",
            name="Admin User",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create sample lead
        lead = Lead(
            organization_id=org.id,
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="Example Corp",
            status="new",
            source="website"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Create sample campaign
        campaign = Campaign(
            organization_id=org.id,
            name="Q1 Marketing Campaign",
            description="First quarter marketing campaign",
            status="active"
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        # Create sample activity
        activity = Activity(
            lead_id=lead.id,
            user_id=user.id,
            type="email",
            title="Welcome Email",
            description="Sent welcome email to new lead",
            status="completed"
        )
        db.add(activity)
        db.commit()
        
        print("Sample data created successfully!")
        print(f"Organization: {org.name} (ID: {org.id})")
        print(f"User: {user.name} (ID: {user.id})")
        print(f"Lead: {lead.name} (ID: {lead.id})")
        print(f"Campaign: {campaign.name} (ID: {campaign.id})")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function to initialize database."""
    print("Initializing database...")
    
    # Create tables
    create_tables()
    print("Database tables created successfully!")
    
    # Create sample data automatically (for Docker compatibility)
    print("Creating sample data...")
    create_sample_data()
    
    print("Database initialization complete!")


if __name__ == "__main__":
    main()