#!/usr/bin/env python3
"""
Detailed N8N Workflow Testing
Test each endpoint that the workflow calls to understand what's happening
"""

import requests
import json
import time

def get_auth_token():
    """Get authentication token"""
    auth_data = {"username": "dev@example.com", "password": "password"}
    response = requests.post("http://localhost:8000/api/auth/login", json=auth_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_individual_workflow_endpoints():
    """Test each endpoint that the n8n workflow calls"""
    print("🔍 Testing Individual Workflow Endpoints")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8000"
    
    # Test endpoints that the workflow uses
    test_cases = [
        {
            "name": "Get Leads for Scoring",
            "method": "GET",
            "url": f"{base_url}/api/leads/dev?test_scoring=true&limit=20",
            "expected": "Should return leads array"
        },
        {
            "name": "Social Outreach Query",
            "method": "GET", 
            "url": f"{base_url}/api/workflows/leads/social-outreach?temperature=hot&limit=5",
            "expected": "Should return hot leads"
        },
        {
            "name": "CRM Sync Query",
            "method": "GET",
            "url": f"{base_url}/api/workflows/leads/crm-sync?limit=10", 
            "expected": "Should return leads for sync"
        }
    ]
    
    for test in test_cases:
        print(f"\n📊 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            response = requests.get(test['url'], headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    items = data.get('items', data.get('data', []))
                    print(f"   ✅ Success: {len(items)} items")
                    if items:
                        sample = items[0]
                        print(f"   📝 Sample: ID={sample.get('id')}, Name={sample.get('first_name', 'N/A')} {sample.get('last_name', 'N/A')}")
                else:
                    print(f"   ✅ Success: {len(data)} items")
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_workflow_with_manual_execution():
    """Test by manually calling the cron trigger path"""
    print("\n🤖 Testing Manual Workflow Execution")
    print("=" * 50)
    
    # The workflow has two entry points:
    # 1. Webhook: http://localhost:5678/webhook/lead-activity
    # 2. Cron trigger (internal)
    
    # Let's test what happens if we trigger the webhook with no payload
    webhook_tests = [
        {"payload": {}, "description": "Empty payload"},
        {"payload": {"test": True}, "description": "Simple test payload"},
        {"payload": {"trigger": "manual", "leads": []}, "description": "Manual trigger"},
    ]
    
    for test in webhook_tests:
        print(f"\n🧪 Testing webhook with: {test['description']}")
        try:
            response = requests.post(
                "http://localhost:5678/webhook/lead-activity",
                json=test['payload'],
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"   ✅ JSON Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"   📝 Raw Response: {response.text}")
            else:
                print(f"   ⚠️ Empty response body")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_n8n_execution_status():
    """Check n8n execution logs via API"""
    print("\n📋 Checking N8N Execution Status")
    print("=" * 50)
    
    try:
        # N8N API endpoints (if available)
        n8n_base = "http://localhost:5678"
        
        # Try to get workflow info
        response = requests.get(f"{n8n_base}/api/v1/workflows", timeout=5)
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Found {len(workflows)} workflows")
            for wf in workflows:
                print(f"   - {wf.get('name', 'Unnamed')} (ID: {wf.get('id')}, Active: {wf.get('active')})")
        else:
            print("⚠️ Cannot access N8N API directly")
            print("   Check executions manually in N8N interface at http://localhost:5678")
            
    except Exception as e:
        print(f"⚠️ N8N API not accessible: {e}")
        print("   Check executions manually in N8N interface at http://localhost:5678")

def main():
    print("🔧 DETAILED N8N WORKFLOW TESTING")
    print("=" * 60)
    
    # Test 1: Individual endpoints
    test_individual_workflow_endpoints()
    
    # Test 2: Manual workflow execution
    test_workflow_with_manual_execution()
    
    # Test 3: N8N execution status
    check_n8n_execution_status()
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("✅ If all endpoints return data: N8N authentication is working")
    print("✅ If webhook returns 200: N8N is receiving requests")
    print("❌ If webhook returns empty: Check N8N execution logs")
    print()
    print("🎯 Next steps:")
    print("1. Check N8N interface: http://localhost:5678")
    print("2. Go to 'Executions' tab")
    print("3. Look for recent executions and any error messages")
    print("4. Check each node in the workflow for data flow")

if __name__ == "__main__":
    main() 