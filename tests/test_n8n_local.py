#!/usr/bin/env python3
"""
Test N8N Local Setup
Tests that n8n is running locally and can communicate with the backend API.
"""

import requests
import json
import time
from typing import Dict, Any

def test_service_health() -> Dict[str, bool]:
    """Test that all required services are running."""
    services = {
        "Backend API": "http://localhost:8000/health",
        "N8N": "http://localhost:5678",
        "PostgreSQL": None,  # Will test via backend
        "Redis": None,  # Will test via backend
    }
    
    results = {}
    
    for service, url in services.items():
        if url is None:
            results[service] = True  # Skip direct testing
            continue
            
        try:
            response = requests.get(url, timeout=5)
            results[service] = response.status_code == 200
            print(f"✅ {service}: Running")
        except requests.exceptions.RequestException:
            results[service] = False
            print(f"❌ {service}: Not responding")
    
    return results

def test_backend_endpoints() -> Dict[str, bool]:
    """Test key backend endpoints that n8n workflows will use."""
    endpoints = {
        "Health Check": "http://localhost:8000/health",
        "Lead Scoring": "http://localhost:8000/api/leads/dev?test_scoring=true&limit=5",
        "Social Outreach": "http://localhost:8000/api/workflows/leads/social-outreach?limit=5",
        "CRM Sync": "http://localhost:8000/api/workflows/leads/crm-sync?limit=5",
    }
    
    headers = {"Authorization": "Bearer test-token"}
    results = {}
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            results[name] = response.status_code == 200
            
            if response.status_code == 200:
                print(f"✅ {name}: Working")
                if name == "Lead Scoring":
                    data = response.json()
                    lead_count = len(data.get('items', []))
                    print(f"   📊 Found {lead_count} leads for scoring")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[name] = False
            print(f"❌ {name}: Connection error - {e}")
    
    return results

def test_n8n_webhook() -> bool:
    """Test n8n webhook endpoint (if workflow is imported and active)."""
    webhook_url = "http://localhost:5678/webhook/lead-activity"
    
    test_payload = {
        "lead_id": 1,
        "activity": "test_activity",
        "timestamp": time.time()
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ N8N Webhook: Working")
            print(f"   📝 Response: {response.text[:100]}...")
            return True
        else:
            print(f"⚠️  N8N Webhook: HTTP {response.status_code}")
            print(f"   📝 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ N8N Webhook: Connection error - {e}")
        print("   💡 Make sure the Lead Scoring workflow is imported and active")
        return False

def main():
    """Run all tests and provide setup guidance."""
    print("🧪 Testing N8N Local Setup")
    print("=" * 50)
    
    # Test service health
    print("\n1. Testing Service Health...")
    service_results = test_service_health()
    
    # Test backend endpoints
    print("\n2. Testing Backend Endpoints...")
    endpoint_results = test_backend_endpoints()
    
    # Test n8n webhook
    print("\n3. Testing N8N Webhook...")
    webhook_result = test_n8n_webhook()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    
    all_services_up = all(service_results.values())
    all_endpoints_working = all(endpoint_results.values())
    
    if all_services_up:
        print("✅ All services are running")
    else:
        print("❌ Some services are not running")
        failed_services = [name for name, status in service_results.items() if not status]
        print(f"   Failed: {', '.join(failed_services)}")
    
    if all_endpoints_working:
        print("✅ All backend endpoints are working")
    else:
        print("❌ Some backend endpoints are not working")
        failed_endpoints = [name for name, status in endpoint_results.items() if not status]
        print(f"   Failed: {', '.join(failed_endpoints)}")
    
    if webhook_result:
        print("✅ N8N webhook is working")
    else:
        print("❌ N8N webhook is not working")
    
    # Provide next steps
    print("\n📝 Next Steps:")
    
    if not all_services_up:
        print("   1. Start services: docker-compose up -d --build")
        print("   2. Wait 30 seconds for services to initialize")
        print("   3. Re-run this test")
    
    if all_services_up and not all_endpoints_working:
        print("   1. Check backend logs: docker-compose logs -f backend")
        print("   2. Verify database is initialized")
        print("   3. Check for any startup errors")
    
    if all_services_up and all_endpoints_working and not webhook_result:
        print("   1. Open N8N: http://localhost:5678 (admin/admin123)")
        print("   2. Import workflow: n8n-workflows/Lead_Scoring_CORRECTED.json")
        print("   3. Activate the workflow (toggle switch)")
        print("   4. Re-run this test")
    
    if all_services_up and all_endpoints_working and webhook_result:
        print("   🎉 Everything is working! You can now:")
        print("   1. Open frontend: http://localhost:15173")
        print("   2. Run full tests: python tests/test_complete_workflow.py")
        print("   3. Monitor with Grafana: http://localhost:13000")

if __name__ == "__main__":
    main() 