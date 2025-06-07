"""
Seed script to add sample data to the database.
"""
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Lead, Organization, User, LeadStatus, LeadSource
import datetime


def create_sample_data():
    """Create sample organizations, users, and leads for testing."""
    db = SessionLocal()
    
    try:
        # Create sample organization if it doesn't exist
        org = db.query(Organization).filter(Organization.id == 1).first()
        if not org:
            org = Organization(
                id=1,
                name="Sample Organization",
                slug="sample-organization",
                website="https://example.com",
                is_active=True,
                created_at=datetime.datetime.utcnow()
            )
            db.add(org)
            db.commit()
            db.refresh(org)
        
        # Create sample leads
        sample_leads = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "company": "Tech Corp",
                "job_title": "Software Engineer",
                "phone": "+1-555-0101",
                "status": LeadStatus.NEW,
                "source": LeadSource.WEBSITE,
                "organization_id": 1,
                "score": 75,
                "value": 5000  # $50.00 in cents
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "company": "Design Studio",
                "job_title": "UX Designer",
                "phone": "+1-555-0102",
                "status": LeadStatus.CONTACTED,
                "source": LeadSource.SOCIAL_MEDIA,
                "organization_id": 1,
                "score": 85,
                "value": 7500  # $75.00 in cents
            },
            {
                "first_name": "Mike",
                "last_name": "Johnson",
                "email": "mike.johnson@example.com",
                "company": "Marketing Inc",
                "job_title": "Marketing Manager",
                "phone": "+1-555-0103",
                "status": LeadStatus.QUALIFIED,
                "source": LeadSource.EMAIL,
                "organization_id": 1,
                "score": 90,
                "value": 12000  # $120.00 in cents
            },
            {
                "first_name": "Sarah",
                "last_name": "Williams",
                "email": "sarah.williams@example.com",
                "company": "Sales Solutions",
                "job_title": "Sales Director",
                "phone": "+1-555-0104",
                "status": LeadStatus.CLOSED_WON,
                "source": LeadSource.REFERRAL,
                "organization_id": 1,
                "score": 80,
                "value": 15000  # $150.00 in cents
            },
            {
                "first_name": "David",
                "last_name": "Brown",
                "email": "david.brown@example.com",
                "company": "Consulting Group",
                "job_title": "Business Consultant",
                "phone": "+1-555-0105",
                "status": LeadStatus.CONTACTED,
                "source": LeadSource.EVENT,
                "organization_id": 1,
                "score": 70,
                "value": 8000  # $80.00 in cents
            }
        ]
        
        # Check if leads already exist and add them if they don't
        for lead_data in sample_leads:
            existing_lead = db.query(Lead).filter(Lead.email == lead_data["email"]).first()
            if not existing_lead:
                lead = Lead(**lead_data)
                db.add(lead)
        
        db.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data() 