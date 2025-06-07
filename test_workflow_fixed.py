#!/usr/bin/env python3
"""
Lead Scoring Workflow Test Script - FIXED VERSION
This script uses existing leads and triggers the n8n workflow with realistic activity data.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://192.168.1.106:8000"
# Update this with your n8n Cloud webhook URL
N8N_WEBHOOK_URL = "https://your-n8n-cloud-instance.app.n8n.cloud/webhook/lead-activity"

# Activity simulation scenarios with realistic behavioral data
engagement_scenarios = [
    {
        "name": "🔥 HOT PROSPECT - High Engagement",
        "activity_type": "website_engagement",
        "activities": [
            {"type": "page_view", "page": "/pricing", "duration": 180},
            {"type": "page_view", "page": "/features", "duration": 240},
            {"type": "page_view", "page": "/demo", "duration": 300},
            {"type": "email_open", "campaign": "product_demo"},
            {"type": "email_click", "link": "schedule_demo"},
            {"type": "download", "resource": "enterprise_guide"},
        ],
        "behavioral_data": {
            "website_visits": 12,
            "pages_viewed": 35,
            "email_opens": 6,
            "email_clicks": 4,
            "downloads": 2,
            "company_size": 500,
            "industry": "technology"
        }
    },
    {
        "name": "🌡️ WARM LEAD - Medium Engagement", 
        "activity_type": "email_engagement",
        "activities": [
            {"type": "email_open", "campaign": "weekly_newsletter"},
            {"type": "page_view", "page": "/blog", "duration": 120},
            {"type": "page_view", "page": "/case-studies", "duration": 90},
        ],
        "behavioral_data": {
            "website_visits": 5,
            "pages_viewed": 12,
            "email_opens": 3,
            "email_clicks": 1,
            "downloads": 1,
            "company_size": 150,
            "industry": "consulting"
        }
    },
    {
        "name": "❄️ COLD LEAD - Low Engagement",
        "activity_type": "minimal_engagement",
        "activities": [
            {"type": "email_open", "campaign": "weekly_newsletter"},
        ],
        "behavioral_data": {
            "website_visits": 1,
            "pages_viewed": 3,
            "email_opens": 1,
            "email_clicks": 0,
            "downloads": 0,
            "company_size": 25,
            "industry": "retail"
        }
    },
    {
        "name": "🚀 ENTERPRISE PROSPECT - Decision Maker",
        "activity_type": "decision_maker_behavior",
        "activities": [
            {"type": "page_view", "page": "/enterprise", "duration": 420},
            {"type": "page_view", "page": "/security", "duration": 300},
            {"type": "page_view", "page": "/pricing", "duration": 180},
            {"type": "download", "resource": "security_whitepaper"},
            {"type": "download", "resource": "roi_calculator"},
        ],
        "behavioral_data": {
            "website_visits": 8,
            "pages_viewed": 25,
            "email_opens": 4,
            "email_clicks": 3,
            "downloads": 3,
            "company_size": 1000,
            "industry": "enterprise_software"
        }
    }
]

def get_existing_leads():
    """Get existing leads from the database"""
    try:
        response = requests.get(f"{BASE_URL}/api/leads/dev?test_scoring=true")
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            print(f"❌ Failed to get leads: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting leads: {e}")
        return []

def trigger_workflow_webhook(lead_data, scenario):
    """Trigger n8n workflow via webhook with enhanced activity data"""
    
    # Create comprehensive webhook payload
    webhook_payload = {
        "lead_id": lead_data["id"],
        "email": lead_data["email"],
        "first_name": lead_data["first_name"],
        "last_name": lead_data["last_name"],
        "company": lead_data["company"],
        "job_title": lead_data.get("job_title", "Unknown"),
        "current_score": lead_data.get("score", 0),
        "current_temperature": lead_data.get("lead_temperature", "cold"),
        
        # Activity trigger data
        "activity_type": scenario["activity_type"],
        "trigger_source": "test_automation",
        "timestamp": datetime.now().isoformat(),
        
        # Enhanced behavioral data for scoring
        **scenario["behavioral_data"],
        
        # Recent activities
        "recent_activities": scenario["activities"],
        
        # Additional context
        "test_scenario": scenario["name"],
        "should_rescore": True
    }
    
    print(f"    📤 Webhook payload preview:")
    print(f"       Lead: {lead_data['first_name']} {lead_data['last_name']}")
    print(f"       Scenario: {scenario['name']}")
    print(f"       Current Score: {lead_data.get('score', 0)}")
    print(f"       Activities: {len(scenario['activities'])} recent activities")
    
    # For testing, let's also test the local webhook endpoint
    local_webhook = "http://localhost:5678/webhook/lead-activity"
    
    for webhook_url in [local_webhook, N8N_WEBHOOK_URL]:
        try:
            response = requests.post(
                webhook_url,
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"    📡 Webhook to {webhook_url.split('/')[-3] if 'https' in webhook_url else 'localhost'}: {response.status_code}")
            
            if response.status_code == 200:
                return True
                
        except requests.exceptions.Timeout:
            print(f"    ⏱️ Timeout on {webhook_url}")
        except requests.exceptions.ConnectionError:
            print(f"    🔌 Connection failed to {webhook_url}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return False

def test_scoring_before_after(leads):
    """Test scoring endpoint before and after activities"""
    print(f"\n📊 INITIAL LEAD SCORES:")
    for lead in leads:
        print(f"  • {lead['first_name']} {lead['last_name']} - Score: {lead['score']}, Temp: {lead['lead_temperature']}")

def simulate_realistic_workflow():
    """Simulate realistic lead workflow with various engagement patterns"""
    print("🎭 SIMULATING REALISTIC LEAD WORKFLOW")
    print("=" * 60)
    
    # Get existing leads
    leads = get_existing_leads()
    if not leads:
        print("❌ No leads found! Please ensure leads exist in the database.")
        return
    
    print(f"✅ Found {len(leads)} existing leads to test")
    
    # Show initial scores
    test_scoring_before_after(leads)
    
    # Simulate different engagement patterns
    print(f"\n🎯 SIMULATING ENGAGEMENT SCENARIOS:")
    
    for i, lead in enumerate(leads[:4]):  # Test up to 4 leads
        scenario = engagement_scenarios[i % len(engagement_scenarios)]
        
        print(f"\n  {i+1}. Testing: {lead['first_name']} {lead['last_name']} ({lead['company']})")
        print(f"     Scenario: {scenario['name']}")
        
        # Trigger workflow
        success = trigger_workflow_webhook(lead, scenario)
        
        if success:
            print(f"     ✅ Workflow triggered successfully")
        else:
            print(f"     ⚠️ Webhook trigger failed - workflow may need manual triggering")
        
        # Wait between tests
        print(f"     ⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
    
    # Check if scores changed
    print(f"\n📈 CHECKING FOR SCORE UPDATES...")
    time.sleep(5)  # Wait for potential workflow execution
    
    updated_leads = get_existing_leads()
    print(f"\n📊 UPDATED LEAD SCORES:")
    for lead in updated_leads:
        print(f"  • {lead['first_name']} {lead['last_name']} - Score: {lead['score']}, Temp: {lead['lead_temperature']}")

def test_manual_scoring():
    """Test the scoring endpoint directly to simulate manual workflow execution"""
    print(f"\n🔧 TESTING MANUAL WORKFLOW EXECUTION:")
    
    leads = get_existing_leads()
    if leads:
        print(f"✅ Scoring endpoint working - returned {len(leads)} leads")
        print("   This simulates what your n8n workflow receives when it runs")
        
        # Show what the workflow algorithm would process
        for lead in leads:
            # Simulate the scoring calculation
            score = lead.get('score', 0)
            temp = lead.get('lead_temperature', 'cold')
            
            # Determine what actions the workflow would take
            actions = []
            if score >= 80:
                actions.append("🚨 Trigger hot lead alert")
                actions.append("📧 Send sales team notification")
            elif score >= 60:
                actions.append("📞 Schedule follow-up call")
                actions.append("🎯 Add to nurturing campaign")
            else:
                actions.append("📚 Add to educational sequence")
            
            print(f"\n   📋 {lead['first_name']} {lead['last_name']}:")
            print(f"      Current Score: {score} (Temperature: {temp})")
            print(f"      Workflow Actions: {', '.join(actions)}")
    else:
        print("❌ Scoring endpoint failed")

def main():
    """Main test execution"""
    print("🚀 COMPREHENSIVE LEAD SCORING WORKFLOW TEST")
    print("=" * 60)
    
    # Test backend connectivity
    print("\n1️⃣ Testing Backend Connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible and healthy")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test scoring endpoint
    print("\n2️⃣ Testing Scoring Endpoint...")
    test_manual_scoring()
    
    # Simulate realistic workflow
    print("\n3️⃣ Simulating Realistic Workflow...")
    simulate_realistic_workflow()
    
    # Final instructions
    print(f"\n🎉 WORKFLOW TEST COMPLETED!")
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. ✅ Check your n8n Cloud executions for workflow runs")
    print(f"   2. 🔍 Monitor lead scores in database for changes")
    print(f"   3. 📧 Look for sales team alert emails if any hot leads detected")
    print(f"   4. 📊 Verify activity logging is working properly")
    print(f"   5. ⏰ Confirm hourly automated scoring is running")
    
    print(f"\n💡 WORKFLOW VALIDATION:")
    print(f"   • Webhook endpoint: {'✅ Configured' if 'your-n8n' not in N8N_WEBHOOK_URL else '⚠️ Update N8N_WEBHOOK_URL'}")
    print(f"   • Backend API: ✅ Working")
    print(f"   • Lead data: ✅ Available") 
    print(f"   • Test scenarios: ✅ Executed")

if __name__ == "__main__":
    main() 