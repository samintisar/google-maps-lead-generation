#!/usr/bin/env python3
"""
Database Performance and Business Logic Test Script

This script performs comprehensive testing of database performance and business logic.
"""

import sys
import os
import time
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import *

def run_performance_tests():
    """Run database performance and business logic tests"""
    # Create session
    engine = create_engine('postgresql://lma_user:lma_password@localhost:5432/lma_db')
    Session = sessionmaker(bind=engine)
    session = Session()

    print('🏃‍♂️ DATABASE PERFORMANCE & BUSINESS LOGIC TESTS')
    print('=' * 55)

    # Test 1: Complex query performance
    print('\n⚡ Performance Tests:')
    
    start_time = time.time()
    complex_query = session.query(Lead).join(Organization).join(User).filter(
        Lead.score > 50,
        Organization.subscription_tier == 'premium'
    ).all()
    end_time = time.time()
    print(f'  Complex join query (leads>50 score, premium orgs): {len(complex_query)} results in {end_time - start_time:.3f}s')

    # Test 2: Aggregation performance
    start_time = time.time()
    avg_scores = session.query(
        Organization.name,
        func.avg(Lead.score).label('avg_score'),
        func.count(Lead.id).label('lead_count')
    ).join(Lead).group_by(Organization.id, Organization.name).all()
    end_time = time.time()
    print(f'  Organization lead averages: {len(avg_scores)} results in {end_time - start_time:.3f}s')
    for org_name, avg_score, lead_count in avg_scores:
        print(f'    {org_name}: {lead_count} leads, avg score {avg_score:.1f}')

    # Test 3: Communication efficiency
    print('\n💬 Communication Analysis:')
    comm_stats = session.query(
        Communication.communication_type,
        Communication.direction,
        func.count(Communication.id).label('count')
    ).group_by(Communication.communication_type, Communication.direction).all()
    
    for comm_type, direction, count in comm_stats:
        print(f'  {comm_type.value} {direction.value}: {count} communications')

    # Test 4: Campaign effectiveness
    print('\n📊 Campaign Analysis:')
    campaigns = session.query(Campaign).all()
    for campaign in campaigns:
        leads_count = len(campaign.campaign_leads)
        budget_efficiency = campaign.budget_spent / max(leads_count, 1) if campaign.budget_spent else 0
        print(f'  {campaign.name}: {leads_count} leads, ${budget_efficiency/100:.2f} cost per lead')

    # Test 5: Lead scoring distribution
    print('\n📈 Lead Scoring Distribution:')
    score_ranges = [
        ('Cold (0-30)', session.query(Lead).filter(Lead.score.between(0, 30)).count()),
        ('Warm (31-60)', session.query(Lead).filter(Lead.score.between(31, 60)).count()),
        ('Hot (61-100)', session.query(Lead).filter(Lead.score.between(61, 100)).count())
    ]
    for range_name, count in score_ranges:
        print(f'  {range_name}: {count} leads')

    # Test 6: User productivity
    print('\n👥 User Productivity:')
    user_stats = session.query(
        User.first_name,
        User.last_name,
        func.count(Lead.id).label('assigned_leads'),
        func.count(Communication.id).label('communications')
    ).outerjoin(Lead, User.id == Lead.assigned_to_id
    ).outerjoin(Communication
    ).group_by(User.id, User.first_name, User.last_name).all()
    
    for first_name, last_name, leads, comms in user_stats:
        print(f'  {first_name} {last_name}: {leads} leads, {comms} communications')

    # Test 7: Workflow adoption
    print('\n⚡ Workflow Status:')
    active_workflows = session.query(Workflow).filter(Workflow.is_active == True).count()
    total_workflows = session.query(Workflow).count()
    print(f'  Active workflows: {active_workflows}/{total_workflows}')
    
    workflow_by_category = session.query(
        Workflow.category,
        func.count(Workflow.id)
    ).group_by(Workflow.category).all()
    for category, count in workflow_by_category:
        print(f'    {category}: {count} workflows')

    # Test 8: Integration health
    print('\n🔗 Integration Health:')
    integration_status = session.query(
        Integration.status,
        func.count(Integration.id)
    ).group_by(Integration.status).all()
    for status, count in integration_status:
        print(f'  {status.value}: {count} integrations')

    # Test 9: Data consistency checks
    print('\n✅ Data Consistency:')
    
    # Check for leads without organizations
    orphaned_leads = session.query(Lead).filter(Lead.organization_id.is_(None)).count()
    print(f'  Leads without organizations: {orphaned_leads}')
    
    # Check for users without organizations  
    orphaned_users = session.query(User).filter(User.organization_id.is_(None)).count()
    print(f'  Users without organizations: {orphaned_users}')
    
    # Check for communications without leads
    orphaned_comms = session.query(Communication).filter(Communication.lead_id.is_(None)).count()
    print(f'  Communications without leads: {orphaned_comms}')
    
    # Check lead score consistency
    invalid_scores = session.query(Lead).filter(
        (Lead.score < 0) | (Lead.score > 100)
    ).count()
    print(f'  Leads with invalid scores (0-100): {invalid_scores}')

    # Test 10: Recent activity summary
    print('\n⏰ Recent Activity Summary:')
    recent_communications = session.query(Communication).filter(
        Communication.created_at >= func.now() - text("INTERVAL '7 days'")
    ).count()
    print(f'  Communications in last 7 days: {recent_communications}')
    
    recent_notes = session.query(LeadNote).filter(
        LeadNote.created_at >= func.now() - text("INTERVAL '7 days'")
    ).count()
    print(f'  Notes created in last 7 days: {recent_notes}')

    print('\n🎯 Business Logic Validation:')
    
    # Validate lead temperature vs score correlation
    hot_leads_high_score = session.query(Lead).filter(
        Lead.lead_temperature == LeadTemperature.HOT,
        Lead.score >= 70
    ).count()
    total_hot_leads = session.query(Lead).filter(
        Lead.lead_temperature == LeadTemperature.HOT
    ).count()
    if total_hot_leads > 0:
        hot_correlation = (hot_leads_high_score / total_hot_leads) * 100
        print(f'  Hot leads with high scores (70+): {hot_correlation:.1f}%')

    # Validate active campaigns have target criteria
    campaigns_with_criteria = session.query(Campaign).filter(
        Campaign.status == CampaignStatus.ACTIVE,
        Campaign.target_criteria.isnot(None)
    ).count()
    active_campaigns = session.query(Campaign).filter(
        Campaign.status == CampaignStatus.ACTIVE
    ).count()
    print(f'  Active campaigns with targeting: {campaigns_with_criteria}/{active_campaigns}')

    print('\n✅ All performance and business logic tests completed!')
    session.close()

if __name__ == "__main__":
    run_performance_tests() 