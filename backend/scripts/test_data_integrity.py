#!/usr/bin/env python3
"""
Data Integrity Test Script for LMA Database

This script performs comprehensive testing of the populated database.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import *

def run_integrity_tests():
    """Run comprehensive database integrity tests"""
    # Create session
    engine = create_engine('postgresql://lma_user:lma_password@localhost:5432/lma_db')
    Session = sessionmaker(bind=engine)
    session = Session()

    print('🔍 DATABASE INTEGRITY TESTS')
    print('=' * 40)

    # Test enum constraints
    print('📊 Testing Enum Values:')
    print(f'  UserRole values: {[role.value for role in UserRole]}')
    print(f'  LeadStatus values: {[status.value for status in LeadStatus]}')
    print(f'  LeadSource values: {[source.value for source in LeadSource]}')
    print(f'  LeadTemperature values: {[temp.value for temp in LeadTemperature]}')

    # Test relationships
    print('\n🔗 Testing Relationships:')
    org = session.query(Organization).first()
    if org:
        users_count = len(org.users)
        leads_count = len(org.leads)
        print(f'  Organization "{org.name}" has {users_count} users and {leads_count} leads')

    user = session.query(User).first()
    if user:
        assigned_leads_count = len(user.leads)
        print(f'  User "{user.first_name} {user.last_name}" has {assigned_leads_count} assigned leads')

    # Test data quality
    print('\n📈 Data Quality Checks:')
    leads_with_scores = session.query(Lead).filter(Lead.score.isnot(None)).count()
    total_leads = session.query(Lead).count()
    print(f'  Leads with scores: {leads_with_scores}/{total_leads}')

    leads_with_companies = session.query(Lead).filter(Lead.company.isnot(None)).count()
    print(f'  Leads with companies: {leads_with_companies}/{total_leads}')

    # Test foreign key constraints
    print('\n🔑 Testing Foreign Key Constraints:')
    orphaned_users = session.query(User).filter(User.organization_id.isnot(None)).filter(
        ~User.organization_id.in_(session.query(Organization.id))
    ).count()
    print(f'  Orphaned users (no valid org): {orphaned_users}')

    orphaned_leads = session.query(Lead).filter(Lead.organization_id.isnot(None)).filter(
        ~Lead.organization_id.in_(session.query(Organization.id))
    ).count()
    print(f'  Orphaned leads (no valid org): {orphaned_leads}')

    # Test unique constraints
    print('\n🆔 Testing Unique Constraints:')
    duplicate_emails = session.execute(text("""
        SELECT email, COUNT(*) as count 
        FROM users 
        GROUP BY email 
        HAVING COUNT(*) > 1
    """)).fetchall()
    print(f'  Duplicate user emails: {len(duplicate_emails)}')

    duplicate_lead_emails = session.execute(text("""
        SELECT email, COUNT(*) as count 
        FROM leads 
        GROUP BY email 
        HAVING COUNT(*) > 1
    """)).fetchall()
    print(f'  Duplicate lead emails: {len(duplicate_lead_emails)}')

    # Test table record counts
    print('\n📊 Table Record Counts:')
    tables = ['organizations', 'users', 'leads', 'workflows', 'campaigns', 
              'integrations', 'lead_scoring_rules', 'communications']
    
    for table in tables:
        try:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f'  {table}: {count} records')
        except Exception as e:
            print(f'  {table}: Error - {str(e)}')

    print('\n✅ All integrity tests completed!')
    session.close()

if __name__ == "__main__":
    run_integrity_tests() 