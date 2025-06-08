#!/usr/bin/env python3
import requests
import json

def test_webhook():
    """Simple webhook test"""
    url = "http://localhost:5678/webhook/lead-activity"
    data = {"test": True, "manual_trigger": True}
    
    print("🚀 Testing N8N Webhook...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print(f"📝 Raw Content: {response.content}")
        
        if response.text:
            print(f"📄 Text Response: {response.text}")
            try:
                json_response = response.json()
                print(f"🎯 JSON Response: {json.dumps(json_response, indent=2)}")
            except:
                print("❌ Not valid JSON")
        else:
            print("❌ Empty response body")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook() 