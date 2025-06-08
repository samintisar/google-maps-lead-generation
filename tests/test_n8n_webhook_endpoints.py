#!/usr/bin/env python3
"""
Test n8n Webhook Endpoints for Lead Scoring Workflow
Tests the actual endpoints that n8n would call in a real workflow
"""

import requests
import json
from datetime import datetime
import random

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

class N8nWebhookTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
    
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
                    user_info = auth_result.get("user", {})
                    print(f"   👤 User: {user_info.get('first_name')} {user_info.get('last_name')}")
                    print(f"   🏢 Organization ID: {user_info.get('organization_id')}")
                    return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            
        return False
    
    def get_test_leads(self):
        """Get leads for testing"""
        print("\n🔍 Getting leads for testing...")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/leads/", timeout=10)
            
            if response.status_code == 200:
                leads_data = response.json()
                leads = leads_data.get("items", [])
                print(f"✅ Found {len(leads)} leads")
                return leads[:3]  # Return first 3 for testing
            else:
                print(f"❌ Failed to get leads: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting leads: {e}")
            
        return []
    
    def test_endpoint(self, method, endpoint, data, description):
        """Test a specific endpoint"""
        print(f"\n🔗 Testing: {description}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == "GET":
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=15)
            elif method == "POST":
                response = self.session.post(f"{BASE_URL}{endpoint}", json=data, timeout=15)
            elif method == "PUT":
                response = self.session.put(f"{BASE_URL}{endpoint}", json=data, timeout=15)
            else:
                print(f"   ❌ Unsupported method: {method}")
                return False
            
            success = response.status_code in [200, 201, 202]
            
            result = {
                "description": description,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": success,
                "response_size": len(response.text)
            }
            
            if success:
                print(f"   ✅ Success: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"   📝 Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list):
                        print(f"   📝 Response: List with {len(response_data)} items")
                    result["response_data"] = response_data
                except:
                    print(f"   📝 Response: {response.text[:100]}...")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   📝 Error: {response.text[:200]}...")
                result["error"] = response.text
            
            self.test_results.append(result)
            return success
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            self.test_results.append({
                "description": description,
                "method": method,
                "endpoint": endpoint,
                "success": False,
                "error": str(e)
            })
            return False
    
    def test_lead_scoring_workflow(self, leads):
        """Test the complete lead scoring workflow"""
        print("\n🚀 TESTING LEAD SCORING WORKFLOW")
        print("="*50)
        
        if not leads:
            print("❌ No leads available for testing")
            return
        
        test_lead = leads[0]
        lead_id = test_lead.get('id')
        lead_name = f"{test_lead.get('first_name', 'Unknown')} {test_lead.get('last_name', '')}"
        
        print(f"🎯 Using test lead: {lead_name} (ID: {lead_id})")
        
        # Test 1: Get leads for scoring (what n8n HTTP Request node would do)
        self.test_endpoint(
            "GET",
            "/api/leads/dev?test_scoring=true",
            None,
            "Get leads for scoring (n8n HTTP Request)"
        )
        
        # Test 2: Create new lead (webhook endpoint)
        new_lead_data = {
            "email": f"test.lead.{random.randint(1000,9999)}@example.com",
            "firstName": "Test",
            "lastName": "Lead",
            "company": "Test Company",
            "source": "website"
        }
        
        self.test_endpoint(
            "POST",
            "/api/workflows/leads/create",
            new_lead_data,
            "Create new lead (n8n webhook)"
        )
        
        # Test 3: Update lead status
        status_update_data = {
            "status": "qualified",
            "notes": "Updated via n8n workflow test"
        }
        
        self.test_endpoint(
            "POST",
            f"/api/workflows/leads/{lead_id}/update-status",
            status_update_data,
            "Update lead status (n8n webhook)"
        )
        
        # Test 4: Get leads for social outreach
        self.test_endpoint(
            "GET",
            "/api/workflows/leads/social-outreach?limit=5",
            None,
            "Get leads for social outreach (n8n HTTP Request)"
        )
        
        # Test 5: Log social outreach activity
        outreach_data = {
            "platform": "linkedin",
            "action": "connection_request",
            "message": "Hi! I'd love to connect and discuss your business needs.",
            "status": "sent"
        }
        
        self.test_endpoint(
            "POST",
            f"/api/workflows/leads/{lead_id}/social-outreach",
            outreach_data,
            "Log social outreach activity (n8n webhook)"
        )
        
        # Test 6: Get leads for CRM sync
        self.test_endpoint(
            "GET",
            "/api/workflows/leads/crm-sync?limit=10",
            None,
            "Get leads for CRM sync (n8n HTTP Request)"
        )
        
        # Test 7: Update CRM sync status
        crm_sync_data = [
            {
                "lead_id": lead_id,
                "crm_id": f"CRM_{random.randint(10000,99999)}",
                "sync_status": "success",
                "last_sync": datetime.utcnow().isoformat()
            }
        ]
        
        self.test_endpoint(
            "POST",
            "/api/workflows/leads/crm-sync",
            crm_sync_data,
            "Update CRM sync status (n8n webhook)"
        )
        
        # Test 8: Handle CRM webhook (external system calling our API)
        crm_webhook_data = {
            "event": "lead_updated",
            "lead_id": lead_id,
            "crm_data": {
                "status": "qualified",
                "score": 85,
                "last_activity": datetime.utcnow().isoformat()
            }
        }
        
        self.test_endpoint(
            "POST",
            "/api/workflows/webhook/crm-update",
            crm_webhook_data,
            "Handle CRM webhook (external system → our API)"
        )
    
    def test_n8n_webhook_endpoints(self):
        """Test n8n-specific webhook endpoints"""
        print("\n🔗 TESTING N8N WEBHOOK ENDPOINTS")
        print("="*40)
        
        # Test generic webhook endpoints
        webhook_tests = [
            {
                "path": "lead-score-update",
                "data": {
                    "lead_id": 1,
                    "score": 85,
                    "temperature": "hot",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "description": "Lead score update webhook"
            },
            {
                "path": "hot-lead-alert",
                "data": {
                    "lead_id": 1,
                    "score": 95,
                    "temperature": "hot",
                    "alert_type": "hot_lead",
                    "urgency": "high"
                },
                "description": "Hot lead alert webhook"
            },
            {
                "path": "lead-engagement",
                "data": {
                    "lead_id": 1,
                    "engagement_type": "email_open",
                    "campaign_id": "test_campaign",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "description": "Lead engagement tracking webhook"
            }
        ]
        
        for webhook_test in webhook_tests:
            self.test_endpoint(
                "POST",
                f"/api/workflows/n8n/webhook/{webhook_test['path']}",
                webhook_test["data"],
                webhook_test["description"]
            )
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE LEAD SCORING WORKFLOW TEST REPORT")
        print("="*70)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get("success", False)])
        failed_tests = total_tests - successful_tests
        
        print(f"\n📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        print(f"\n🔍 Detailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result.get("success", False) else "❌"
            print(f"   {i:2d}. {status} {result['description']}")
            print(f"       {result['method']} {result['endpoint']}")
            if not result.get("success", False) and "error" in result:
                error_msg = result["error"][:100] + "..." if len(result["error"]) > 100 else result["error"]
                print(f"       Error: {error_msg}")
        
        print(f"\n🌐 Working Endpoints for n8n:")
        working_endpoints = [r for r in self.test_results if r.get("success", False)]
        for result in working_endpoints:
            print(f"   • {result['method']} {BASE_URL}{result['endpoint']}")
        
        print(f"\n⚠️ Failed Endpoints (need attention):")
        failed_endpoints = [r for r in self.test_results if not r.get("success", False)]
        for result in failed_endpoints:
            print(f"   • {result['method']} {BASE_URL}{result['endpoint']}")
        
        print(f"\n✅ Next Steps for n8n Workflow Setup:")
        print(f"   1. Use working endpoints in your n8n HTTP Request nodes")
        print(f"   2. Set up webhook triggers for the working webhook endpoints")
        print(f"   3. Implement error handling for failed endpoints")
        print(f"   4. Test the complete workflow end-to-end")
        print(f"   5. Monitor lead score changes and alerts")
        
        print("="*70)

def main():
    """Main test execution"""
    print("🚀 N8N WEBHOOK ENDPOINTS TEST SUITE")
    print("="*50)
    
    tester = N8nWebhookTester()
    
    # Step 1: Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed. Cannot proceed.")
        return
    
    try:
        # Step 2: Get test leads
        leads = tester.get_test_leads()
        
        # Step 3: Test lead scoring workflow
        tester.test_lead_scoring_workflow(leads)
        
        # Step 4: Test n8n webhook endpoints
        tester.test_n8n_webhook_endpoints()
        
        # Step 5: Generate comprehensive report
        tester.generate_comprehensive_report()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 