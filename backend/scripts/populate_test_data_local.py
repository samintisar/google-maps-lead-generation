#!/usr/bin/env python3
"""
Local Test Data Population Script for LMA Database

This script populates the database with comprehensive test data using localhost connection.
"""

import sys
import os
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from faker import Faker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base
from models import (
    User, Organization, Lead, WorkflowExecution, ActivityLog,
    Workflow, LeadScoringRule, LeadScoreHistory, Communication,
    Campaign, CampaignLead, Integration, LeadNote, LeadAssignment,
    UserRole, LeadStatus, LeadSource, LeadTemperature,
    CommunicationType, CommunicationDirection, CommunicationStatus,
    CampaignStatus, IntegrationStatus
)
from auth import get_password_hash

# Initialize Faker for generating realistic test data
fake = Faker()

# Use localhost database URL
DATABASE_URL = "postgresql://lma_user:lma_password@localhost:5432/lma_db"

def create_test_session():
    """Create a database session for testing"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    return Session()

def clear_existing_data(session):
    """Clear existing data from all tables (for clean testing)"""
    print("🧹 Clearing existing test data...")
    
    try:
        session.execute(text("DELETE FROM activity_logs"))
        session.execute(text("DELETE FROM workflow_executions"))
        session.execute(text("DELETE FROM lead_score_history"))
        session.execute(text("DELETE FROM lead_notes"))
        session.execute(text("DELETE FROM lead_assignments"))
        session.execute(text("DELETE FROM communications"))
        session.execute(text("DELETE FROM campaign_leads"))
        session.execute(text("DELETE FROM campaigns"))
        session.execute(text("DELETE FROM lead_scoring_rules"))
        session.execute(text("DELETE FROM leads"))
        session.execute(text("DELETE FROM integrations"))
        session.execute(text("DELETE FROM workflows"))
        session.execute(text("DELETE FROM users"))
        session.execute(text("DELETE FROM organizations"))
        session.commit()
        print("✅ Existing data cleared")
    except Exception as e:
        print(f"⚠️  Warning during data clearing: {e}")
        session.rollback()

def create_organizations(session, count=3):
    """Create test organizations"""
    print(f"🏢 Creating {count} test organizations...")
    
    organizations = []
    for i in range(count):
        company_name = fake.company()
        slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '').replace('&', 'and')[:100]
        
        org = Organization(
            name=company_name,
            slug=f"{slug}-{i}",
            description=fake.text(max_nb_chars=200),
            website=fake.url() if random.choice([True, False]) else None,
            industry=random.choice(['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 'Consulting']),
            size=random.choice(['startup', 'small', 'medium', 'large', 'enterprise']),
            subscription_tier=random.choice(['free', 'basic', 'premium', 'enterprise']),
            billing_email=fake.company_email(),
            settings={
                "timezone": fake.timezone(),
                "currency": random.choice(["USD", "EUR", "GBP"]),
                "lead_scoring_enabled": True,
                "workflow_automation": True
            }
        )
        session.add(org)
        organizations.append(org)
    
    session.commit()
    print(f"✅ Created {len(organizations)} organizations")
    return organizations

def create_users(session, organizations, count=8):
    """Create test users across organizations"""
    print(f"👥 Creating {count} test users...")
    
    users = []
    for i in range(count):
        org = random.choice(organizations)
        first_name = fake.first_name()
        last_name = fake.last_name()
        user = User(
            email=fake.email(),
            username=f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}",
            hashed_password=get_password_hash("password123"),
            first_name=first_name,
            last_name=last_name,
            role=random.choice([UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES_REP, UserRole.VIEWER]),
            organization_id=org.id,
            timezone=fake.timezone(),
            preferences={
                "email_notifications": True,
                "dashboard_layout": "default",
                "lead_view_mode": "cards"
            },
            avatar_url=fake.image_url() if random.choice([True, False]) else None,
            is_active=True
        )
        session.add(user)
        users.append(user)
    
    session.commit()
    print(f"✅ Created {len(users)} users")
    return users

def create_leads(session, organizations, users, count=25):
    """Create test leads"""
    print(f"🎯 Creating {count} test leads...")
    
    leads = []
    
    for i in range(count):
        org = random.choice(organizations)
        assigned_user = random.choice([u for u in users if u.organization_id == org.id]) if random.choice([True, False]) else None
        
        lead = Lead(
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            company=fake.company(),
            job_title=fake.job(),
            phone=fake.phone_number(),
            source=random.choice([LeadSource.WEBSITE, LeadSource.EMAIL, LeadSource.SOCIAL_MEDIA, LeadSource.REFERRAL]),
            status=random.choice([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED, LeadStatus.PROPOSAL]),
            score=random.randint(0, 100),
            value=random.randint(1000, 50000) if random.choice([True, False]) else None,
            notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
            tags=json.dumps(random.sample(['enterprise', 'startup', 'smb', 'urgent', 'hot-lead', 'follow-up'], k=random.randint(0, 3))),
            custom_fields={
                "industry": fake.bs().split()[0],
                "company_size": random.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"]),
                "budget": random.choice(["< $10k", "$10k-$50k", "$50k-$100k", "> $100k"])
            },
            linkedin_url=f"https://linkedin.com/in/{fake.user_name()}" if random.choice([True, False]) else None,
            lead_temperature=random.choice([LeadTemperature.HOT, LeadTemperature.WARM, LeadTemperature.COLD]),
            expected_close_date=fake.date_between(start_date='today', end_date='+6M') if random.choice([True, False]) else None,
            last_engagement_date=fake.date_time_between(start_date='-30d', end_date='now') if random.choice([True, False]) else None,
            first_contacted_at=fake.date_time_between(start_date='-60d', end_date='-1d') if random.choice([True, False]) else None,
            last_contacted_at=fake.date_time_between(start_date='-7d', end_date='now') if random.choice([True, False]) else None,
            organization_id=org.id,
            assigned_to_id=assigned_user.id if assigned_user else None
        )
        session.add(lead)
        leads.append(lead)
    
    session.commit()
    print(f"✅ Created {len(leads)} leads")
    return leads

def validate_data_integrity(session):
    """Validate data integrity and relationships"""
    print("🔍 Validating data integrity...")
    
    validation_results = {}
    
    # Count records in each table
    validation_results['organizations'] = session.query(Organization).count()
    validation_results['users'] = session.query(User).count()
    validation_results['leads'] = session.query(Lead).count()
    
    # Test some relationships
    print("🔗 Testing relationships...")
    
    # Test user-organization relationship
    users_with_orgs = session.query(User).filter(User.organization_id.isnot(None)).count()
    print(f"  Users with organizations: {users_with_orgs}/{validation_results['users']}")
    
    # Test lead-user assignments
    assigned_leads = session.query(Lead).filter(Lead.assigned_to_id.isnot(None)).count()
    print(f"  Assigned leads: {assigned_leads}/{validation_results['leads']}")
    
    # Test enum constraints
    print("🎛️ Testing enum constraints...")
    
    # Test lead temperature enum
    temp_counts = {}
    for temp in [LeadTemperature.HOT, LeadTemperature.WARM, LeadTemperature.COLD]:
        count = session.query(Lead).filter(Lead.lead_temperature == temp).count()
        temp_counts[temp.value] = count
    print(f"  Lead temperatures: {temp_counts}")
    
    print("✅ Data integrity validation complete")
    return validation_results

def main():
    """Main function to populate test data"""
    print("🚀 Starting LMA Local Test Data Population")
    print("=" * 50)
    
    try:
        # Create database session
        session = create_test_session()
        
        # Clear existing data
        clear_existing_data(session)
        
        # Create test data in dependency order
        organizations = create_organizations(session, count=3)
        users = create_users(session, organizations, count=8)
        leads = create_leads(session, organizations, users, count=25)
        
        # Validate data integrity
        validation_results = validate_data_integrity(session)
        
        print("\n" + "=" * 50)
        print("🎉 Test Data Population Complete!")
        print("=" * 50)
        print("📊 Summary:")
        for table, count in validation_results.items():
            print(f"  {table}: {count} records")
        
        print("\n✅ Database is ready for testing!")
        
    except Exception as e:
        print(f"❌ Error during data population: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 