#!/usr/bin/env python3
"""
Create test data for development environment.
"""
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import Organization, User, Lead, LeadStatus, LeadSource
from datetime import datetime, timedelta, timezone
import uuid

def create_test_data():
    """Create test data for development."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Organization).first():
            print("Test data already exists")
            return
        
        # Create test organization
        org = Organization(
            id=1,
            name="Test Organization",
            slug="test-org",
            description="Test organization for development",
            billing_email="test@example.com"
        )
        db.add(org)
        db.flush()
        
        # Create test user
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="$2b$12$test",  # placeholder
            is_active=True,
            organization_id=org.id
        )
        db.add(user)
        db.flush()
        
        # Create test leads
        sources = [LeadSource.WEBSITE, LeadSource.EMAIL, LeadSource.COLD_OUTREACH, LeadSource.SOCIAL_MEDIA]
        statuses = [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED, LeadStatus.PROPOSAL]
        
        for i in range(14):  # Create 14 leads to match our test data
            lead = Lead(
                id=i + 1,
                first_name=f"Lead {i+1}",
                last_name="Test",
                email=f"lead{i+1}@example.com",
                phone=f"555-{1000+i}",
                company=f"Company {i+1}",
                source=sources[i % len(sources)],
                status=statuses[i % len(statuses)],
                score=50 + (i * 3),
                value=(1000 + i * 500) * 100,  # in cents
                organization_id=org.id,
                assigned_to_id=user.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=i)
            )
            db.add(lead)
        
        db.commit()
        print("Test data created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 