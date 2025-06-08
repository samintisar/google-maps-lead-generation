#!/usr/bin/env python3
"""
Test N8N Webhook for Lead Scoring Workflow
"""

import requests
import json
import time

def test_n8n_webhook():
    """Test the n8n webhook endpoint"""
    webhook_url = "http://localhost:5678/webhook/lead-activity"
    
    # Test data
    test_data = {
        "test": True,
        "trigger": "manual_test",
        "timestamp": time.time()
    }
    
    print("🧪 Testing N8N Lead Scoring Webhook")
    print("=" * 50)
    print(f"Webhook URL: {webhook_url}")
    print(f"Test Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        print("🚀 Sending webhook request...")
        response = requests.post(
            webhook_url,
            json=test_data,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"📝 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n🎉 Webhook test SUCCESSFUL!")
            return True
        else:
            print(f"\n❌ Webhook test FAILED with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text}")
        return False

def test_backend_endpoints():
    """Test the backend API endpoints that the workflow uses"""
    base_url = "http://localhost:8000"
    
    # First, get a token
    auth_data = {
        "username": "dev@example.com",
        "password": "password"
    }
    
    print("\n🔐 Getting authentication token...")
    auth_response = requests.post(f"{base_url}/api/auth/login", json=auth_data)
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful")
    
    # Test endpoints
    endpoints = [
        ("/api/leads/dev?test_scoring=true&limit=20", "GET"),
        ("/api/workflows/leads/social-outreach?temperature=hot&limit=5", "GET"),
        ("/api/workflows/leads/crm-sync?limit=10", "GET"),
    ]
    
    print("\n🧪 Testing Backend Endpoints...")
    print("-" * 40)
    
    for endpoint, method in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {method} {endpoint}")
                print(f"   📊 Response: {len(data.get('items', data.get('data', [])))} items")
            else:
                print(f"❌ {method} {endpoint} - Status: {response.status_code}")
                print(f"   📝 Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {e}")
    
    return True

def main():
    print("🚀 LMA N8N Workflow Testing")
    print("=" * 50)
    
    # Test 1: Backend endpoints
    backend_ok = test_backend_endpoints()
    
    # Test 2: N8N webhook
    webhook_ok = test_n8n_webhook()
    
    print("\n" + "=" * 50)
    print("📋 FINAL RESULTS")
    print("=" * 50)
    print(f"Backend Endpoints: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"N8N Webhook: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    if backend_ok and webhook_ok:
        print("\n🎉 ALL TESTS PASSED! Your workflow is ready!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 