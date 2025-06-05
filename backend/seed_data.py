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
                domain="example.com",
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
                "score": 75
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "company": "Design Studio",
                "job_title": "UX Designer",
                "phone": "+1-555-0102",
                "status": LeadStatus.CONTACTED,
                "source": LeadSource.LINKEDIN,
                "organization_id": 1,
                "score": 85
            },
            {
                "first_name": "Mike",
                "last_name": "Johnson",
                "email": "mike.johnson@example.com",
                "company": "Marketing Inc",
                "job_title": "Marketing Manager",
                "phone": "+1-555-0103",
                "status": LeadStatus.QUALIFIED,
                "source": LeadSource.EMAIL_CAMPAIGN,
                "organization_id": 1,
                "score": 90
            },
            {
                "first_name": "Sarah",
                "last_name": "Williams",
                "email": "sarah.williams@example.com",
                "company": "Sales Solutions",
                "job_title": "Sales Director",
                "phone": "+1-555-0104",
                "status": LeadStatus.NEW,
                "source": LeadSource.REFERRAL,
                "organization_id": 1,
                "score": 80
            },
            {
                "first_name": "David",
                "last_name": "Brown",
                "email": "david.brown@example.com",
                "company": "Consulting Group",
                "job_title": "Business Consultant",
                "phone": "+1-555-0105",
                "status": LeadStatus.NURTURING,
                "source": LeadSource.WEBINAR,
                "organization_id": 1,
                "score": 70
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