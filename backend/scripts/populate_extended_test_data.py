#!/usr/bin/env python3
"""
Extended Test Data Population Script for LMA Database

This script populates the database with comprehensive test data including all entities.
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

def create_workflows(session, organizations, users, count=5):
    """Create test workflows"""
    print(f"⚡ Creating {count} test workflows...")
    
    workflows = []
    workflow_categories = ['lead_nurturing', 'follow_up', 'qualification', 'onboarding', 'renewal']
    trigger_types = ['manual', 'scheduled', 'event_based', 'lead_status_change']
    
    for i in range(count):
        org = random.choice(organizations)
        created_by = random.choice([u for u in users if u.organization_id == org.id])
        
        workflow = Workflow(
            organization_id=org.id,
            n8n_workflow_id=f"wf_{fake.uuid4()}",
            name=f"{random.choice(['Email', 'LinkedIn', 'Call', 'Follow-up', 'Welcome'])} {random.choice(['Sequence', 'Campaign', 'Flow', 'Automation'])}",
            description=fake.text(max_nb_chars=200),
            category=random.choice(workflow_categories),
            trigger_type=random.choice(trigger_types),
            trigger_conditions={
                "lead_status": random.choice([status.value for status in LeadStatus]),
                "score_threshold": random.randint(10, 80),
                "days_since_contact": random.randint(1, 14)
            },
            configuration={
                "steps": random.randint(3, 8),
                "delay_hours": random.randint(1, 72),
                "personalization_enabled": True
            },
            is_active=random.choice([True, False]),
            created_by=created_by.id
        )
        session.add(workflow)
        workflows.append(workflow)
    
    session.commit()
    print(f"✅ Created {len(workflows)} workflows")
    return workflows

def create_campaigns(session, organizations, users, count=4):
    """Create test campaigns"""
    print(f"📢 Creating {count} test campaigns...")
    
    campaigns = []
    campaign_types = ['email', 'cold_outreach', 'content', 'social', 'event']
    
    for i in range(count):
        org = random.choice(organizations)
        created_by = random.choice([u for u in users if u.organization_id == org.id])
        
        start_date = fake.date_between(start_date='-30d', end_date='today')
        end_date = fake.date_between(start_date=start_date, end_date='+90d')
        
        campaign = Campaign(
            organization_id=org.id,
            name=f"{fake.catch_phrase()} {random.choice(['Campaign', 'Initiative', 'Drive', 'Program'])}",
            description=fake.text(max_nb_chars=300),
            campaign_type=random.choice(campaign_types),
            status=random.choice([status for status in CampaignStatus]),
            target_criteria={
                "industry": random.choice(['Technology', 'Healthcare', 'Finance']),
                "company_size": random.choice(["11-50", "51-200", "201-1000"]),
                "score_min": random.randint(20, 50)
            },
            start_date=start_date,
            end_date=end_date,
            budget_allocated=random.randint(5000, 50000) * 100,  # in cents
            budget_spent=random.randint(1000, 25000) * 100,  # in cents
            goals={
                "target_leads": random.randint(50, 500),
                "conversion_rate": random.randint(5, 25),
                "roi_target": random.randint(200, 500)
            },
            created_by=created_by.id
        )
        session.add(campaign)
        campaigns.append(campaign)
    
    session.commit()
    print(f"✅ Created {len(campaigns)} campaigns")
    return campaigns

def create_communications(session, leads, users, count=15):
    """Create test communications"""
    print(f"💬 Creating {count} test communications...")
    
    communications = []
    subjects = [
        "Follow up on our conversation",
        "Proposal for your review",
        "Quick question about your needs",
        "Introducing our new solution",
        "Thank you for your time today"
    ]
    
    for i in range(count):
        lead = random.choice(leads)
        user = random.choice([u for u in users if u.organization_id == lead.organization_id])
        
        comm_type = random.choice([ct for ct in CommunicationType])
        direction = random.choice([cd for cd in CommunicationDirection])
        
        scheduled_at = fake.date_time_between(start_date='-7d', end_date='+7d')
        completed_at = scheduled_at + timedelta(minutes=random.randint(5, 60)) if random.choice([True, False]) else None
        
        communication = Communication(
            lead_id=lead.id,
            user_id=user.id,
            communication_type=comm_type,
            direction=direction,
            subject=random.choice(subjects) if comm_type == CommunicationType.EMAIL else None,
            content=fake.text(max_nb_chars=500),
            status=random.choice([cs for cs in CommunicationStatus]),
            scheduled_at=scheduled_at,
            completed_at=completed_at,
            comm_metadata={
                "duration_minutes": random.randint(5, 60) if comm_type == CommunicationType.CALL else None,
                "response_received": random.choice([True, False]),
                "sentiment": random.choice(['positive', 'neutral', 'negative'])
            }
        )
        session.add(communication)
        communications.append(communication)
    
    session.commit()
    print(f"✅ Created {len(communications)} communications")
    return communications

def create_lead_notes(session, leads, users, count=20):
    """Create test lead notes"""
    print(f"📝 Creating {count} test lead notes...")
    
    notes = []
    note_types = ['general', 'meeting', 'call', 'research', 'reminder']
    
    for i in range(count):
        lead = random.choice(leads)
        user = random.choice([u for u in users if u.organization_id == lead.organization_id])
        
        note = LeadNote(
            lead_id=lead.id,
            user_id=user.id,
            note_type=random.choice(note_types),
            content=fake.text(max_nb_chars=300),
            is_private=random.choice([True, False]),
            mentioned_users=[random.choice([u.id for u in users if u.organization_id == lead.organization_id])] if random.choice([True, False]) else [],
            attachments=[]
        )
        session.add(note)
        notes.append(note)
    
    session.commit()
    print(f"✅ Created {len(notes)} lead notes")
    return notes

def create_lead_scoring_rules(session, organizations, count=8):
    """Create test lead scoring rules"""
    print(f"📊 Creating {count} test lead scoring rules...")
    
    rules = []
    rule_types = ['demographic', 'behavioral', 'engagement', 'firmographic']
    
    for i in range(count):
        org = random.choice(organizations)
        
        rule = LeadScoringRule(
            organization_id=org.id,
            name=f"{random.choice(['High Value', 'Enterprise', 'Hot Lead', 'Qualified', 'Engaged'])} Rule",
            description=fake.text(max_nb_chars=150),
            rule_type=random.choice(rule_types),
            criteria={
                "field": random.choice(['job_title', 'company_size', 'industry', 'engagement_score']),
                "operator": random.choice(['equals', 'contains', 'greater_than', 'in']),
                "value": random.choice(['CEO', 'Director', 'Manager', '100+', 'Technology'])
            },
            score_points=random.randint(5, 25),
            is_active=True,
            priority=random.randint(1, 5)
        )
        session.add(rule)
        rules.append(rule)
    
    session.commit()
    print(f"✅ Created {len(rules)} lead scoring rules")
    return rules

def create_integrations(session, organizations, users, count=6):
    """Create test integrations"""
    print(f"🔗 Creating {count} test integrations...")
    
    integrations = []
    integration_types = ['crm', 'email_provider', 'social', 'calendar', 'analytics']
    providers = {
        'crm': ['salesforce', 'hubspot', 'pipedrive'],
        'email_provider': ['gmail', 'outlook', 'sendgrid'],
        'social': ['linkedin', 'twitter', 'facebook'],
        'calendar': ['google_calendar', 'outlook_calendar'],
        'analytics': ['google_analytics', 'mixpanel']
    }
    
    for i in range(count):
        org = random.choice(organizations)
        created_by = random.choice([u for u in users if u.organization_id == org.id])
        
        int_type = random.choice(integration_types)
        provider = random.choice(providers[int_type])
        
        integration = Integration(
            organization_id=org.id,
            integration_type=int_type,
            provider_name=provider,
            display_name=f"{provider.title()} Integration",
            configuration={
                "api_key": f"fake_key_{fake.uuid4()}",
                "endpoint": f"https://api.{provider}.com",
                "sync_enabled": True
            },
            status=random.choice([status for status in IntegrationStatus]),
            last_sync_at=fake.date_time_between(start_date='-1d', end_date='now') if random.choice([True, False]) else None,
            sync_frequency_minutes=random.choice([15, 30, 60, 120]),
            error_message=fake.text(max_nb_chars=100) if random.choice([True, False]) else None,
            created_by=created_by.id
        )
        session.add(integration)
        integrations.append(integration)
    
    session.commit()
    print(f"✅ Created {len(integrations)} integrations")
    return integrations

def main():
    """Main function to populate extended test data"""
    print("🚀 Starting LMA Extended Test Data Population")
    print("=" * 50)
    
    try:
        # Create database session
        session = create_test_session()
        
        # Get existing data
        organizations = session.query(Organization).all()
        users = session.query(User).all()
        leads = session.query(Lead).all()
        
        if not organizations or not users or not leads:
            print("❌ Basic data not found. Please run populate_test_data_local.py first!")
            return
        
        print(f"📋 Found existing data: {len(organizations)} orgs, {len(users)} users, {len(leads)} leads")
        
        # Create extended test data
        workflows = create_workflows(session, organizations, users, count=5)
        campaigns = create_campaigns(session, organizations, users, count=4)
        communications = create_communications(session, leads, users, count=15)
        notes = create_lead_notes(session, leads, users, count=20)
        rules = create_lead_scoring_rules(session, organizations, count=8)
        integrations = create_integrations(session, organizations, users, count=6)
        
        print("\n" + "=" * 50)
        print("🎉 Extended Test Data Population Complete!")
        print("=" * 50)
        print("📊 Extended Data Summary:")
        print(f"  workflows: {len(workflows)} records")
        print(f"  campaigns: {len(campaigns)} records") 
        print(f"  communications: {len(communications)} records")
        print(f"  lead_notes: {len(notes)} records")
        print(f"  lead_scoring_rules: {len(rules)} records")
        print(f"  integrations: {len(integrations)} records")
        
        print("\n✅ Database is ready for comprehensive testing!")
        
    except Exception as e:
        print(f"❌ Error during extended data population: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 