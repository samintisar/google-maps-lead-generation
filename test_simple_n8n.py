#!/usr/bin/env python3
"""
Simple test to show what n8n Cloud will see when it tries to access your backend
"""

import requests

def test_n8n_cloud_access():
    """Test what n8n Cloud would experience"""
    
    print("🧪 TESTING N8N CLOUD ACCESS SCENARIO")
    print("=" * 50)
    
    # Test local access (what we know works)
    print("\n1️⃣ Testing Local Access (what we confirmed works):")
    try:
        response = requests.get("http://192.168.1.106:8000/health", timeout=5)
        print(f"   ✅ Local health check: {response.status_code}")
        
        response = requests.get("http://192.168.1.106:8000/api/leads/dev?test_scoring=true", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Local data retrieval: {len(data.get('items', []))} leads")
        else:
            print(f"   ❌ Local data retrieval failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Local access failed: {e}")
    
    # Test what n8n Cloud would see
    print("\n2️⃣ What N8N Cloud Will Experience:")
    print("   ⚠️ N8N Cloud cannot access 192.168.1.106:8000")
    print("   📍 Reason: 192.168.x.x is a private network address")
    print("   🌐 N8N Cloud needs a public URL to access your backend")
    
    print("\n3️⃣ Solutions for N8N Cloud Testing:")
    print("   🔧 Option A: Use ngrok to expose backend publicly")
    print("   🏠 Option B: Test with local n8n installation") 
    print("   📋 Option C: Use sample data workflow (no backend needed)")
    
    # Show the sample data that would be processed
    print("\n4️⃣ Sample Data for N8N Testing:")
    sample_leads = [
        {"id": 1, "first_name": "John", "last_name": "Doe", "company": "Tech Corp", "score": 75, "email": "john.doe@example.com"},
        {"id": 2, "first_name": "Jane", "last_name": "Smith", "company": "Design Studio Inc", "score": 85, "email": "jane.smith@example.com"},
        {"id": 3, "first_name": "Mike", "last_name": "Johnson", "company": "Marketing Solutions", "score": 90, "email": "mike.johnson@example.com"},
        {"id": 4, "first_name": "Sarah", "last_name": "Wilson", "company": "Tech Innovations", "score": 95, "email": "sarah.wilson@example.com"}
    ]
    
    print("   📊 Sample leads for workflow testing:")
    for lead in sample_leads:
        print(f"      • {lead['first_name']} {lead['last_name']} - Score: {lead['score']}")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. 🌐 For N8N Cloud: Set up ngrok or use sample data workflow")
    print(f"   2. 🏠 For Local Testing: Install n8n locally (npx n8n@latest)")
    print(f"   3. 📊 For Logic Testing: Use the sample data version of workflow")

if __name__ == "__main__":
    test_n8n_cloud_access() 