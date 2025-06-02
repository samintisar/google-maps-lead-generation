#!/usr/bin/env python3
"""
Test Data Population Script for LMA Database

This script populates the database with comprehensive test data to validate
the schema implementation and test all relationships and constraints.
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import (
    User, Organization, Lead, WorkflowExecution, ActivityLog,
    Workflow, LeadScoringRule, LeadScoreHistory, Communication,
    Campaign, CampaignLead, Integration, LeadNote, LeadAssignment
)
from config import settings

# Initialize Faker for generating realistic test data
fake = Faker()

def create_test_session():
    """Create a database session for testing"""
    engine = create_engine(settings.database_url)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    return Session()

def clear_existing_data(session):
    """Clear existing data from all tables (for clean testing)"""
    print("🧹 Clearing existing test data...")
    
    # Use raw SQL to avoid SQLAlchemy relationship issues
    try:
        session.execute("DELETE FROM activity_logs")
        session.execute("DELETE FROM workflow_executions")
        session.execute("DELETE FROM lead_score_history")
        session.execute("DELETE FROM lead_notes")
        session.execute("DELETE FROM lead_assignments")
        session.execute("DELETE FROM communications")
        session.execute("DELETE FROM campaign_leads")
        session.execute("DELETE FROM campaigns")
        session.execute("DELETE FROM lead_scoring_rules")
        session.execute("DELETE FROM leads")
        session.execute("DELETE FROM integrations")
        session.execute("DELETE FROM workflows")
        session.execute("DELETE FROM users")
        session.execute("DELETE FROM organizations")
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
            slug=f"{slug}-{i}",  # Add required slug field with unique suffix
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
            hashed_password=fake.password(),
            first_name=first_name,
            last_name=last_name,
            role=random.choice(['admin', 'manager', 'sales_rep', 'viewer']),
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
    lead_sources = ['WEBSITE', 'EMAIL', 'SOCIAL_MEDIA', 'REFERRAL', 'ADVERTISING', 'COLD_OUTREACH', 'EVENT', 'OTHER']
    lead_statuses = ['NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION', 'CLOSED_WON', 'CLOSED_LOST']
    temperatures = ['hot', 'warm', 'cold']
    
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
            source=random.choice(lead_sources),
            status=random.choice(lead_statuses),
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
            lead_temperature=random.choice(temperatures),
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

def create_workflows(session, organizations, users, count=5):
    """Create test workflows"""
    print(f"🔄 Creating {count} test workflows...")
    
    workflows = []
    categories = ['lead_nurturing', 'follow_up', 'scoring', 'assignment', 'notification']
    
    for i in range(count):
        org = random.choice(organizations)
        creator = random.choice([u for u in users if u.organization_id == org.id])
        
        workflow = Workflow(
            organization_id=org.id,
            n8n_workflow_id=f"wf_{fake.uuid4()}",
            name=f"{random.choice(['Email', 'Lead', 'Sales', 'Follow-up', 'Scoring'])} {fake.word().title()} Workflow",
            description=fake.text(max_nb_chars=150),
            category=random.choice(categories),
            trigger_type=random.choice(['webhook', 'schedule', 'manual', 'lead_created', 'lead_updated']),
            trigger_conditions={
                "lead_score_threshold": random.randint(50, 90),
                "lead_source": random.choice(['WEBSITE', 'EMAIL', 'REFERRAL']),
                "conditions": "score > 75 AND temperature = 'hot'"
            },
            configuration={
                "email_template": f"template_{i+1}",
                "delay_minutes": random.randint(5, 1440),
                "max_attempts": random.randint(1, 5)
            },
            is_active=random.choice([True, True, False]),  # 66% active
            created_by=creator.id
        )
        session.add(workflow)
        workflows.append(workflow)
    
    session.commit()
    print(f"✅ Created {len(workflows)} workflows")
    return workflows

def create_integrations(session, organizations, users, count=4):
    """Create test integrations"""
    print(f"🔌 Creating {count} test integrations...")
    
    integrations = []
    integration_types = ['email', 'crm', 'marketing', 'social']
    providers = ['mailchimp', 'salesforce', 'hubspot', 'linkedin', 'zapier']
    
    for i in range(count):
        org = random.choice(organizations)
        creator = random.choice([u for u in users if u.organization_id == org.id])
        
        integration = Integration(
            organization_id=org.id,
            integration_type=random.choice(integration_types),
            provider_name=random.choice(providers),
            display_name=f"{random.choice(providers).title()} Integration",
            configuration={
                "api_key": f"key_{fake.uuid4()}",
                "endpoint": f"https://api.{random.choice(providers)}.com/v1",
                "webhook_url": f"https://webhook.lma.com/{fake.uuid4()}"
            },
            status=random.choice(['active', 'active', 'inactive', 'error']),  # Mostly active
            last_sync_at=fake.date_time_between(start_date='-7d', end_date='now') if random.choice([True, False]) else None,
            sync_frequency_minutes=random.choice([15, 30, 60, 120, 1440]),
            error_message=fake.sentence() if random.choice([False, False, True]) else None,  # 33% have errors
            created_by=creator.id
        )
        session.add(integration)
        integrations.append(integration)
    
    session.commit()
    print(f"✅ Created {len(integrations)} integrations")
    return integrations

def create_lead_scoring_rules(session, organizations, count=8):
    """Create test lead scoring rules"""
    print(f"📊 Creating {count} test lead scoring rules...")
    
    rules = []
    rule_types = ['demographic', 'behavioral', 'firmographic', 'engagement']
    
    for i in range(count):
        org = random.choice(organizations)
        
        rule = LeadScoringRule(
            organization_id=org.id,
            name=f"{random.choice(['Email', 'Website', 'Company', 'Title', 'Engagement'])} Scoring Rule {i+1}",
            description=fake.text(max_nb_chars=100),
            rule_type=random.choice(rule_types),
            criteria={
                "field": random.choice(["email_domain", "company_size", "title", "source"]),
                "operator": random.choice(["contains", "equals", "starts_with"]),
                "value": random.choice(["@gmail.com", "CEO", "Manager", "Director"]),
                "condition": "if field contains value then add points"
            },
            score_points=random.choice([5, 10, 15, 20, 25, -5, -10]),
            is_active=random.choice([True, True, False]),  # 66% active
            priority=random.randint(1, 10)
        )
        session.add(rule)
        rules.append(rule)
    
    session.commit()
    print(f"✅ Created {len(rules)} lead scoring rules")
    return rules

def create_campaigns(session, organizations, users, count=6):
    """Create test campaigns"""
    print(f"📢 Creating {count} test campaigns...")
    
    campaigns = []
    campaign_types = ['email', 'cold_outreach', 'nurture', 'webinar', 'demo']
    statuses = ['draft', 'active', 'paused', 'completed', 'cancelled']
    
    for i in range(count):
        org = random.choice(organizations)
        creator = random.choice([u for u in users if u.organization_id == org.id])
        
        start_date = fake.date_between(start_date='-30d', end_date='+30d')
        end_date = fake.date_between(start_date=start_date, end_date=start_date + timedelta(days=90))
        
        campaign = Campaign(
            organization_id=org.id,
            name=f"{fake.catch_phrase()} Campaign",
            description=fake.text(max_nb_chars=200),
            campaign_type=random.choice(campaign_types),
            status=random.choice(statuses),
            target_criteria={
                "lead_score_min": random.randint(50, 80),
                "lead_temperature": random.choice(['hot', 'warm']),
                "source": random.choice(['WEBSITE', 'REFERRAL'])
            },
            start_date=start_date,
            end_date=end_date,
            budget_allocated=random.randint(1000, 10000) if random.choice([True, False]) else None,
            budget_spent=random.randint(0, 5000),
            goals={
                "target_leads": random.randint(50, 200),
                "target_conversion_rate": random.uniform(0.05, 0.15),
                "target_revenue": random.randint(10000, 100000)
            },
            created_by=creator.id
        )
        session.add(campaign)
        campaigns.append(campaign)
    
    session.commit()
    print(f"✅ Created {len(campaigns)} campaigns")
    return campaigns

def create_communications(session, leads, users, count=40):
    """Create test communications"""
    print(f"💬 Creating {count} test communications...")
    
    communications = []
    comm_types = ['email', 'call', 'meeting', 'linkedin', 'sms']
    directions = ['inbound', 'outbound']
    statuses = ['scheduled', 'completed', 'failed', 'cancelled']
    
    for i in range(count):
        lead = random.choice(leads)
        user = random.choice([u for u in users if u.organization_id == lead.organization_id]) if random.choice([True, False]) else None
        
        comm_type = random.choice(comm_types)
        direction = random.choice(directions)
        status = random.choice(statuses)
        
        # Generate appropriate subject and content based on type
        if comm_type == 'email':
            subject = fake.sentence(nb_words=6)
            content = fake.text(max_nb_chars=500)
        elif comm_type == 'call':
            subject = f"Call with {lead.first_name} {lead.last_name}"
            content = f"Duration: {random.randint(5, 60)} minutes. " + fake.text(max_nb_chars=200)
        elif comm_type == 'meeting':
            subject = f"Meeting: {fake.catch_phrase()}"
            content = fake.text(max_nb_chars=300)
        else:
            subject = None
            content = fake.text(max_nb_chars=160)
        
        scheduled_at = fake.date_time_between(start_date='-7d', end_date='+7d') if status in ['scheduled', 'cancelled'] else None
        completed_at = fake.date_time_between(start_date='-30d', end_date='now') if status == 'completed' else None
        
        communication = Communication(
            lead_id=lead.id,
            user_id=user.id if user else None,
            communication_type=comm_type,
            direction=direction,
            subject=subject,
            content=content,
            status=status,
            scheduled_at=scheduled_at,
            completed_at=completed_at,
            comm_metadata={
                "platform": comm_type,
                "duration_minutes": random.randint(5, 60) if comm_type in ['call', 'meeting'] else None,
                "response_time_hours": random.randint(1, 48) if direction == 'inbound' else None
            }
        )
        session.add(communication)
        communications.append(communication)
    
    session.commit()
    print(f"✅ Created {len(communications)} communications")
    return communications

def create_campaign_leads(session, campaigns, leads, count=30):
    """Create campaign-lead associations"""
    print(f"🎯 Creating {count} campaign-lead associations...")
    
    campaign_leads = []
    statuses = ['added', 'contacted', 'responded', 'converted', 'opted_out']
    
    for i in range(count):
        campaign = random.choice(campaigns)
        lead = random.choice([l for l in leads if l.organization_id == campaign.organization_id])
        
        # Avoid duplicates
        existing = session.query(CampaignLead).filter_by(campaign_id=campaign.id, lead_id=lead.id).first()
        if existing:
            continue
        
        added_at = fake.date_time_between(start_date=campaign.start_date, end_date='now')
        
        campaign_lead = CampaignLead(
            campaign_id=campaign.id,
            lead_id=lead.id,
            status=random.choice(statuses),
            added_at=added_at,
            last_contact_at=fake.date_time_between(start_date=added_at, end_date='now') if random.choice([True, False]) else None,
            response_at=fake.date_time_between(start_date=added_at, end_date='now') if random.choice([True, False]) else None,
            conversion_at=fake.date_time_between(start_date=added_at, end_date='now') if random.choice([False, False, True]) else None
        )
        session.add(campaign_lead)
        campaign_leads.append(campaign_lead)
    
    session.commit()
    print(f"✅ Created {len(campaign_leads)} campaign-lead associations")
    return campaign_leads

def create_lead_notes(session, leads, users, count=35):
    """Create test lead notes"""
    print(f"📝 Creating {count} test lead notes...")
    
    notes = []
    note_types = ['general', 'meeting', 'call', 'email', 'task', 'reminder']
    
    for i in range(count):
        lead = random.choice(leads)
        user = random.choice([u for u in users if u.organization_id == lead.organization_id])
        
        note = LeadNote(
            lead_id=lead.id,
            user_id=user.id,
            note_type=random.choice(note_types),
            content=fake.text(max_nb_chars=400),
            is_private=random.choice([False, False, True]),  # 33% private
            mentioned_users=[random.choice(users).id] if random.choice([False, True]) else [],
            attachments={
                "files": [f"document_{random.randint(1, 100)}.pdf"] if random.choice([False, False, True]) else [],
                "images": []
            }
        )
        session.add(note)
        notes.append(note)
    
    session.commit()
    print(f"✅ Created {len(notes)} lead notes")
    return notes

def create_lead_assignments(session, leads, users, count=15):
    """Create test lead assignments"""
    print(f"👤 Creating {count} test lead assignments...")
    
    assignments = []
    
    for i in range(count):
        lead = random.choice(leads)
        org_users = [u for u in users if u.organization_id == lead.organization_id]
        
        if len(org_users) < 2:
            continue
            
        assigned_from = random.choice(org_users)
        assigned_to = random.choice([u for u in org_users if u.id != assigned_from.id])
        assigned_by = random.choice(org_users)
        
        assignment = LeadAssignment(
            lead_id=lead.id,
            assigned_from=assigned_from.id,
            assigned_to=assigned_to.id,
            assigned_by=assigned_by.id,
            reason=random.choice([
                "Better territory match",
                "Expertise in this industry",
                "Workload balancing",
                "Client relationship",
                "Availability"
            ]),
            assigned_at=fake.date_time_between(start_date='-30d', end_date='now')
        )
        session.add(assignment)
        assignments.append(assignment)
    
    session.commit()
    print(f"✅ Created {len(assignments)} lead assignments")
    return assignments

def create_lead_score_history(session, leads, scoring_rules, count=50):
    """Create test lead score history"""
    print(f"📈 Creating {count} test lead score history entries...")
    
    score_history = []
    
    for i in range(count):
        lead = random.choice(leads)
        rule = random.choice(scoring_rules) if scoring_rules and random.choice([True, False]) else None
        
        previous_score = random.randint(0, 100)
        score_change = random.randint(-20, 25)
        new_score = max(0, min(100, previous_score + score_change))
        
        history = LeadScoreHistory(
            lead_id=lead.id,
            previous_score=previous_score,
            new_score=new_score,
            score_change=score_change,
            reason=random.choice([
                "Email opened",
                "Website visit",
                "Form submission",
                "Meeting scheduled",
                "Proposal requested",
                "Email bounced",
                "Unsubscribed"
            ]),
            rule_id=rule.id if rule else None,
            created_at=fake.date_time_between(start_date='-60d', end_date='now')
        )
        session.add(history)
        score_history.append(history)
    
    session.commit()
    print(f"✅ Created {len(score_history)} lead score history entries")
    return score_history

def create_activity_logs(session, leads, users, count=60):
    """Create test activity logs"""
    print(f"📋 Creating {count} test activity logs...")
    
    activities = []
    activity_types = ['lead_created', 'lead_updated', 'email_sent', 'call_made', 'meeting_scheduled', 'score_changed']
    
    for i in range(count):
        lead = random.choice(leads)
        user = random.choice([u for u in users if u.organization_id == lead.organization_id]) if random.choice([True, False]) else None
        
        activity_type = random.choice(activity_types)
        activity = ActivityLog(
            lead_id=lead.id,
            user_id=user.id if user else None,
            activity_type=activity_type,
            description=f"{activity_type.replace('_', ' ').title()} for {lead.first_name} {lead.last_name}",
            activity_metadata={
                "field_changed": random.choice(["status", "score", "temperature", "assigned_to"]),
                "old_value": fake.word(),
                "new_value": fake.word(),
                "ip_address": fake.ipv4(),
                "user_agent": fake.user_agent()
            },
            created_at=fake.date_time_between(start_date='-60d', end_date='now')
        )
        session.add(activity)
        activities.append(activity)
    
    session.commit()
    print(f"✅ Created {len(activities)} activity logs")
    return activities

def validate_data_integrity(session):
    """Validate data integrity and relationships"""
    print("🔍 Validating data integrity...")
    
    validation_results = {}
    
    # Count records in each table
    validation_results['organizations'] = session.query(Organization).count()
    validation_results['users'] = session.query(User).count()
    validation_results['leads'] = session.query(Lead).count()
    validation_results['workflows'] = session.query(Workflow).count()
    validation_results['integrations'] = session.query(Integration).count()
    validation_results['lead_scoring_rules'] = session.query(LeadScoringRule).count()
    validation_results['campaigns'] = session.query(Campaign).count()
    validation_results['communications'] = session.query(Communication).count()
    validation_results['campaign_leads'] = session.query(CampaignLead).count()
    validation_results['lead_notes'] = session.query(LeadNote).count()
    validation_results['lead_assignments'] = session.query(LeadAssignment).count()
    validation_results['lead_score_history'] = session.query(LeadScoreHistory).count()
    validation_results['workflow_executions'] = session.query(WorkflowExecution).count()
    validation_results['activity_logs'] = session.query(ActivityLog).count()
    
    # Test some relationships
    print("🔗 Testing relationships...")
    
    # Test user-organization relationship
    users_with_orgs = session.query(User).filter(User.organization_id.isnot(None)).count()
    print(f"  Users with organizations: {users_with_orgs}/{validation_results['users']}")
    
    # Test lead-user assignments
    assigned_leads = session.query(Lead).filter(Lead.assigned_to_id.isnot(None)).count()
    print(f"  Assigned leads: {assigned_leads}/{validation_results['leads']}")
    
    # Test campaign-lead associations
    campaign_lead_count = session.query(CampaignLead).count()
    print(f"  Campaign-lead associations: {campaign_lead_count}")
    
    # Test enum constraints
    print("🎛️ Testing enum constraints...")
    
    # Test lead temperature enum
    temp_counts = {}
    for temp in ['hot', 'warm', 'cold']:
        count = session.query(Lead).filter(Lead.lead_temperature == temp).count()
        temp_counts[temp] = count
    print(f"  Lead temperatures: {temp_counts}")
    
    # Test campaign status enum
    status_counts = {}
    for status in ['draft', 'active', 'paused', 'completed', 'cancelled']:
        count = session.query(Campaign).filter(Campaign.status == status).count()
        status_counts[status] = count
    print(f"  Campaign statuses: {status_counts}")
    
    print("✅ Data integrity validation complete")
    return validation_results

def main():
    """Main function to populate test data"""
    print("🚀 Starting LMA Test Data Population")
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
        workflows = create_workflows(session, organizations, users, count=5)
        integrations = create_integrations(session, organizations, users, count=4)
        scoring_rules = create_lead_scoring_rules(session, organizations, count=8)
        campaigns = create_campaigns(session, organizations, users, count=6)
        
        # Create relationship data (skip workflow executions for now due to model issues)
        communications = create_communications(session, leads, users, count=40)
        campaign_leads = create_campaign_leads(session, campaigns, leads, count=30)
        lead_notes = create_lead_notes(session, leads, users, count=35)
        lead_assignments = create_lead_assignments(session, leads, users, count=15)
        score_history = create_lead_score_history(session, leads, scoring_rules, count=50)
        # Skip workflow_executions for now: workflow_executions = create_workflow_executions(session, workflows, leads, count=30)
        activity_logs = create_activity_logs(session, leads, users, count=60)
        
        # Validate data integrity
        validation_results = validate_data_integrity(session)
        
        print("\n" + "=" * 50)
        print("🎉 Test Data Population Complete!")
        print("=" * 50)
        print("📊 Summary:")
        for table, count in validation_results.items():
            print(f"  {table}: {count} records")
        
        print("\n✅ Database is ready for testing!")
        print("⚠️  Note: Workflow executions skipped due to model relationship issues")
        
    except Exception as e:
        print(f"❌ Error during data population: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 