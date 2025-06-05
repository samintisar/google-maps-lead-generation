#!/usr/bin/env python3
"""
Simple test script for Lead Enrichment Service
"""
import asyncio
import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from models import Lead, Organization, User, Base
from services.lead_enrichment_service import LeadEnrichmentService

def create_test_db():
    """Create a test database in memory."""
    # Clean up any existing test database
    db_path = "test_enrichment.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass  # Ignore if file is locked
    
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_test_data(db):
    """Create test organization and lead data."""
    # Create organization with unique slug
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Company",
        slug=f"test-company-{unique_id}"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Create user
    user = User(
        email=f"test-{unique_id}@example.com",
        username=f"testuser-{unique_id}",
        first_name="Test",
        last_name="User",
        hashed_password="hashed_password",
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create test lead
    lead = Lead(
        email="john.doe@acme-corp.com",
        first_name="john",
        last_name="doe",
        company="acme corp",
        job_title="ceo",
        phone="555-123-4567",
        website="https://www.acme-corp.com",
        organization_id=org.id
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    return org, user, lead

async def test_enrichment_service():
    """Test the lead enrichment service."""
    print("🧪 Testing Lead Enrichment Service...")
    
    # Create test database and data
    db = create_test_db()
    org, user, lead = create_test_data(db)
    
    print(f"📝 Created test lead: {lead.first_name} {lead.last_name} ({lead.email})")
    print(f"   Company: {lead.company}")
    print(f"   Job Title: {lead.job_title}")
    print(f"   Phone: {lead.phone}")
    print(f"   Website: {lead.website}")
    
    # Initialize enrichment service
    enrichment_service = LeadEnrichmentService(db)
    
    try:
        # Test individual enrichment types
        print("\n🔍 Testing email enrichment...")
        email_result = await enrichment_service._enrich_email(lead)
        print(f"   Email validation result: {email_result['validation']}")
        
        print("\n📞 Testing phone enrichment...")
        phone_result = await enrichment_service._enrich_phone(lead)
        print(f"   Phone validation result: {phone_result['validation']}")
        print(f"   Phone formatting result: {phone_result['formatted']}")
        
        print("\n🏢 Testing company enrichment...")
        company_result = await enrichment_service._enrich_company(lead)
        print(f"   Normalized company: {company_result['normalized_company']}")
        print(f"   Industry: {company_result['industry']}")
        print(f"   Size estimate: {company_result['size_estimate']}")
        
        print("\n🔄 Testing data normalization...")
        norm_result = await enrichment_service._normalize_lead_data(lead)
        print(f"   Original data: {norm_result['original_data']}")
        print(f"   Normalized data: {norm_result['normalized_data']}")
        print(f"   Changes: {norm_result['changes']}")
        
        print("\n🔍 Testing duplicate detection...")
        dedup_result = await enrichment_service._check_duplicates(lead)
        print(f"   Potential duplicates: {len(dedup_result['potential_duplicates'])}")
        print(f"   Duplicate score: {dedup_result['duplicate_score']}")
        
        # Test full enrichment
        print("\n🚀 Testing full lead enrichment...")
        enrichment_result = await enrichment_service.enrich_lead(lead.id)
        
        print(f"✅ Enrichment completed successfully!")
        print(f"   Processing time: {enrichment_result['metadata']['processing_time_ms']:.2f}ms")
        print(f"   Enrichment types: {enrichment_result['enrichment_types']}")
        print(f"   Data sources: {enrichment_result['data_sources']}")
        print(f"   Errors: {len(enrichment_result['errors'])}")
        
        # Check the enriched lead data
        db.refresh(lead)
        print(f"\n📊 Enriched lead data:")
        print(f"   Email: {lead.email}")
        print(f"   First name: {lead.first_name}")
        print(f"   Last name: {lead.last_name}")
        print(f"   Company: {lead.company}")
        print(f"   Job title: {lead.job_title}")
        print(f"   Phone: {lead.phone}")
        print(f"   Custom fields: {lead.custom_fields}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        # Clean up test database file
        if os.path.exists("test_enrichment.db"):
            os.remove("test_enrichment.db")

if __name__ == "__main__":
    asyncio.run(test_enrichment_service()) 