#!/usr/bin/env python3
"""
Create Test Leads for Lead Scoring Workflow Testing
Populates the database with realistic test leads
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "dev@example.com"
TEST_PASSWORD = "password"

class TestLeadCreator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
    
    def authenticate(self):
        """Authenticate with the API"""
        print("🔐 Authenticating with API...")
        
        auth_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                auth_result = response.json()
                self.auth_token = auth_result.get("access_token")
                
                if self.auth_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    print("✅ Authentication successful")
                    return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            
        return False
    
    def create_test_leads_via_api(self):
        """Create test leads using the regular leads API"""
        print("\n📝 Creating test leads via API...")
        
        # Test lead data - realistic examples with correct fields
        test_leads = [
            {
                "organization_id": 1,  # Test organization
                "email": "john.doe@techcorp.com",
                "first_name": "John",
                "last_name": "Doe", 
                "company": "TechCorp Industries",
                "phone": "+1-555-0101",
                "source": "website",  # Valid enum value
                "notes": "Downloaded pricing guide, visited demo page 3 times"
            },
            {
                "organization_id": 1,
                "email": "sarah.wilson@startup.io",
                "first_name": "Sarah",
                "last_name": "Wilson",
                "company": "Startup Solutions",
                "phone": "+1-555-0102", 
                "source": "social_media",  # linkedin -> social_media
                "notes": "CEO of growing startup, interested in enterprise features"
            },
            {
                "organization_id": 1,
                "email": "mike.chen@bigcorp.net",
                "first_name": "Mike",
                "last_name": "Chen",
                "company": "BigCorp Enterprise",
                "phone": "+1-555-0103",
                "source": "referral",  # Valid enum value
                "notes": "Referred by existing customer, high-value prospect"
            },
            {
                "organization_id": 1,
                "email": "lisa.brown@smallbiz.com",
                "first_name": "Lisa", 
                "last_name": "Brown",
                "company": "Small Business Co",
                "phone": "+1-555-0104",
                "source": "advertising",  # paid_ads -> advertising
                "notes": "Clicked on Google Ad, budget-conscious"
            },
            {
                "organization_id": 1,
                "email": "alex.garcia@enterprise.org",
                "first_name": "Alex",
                "last_name": "Garcia", 
                "company": "Enterprise Solutions",
                "phone": "+1-555-0105",
                "source": "event",  # conference -> event
                "notes": "Met at tech conference, very interested in automation"
            }
        ]
        
        created_leads = []
        
        for lead_data in test_leads:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/leads/",
                    json=lead_data,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    created_leads.append(result)
                    print(f"   ✅ Created: {lead_data['first_name']} {lead_data['last_name']} - {lead_data['company']}")
                else:
                    print(f"   ❌ Failed to create {lead_data['first_name']} {lead_data['last_name']}: {response.status_code}")
                    print(f"      Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error creating {lead_data['first_name']} {lead_data['last_name']}: {e}")
        
        print(f"\n✅ Successfully created {len(created_leads)} test leads")
        return created_leads
    
    def simulate_lead_engagement(self, leads):
        """Simulate engagement data for leads to make scoring more realistic"""
        print("\n🎭 Simulating lead engagement activities...")
        
        for lead in leads:
            if not isinstance(lead, dict):
                continue
                
            lead_id = lead.get('id')
            name = f"{lead.get('first_name', 'Unknown')} {lead.get('last_name', '')}"
            
            # Simulate different engagement levels
            engagement_level = random.choice(['high', 'medium', 'low'])
            
            activities = []
            
            if engagement_level == 'high':
                activities = [
                    "Visited pricing page 5 times",
                    "Downloaded product guide",
                    "Watched demo video",
                    "Opened 8 of 10 emails",
                    "Requested demo call"
                ]
                score_boost = random.randint(60, 85)
            elif engagement_level == 'medium':
                activities = [
                    "Visited website 3 times", 
                    "Opened 4 of 7 emails",
                    "Downloaded whitepaper"
                ]
                score_boost = random.randint(25, 50)
            else:  # low
                activities = [
                    "Visited homepage once",
                    "Opened 1 of 5 emails"
                ]
                score_boost = random.randint(5, 20)
            
            # Try to update lead with engagement notes
            update_data = {
                "notes": f"Engagement: {', '.join(activities)}"
            }
            
            try:
                response = self.session.put(
                    f"{BASE_URL}/api/leads/{lead_id}",
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   📈 {name}: {engagement_level.upper()} engagement (potential score: {score_boost})")
                else:
                    print(f"   ⚠️ Could not update engagement for {name}")
                    
            except Exception as e:
                print(f"   ❌ Error updating {name}: {e}")
        
        print("✅ Engagement simulation completed")
    
    def run_workflow_test_after_creation(self):
        """Run the lead scoring test after creating leads"""
        print("\n🚀 Running Lead Scoring Workflow Test...")
        
        try:
            # Import and run the simplified test
            import subprocess
            result = subprocess.run(
                ["python", "test_lead_scoring_simple.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print("📊 Workflow Test Results:")
            print(result.stdout)
            
            if result.stderr:
                print("⚠️ Test Warnings/Errors:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏰ Workflow test timed out")
        except Exception as e:
            print(f"❌ Error running workflow test: {e}")

def main():
    """Main execution"""
    print("🚀 CREATING TEST LEADS FOR SCORING WORKFLOW")
    print("="*60)
    
    creator = TestLeadCreator()
    
    # Step 1: Authenticate
    if not creator.authenticate():
        print("❌ Authentication failed. Cannot proceed.")
        return
    
    try:
        # Step 2: Create test leads
        leads = creator.create_test_leads_via_api()
        
        if leads:
            # Step 3: Simulate engagement
            creator.simulate_lead_engagement(leads)
            
            # Step 4: Run the workflow test
            print("\n" + "="*60)
            creator.run_workflow_test_after_creation()
        else:
            print("❌ No leads were created. Cannot proceed with workflow test.")
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 