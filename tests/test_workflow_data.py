#!/usr/bin/env python3
"""
Test and Provide Data to N8N Workflow
This script will check backend data and feed test data to the workflow
"""

import requests
import json
import time

def get_auth_token():
    """Get authentication token from backend"""
    auth_data = {
        "username": "dev@example.com", 
        "password": "password"
    }
    
    response = requests.post("http://localhost:8000/api/auth/login", json=auth_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Auth failed: {response.status_code}")
        return None

def check_backend_data():
    """Check what data exists in the backend"""
    print("🔍 Checking Backend Data...")
    
    token = get_auth_token()
    if not token:
        return []
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check leads
    response = requests.get("http://localhost:8000/api/leads/dev?test_scoring=true&limit=20", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        leads = data.get("items", data.get("data", []))
        print(f"✅ Found {len(leads)} leads in backend")
        
        if leads:
            print("📝 Sample lead:")
            sample = leads[0]
            print(f"   ID: {sample.get('id')}")
            print(f"   Name: {sample.get('first_name')} {sample.get('last_name')}")
            print(f"   Email: {sample.get('email')}")
            print(f"   Company: {sample.get('company')}")
            print(f"   Score: {sample.get('score', 'N/A')}")
        
        return leads
    else:
        print(f"❌ Failed to get leads: {response.status_code}")
        print(f"   Error: {response.text}")
        return []

def feed_data_to_webhook(leads_data=None):
    """Send data directly to the n8n webhook"""
    webhook_url = "http://localhost:5678/webhook/lead-activity"
    
    # If no leads provided, create sample data
    if not leads_data:
        leads_data = [
            {
                "id": 1,
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "company": "Test Company",
                "score": 45,
                "created_at": "2025-01-01T00:00:00Z"
            }
        ]
    
    # Create payload for webhook
    payload = {
        "trigger": "manual_test",
        "timestamp": time.time(),
        "leads": leads_data[:5],  # Send first 5 leads
        "test_mode": True
    }
    
    print(f"\n🚀 Sending {len(payload['leads'])} leads to webhook...")
    print(f"Webhook URL: {webhook_url}")
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        print(f"✅ Webhook Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("📋 Webhook Result:")
                print(json.dumps(result, indent=2))
                return True
            except:
                print(f"📝 Raw Response: {response.text}")
                return True
        else:
            print(f"❌ Webhook failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return False

def test_workflow_with_cron():
    """Test the hourly cron trigger"""
    print("\n⏰ Testing Cron Trigger...")
    print("NOTE: Cron triggers run automatically in n8n")
    print("To manually test: Go to n8n > Your workflow > Click 'Execute Workflow'")

def get_real_auth_token_for_n8n():
    """Get a real token that can be used in n8n workflow"""
    print("\n🔑 Getting Real Auth Token for N8N...")
    
    token = get_auth_token()
    if token:
        print("✅ Token obtained!")
        print("📋 Copy this token to your n8n workflow:")
        print(f"Bearer {token}")
        print("\n📝 How to update n8n workflow:")
        print("1. Go to each HTTP Request node in n8n")
        print("2. In 'Header Auth' credential, update the value to:")
        print(f"   Authorization: Bearer {token}")
        print("3. Save and test the workflow")
        return token
    else:
        print("❌ Could not get token")
        return None

def main():
    print("🧪 N8N Workflow Data Testing")
    print("=" * 50)
    
    # Step 1: Check backend data
    leads = check_backend_data()
    
    # Step 2: Get real auth token
    token = get_real_auth_token_for_n8n()
    
    # Step 3: Test webhook with data
    if leads:
        print(f"\n📤 Testing webhook with {len(leads)} real leads...")
        webhook_success = feed_data_to_webhook(leads)
    else:
        print("\n📤 Testing webhook with sample data...")
        webhook_success = feed_data_to_webhook()
    
    # Step 4: Instructions
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS")
    print("=" * 50)
    
    if token:
        print("✅ 1. Update n8n authentication:")
        print(f"      Use this token: Bearer {token}")
    
    if webhook_success:
        print("✅ 2. Webhook is working")
    else:
        print("❌ 2. Fix webhook issues")
    
    print("✅ 3. In n8n interface:")
    print("      - Click 'Execute Workflow' to manually test")
    print("      - Check 'Executions' tab for detailed logs")
    print("      - Verify each node has data flowing through")
    
    print("\n🎯 The workflow should now have data to process!")

if __name__ == "__main__":
    main() 