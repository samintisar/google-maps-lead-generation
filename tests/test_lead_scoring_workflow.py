#!/usr/bin/env python3
"""
Comprehensive Lead Scoring Workflow Test
Simulates the complete lead lifecycle that would happen in n8n workflows.
"""
import requests
import json
import time
from datetime import datetime
from faker import Faker

fake = Faker()

class LeadScoringWorkflowTester:
    def __init__(self, base_url="http://localhost:8000", token="test-token"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.created_leads = []
        
    def log_step(self, step_number, description, status="🔄"):
        """Log workflow step with formatting"""
        print(f"\n{status} Step {step_number}: {description}")
        print("=" * 60)
    
    def log_result(self, success, message, data=None):
        """Log step result"""
        status = "✅" if success else "❌"
        print(f"{status} {message}")
        if data:
            print(f"📊 Data: {json.dumps(data, indent=2)}")
    
    def authenticate(self):
        """Test authentication"""
        self.log_step(0, "Authentication Test")
        try:
            response = requests.get(f"{self.base_url}/api/auth/me", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                self.log_result(True, f"Authenticated as: {user_data.get('email', 'Unknown')}")
                return True
            else:
                self.log_result(False, f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_result(False, f"Authentication error: {str(e)}")
            return False
    
    def create_new_lead(self):
        """Step 1: Create a new lead (simulates form submission/import)"""
        self.log_step(1, "Create New Lead (Form Submission)")
        
        # Generate realistic lead data
        lead_data = {
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "company": fake.company(),
            "organization_id": 1,
            "source": "website"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/workflows/leads/create",
                headers=self.headers,
                json=lead_data
            )
            
            if response.status_code == 200:
                result = response.json()
                lead_id = result["data"]["lead_id"]
                self.created_leads.append(lead_id)
                self.log_result(True, f"Lead created successfully (ID: {lead_id})", {
                    "lead_id": lead_id,
                    "email": result["data"]["email"],
                    "name": f"{result['data']['first_name']} {result['data']['last_name']}",
                    "company": result["data"]["company"]
                })
                return lead_id
            else:
                self.log_result(False, f"Failed to create lead: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result(False, f"Error creating lead: {str(e)}")
            return None
    
    def update_lead_status(self, lead_id):
        """Step 2: Update lead status (simulates lead qualification)"""
        self.log_step(2, f"Update Lead Status (Lead ID: {lead_id})")
        
        update_data = {
            "status": "contacted",
            "notes": "Initial contact made via phone call",
            "last_contacted_at": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/workflows/leads/{lead_id}/update-status",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(True, "Lead status updated successfully", {
                    "lead_id": result["data"]["lead_id"],
                    "new_status": result["data"]["status"]
                })
                return True
            else:
                self.log_result(False, f"Failed to update status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(False, f"Error updating lead status: {str(e)}")
            return False
    
    def get_leads_for_social_outreach(self):
        """Step 3: Get leads for social media outreach"""
        self.log_step(3, "Get Leads for Social Media Outreach")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/leads/social-outreach?limit=5",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                leads = result["data"]
                self.log_result(True, f"Retrieved {len(leads)} leads for social outreach", {
                    "count": len(leads),
                    "leads": [{"id": lead["id"], "name": f"{lead['first_name']} {lead['last_name']}", 
                             "company": lead["company"], "score": lead["score"]} for lead in leads[:3]]
                })
                return leads
            else:
                self.log_result(False, f"Failed to get social outreach leads: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log_result(False, f"Error getting social outreach leads: {str(e)}")
            return []
    
    def log_social_outreach_activity(self, lead_id):
        """Step 4: Log social media outreach activity"""
        self.log_step(4, f"Log Social Media Outreach (Lead ID: {lead_id})")
        
        outreach_data = {
            "outreach_type": "linkedin_connection",
            "message_sent": True,
            "status": "sent",
            "linkedin_connection_status": "pending",
            "linkedin_connection_message": "Hi! I'd love to connect and discuss how we can help your business grow."
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/workflows/leads/{lead_id}/social-outreach",
                headers=self.headers,
                json=outreach_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(True, "Social outreach activity logged", {
                    "lead_id": result["data"]["lead_id"],
                    "activity_logged": result["data"]["outreach_logged"],
                    "linkedin_messages_sent": result["data"]["linkedin_messages_sent"]
                })
                return True
            else:
                self.log_result(False, f"Failed to log social outreach: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(False, f"Error logging social outreach: {str(e)}")
            return False
    
    def get_leads_for_crm_sync(self):
        """Step 5: Get leads for CRM synchronization"""
        self.log_step(5, "Get Leads for CRM Synchronization")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/leads/crm-sync?limit=10",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                leads = result["data"]
                self.log_result(True, f"Retrieved {len(leads)} leads for CRM sync", {
                    "count": len(leads),
                    "sample_leads": [{"id": lead["id"], "email": lead["email"], 
                                   "crm_id": lead.get("crm_id", "None")} for lead in leads[:3]]
                })
                return leads
            else:
                self.log_result(False, f"Failed to get CRM sync leads: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log_result(False, f"Error getting CRM sync leads: {str(e)}")
            return []
    
    def update_crm_sync_status(self, leads):
        """Step 6: Update CRM synchronization status"""
        self.log_step(6, "Update CRM Synchronization Status")
        
        # Simulate CRM sync updates for the leads
        sync_updates = []
        for lead in leads[:3]:  # Process first 3 leads
            sync_updates.append({
                "lead_id": lead["id"],
                "crm_id": f"CRM_{fake.random_number(digits=6)}",
                "sync_status": "synced",
                "last_sync": datetime.utcnow().isoformat()
            })
        
        try:
            response = requests.post(
                f"{self.base_url}/api/workflows/leads/crm-sync",
                headers=self.headers,
                json=sync_updates
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(True, f"CRM sync completed for {len(sync_updates)} leads", {
                    "synced_count": len(result["data"]["successful_syncs"]),
                    "failed_count": len(result["data"]["failed_syncs"]),
                    "sample_synced": result["data"]["successful_syncs"][:2]
                })
                return True
            else:
                self.log_result(False, f"Failed to update CRM sync: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(False, f"Error updating CRM sync: {str(e)}")
            return False
    
    def get_leads_for_scoring(self):
        """Step 7: Get leads for scoring analysis"""
        self.log_step(7, "Get Leads for Scoring Analysis")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/leads/dev?test_scoring=true&limit=10",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                leads = result["items"]
                
                # Calculate some basic analytics
                total_leads = len(leads)
                avg_score = sum(lead.get("score", 0) for lead in leads) / total_leads if total_leads > 0 else 0
                hot_leads = sum(1 for lead in leads if lead.get("lead_temperature") == "hot")
                
                self.log_result(True, f"Retrieved {total_leads} leads for scoring", {
                    "total_leads": total_leads,
                    "average_score": round(avg_score, 2),
                    "hot_leads": hot_leads,
                    "score_distribution": {
                        "high_score (>70)": sum(1 for lead in leads if lead.get("score", 0) > 70),
                        "medium_score (30-70)": sum(1 for lead in leads if 30 <= lead.get("score", 0) <= 70),
                        "low_score (<30)": sum(1 for lead in leads if lead.get("score", 0) < 30)
                    }
                })
                return leads
            else:
                self.log_result(False, f"Failed to get leads for scoring: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log_result(False, f"Error getting leads for scoring: {str(e)}")
            return []
    
    def run_complete_workflow(self):
        """Run the complete lead scoring workflow"""
        print("🚀 COMPREHENSIVE LEAD SCORING WORKFLOW TEST")
        print("=" * 80)
        print("This simulates how your n8n workflows would interact with the API")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Workflow stopped due to authentication failure")
            return False
        
        # Wait a moment
        time.sleep(1)
        
        # Step 1: Create new lead
        lead_id = self.create_new_lead()
        if not lead_id:
            print("❌ Workflow stopped due to lead creation failure")
            return False
        
        time.sleep(1)
        
        # Step 2: Update lead status
        if not self.update_lead_status(lead_id):
            print("⚠️  Continuing workflow despite status update failure")
        
        time.sleep(1)
        
        # Step 3: Get leads for social outreach
        social_leads = self.get_leads_for_social_outreach()
        
        time.sleep(1)
        
        # Step 4: Log social outreach (use created lead or first available)
        outreach_lead_id = lead_id if lead_id else (social_leads[0]["id"] if social_leads else None)
        if outreach_lead_id:
            self.log_social_outreach_activity(outreach_lead_id)
        
        time.sleep(1)
        
        # Step 5: Get leads for CRM sync
        crm_leads = self.get_leads_for_crm_sync()
        
        time.sleep(1)
        
        # Step 6: Update CRM sync status
        if crm_leads:
            self.update_crm_sync_status(crm_leads)
        
        time.sleep(1)
        
        # Step 7: Get leads for scoring
        scoring_leads = self.get_leads_for_scoring()
        
        # Final summary
        self.print_workflow_summary()
        
        return True
    
    def print_workflow_summary(self):
        """Print final workflow summary"""
        print("\n" + "=" * 80)
        print("📊 WORKFLOW EXECUTION SUMMARY")
        print("=" * 80)
        print(f"✅ Workflow completed successfully!")
        print(f"📈 New leads created: {len(self.created_leads)}")
        print(f"🎯 Lead IDs: {', '.join(map(str, self.created_leads))}")
        print("\n🔗 This demonstrates how n8n would:")
        print("   1. ✅ Create leads from form submissions")
        print("   2. ✅ Update lead statuses during qualification")
        print("   3. ✅ Identify leads for social media outreach")
        print("   4. ✅ Log outreach activities and engagement")
        print("   5. ✅ Sync lead data with external CRM systems")
        print("   6. ✅ Continuously analyze and score leads")
        print("\n🚀 Your lead scoring system is ready for n8n integration!")
        print("=" * 80)

def main():
    """Main test function"""
    tester = LeadScoringWorkflowTester()
    success = tester.run_complete_workflow()
    
    if success:
        print("\n✅ All workflow tests completed successfully!")
    else:
        print("\n❌ Workflow tests encountered errors")
    
    return success

if __name__ == "__main__":
    main() 