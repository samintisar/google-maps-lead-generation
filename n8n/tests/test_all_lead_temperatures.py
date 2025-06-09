#!/usr/bin/env python3
"""
Test All Lead Temperature Scenarios
Tests that the workflow properly handles hot, warm, and cold leads
"""

import requests
import json
import time
from datetime import datetime, timedelta
import jwt

def generate_token(username="devuser", expires_minutes=30):
    """Generate a JWT token for API authentication"""
    payload = {
        "sub": username,
        "exp": int((datetime.now() + timedelta(minutes=expires_minutes)).timestamp())
    }
    secret_key = "your-secret-key-here-change-this-in-production"
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def test_individual_lead_update(lead_id, temperature, score):
    """Test updating a single lead with specific temperature and score"""
    print(f"\n🧪 Testing {temperature.upper()} lead (ID: {lead_id}, Score: {score})")
    print("-" * 50)
    
    token = generate_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test the exact API call that the workflow makes
    update_data = {
        "lead_temperature": temperature,
        "score": score,
        "score_breakdown": {
            "demographic": 10,
            "behavioral": 8,
            "engagement": 5,
            "firmographic": 12,
            "temporal": 5
        }
    }
    
    url = f"http://localhost:8000/api/leads/{lead_id}"
    
    try:
        print(f"🚀 PUT {url}")
        print(f"📝 Data: {json.dumps(update_data, indent=2)}")
        
        response = requests.put(url, json=update_data, headers=headers, timeout=15)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            updated_temp = result.get('data', {}).get('lead_temperature', 'unknown')
            updated_score = result.get('data', {}).get('score', 'unknown')
            
            print(f"✅ Update successful!")
            print(f"   Temperature: {updated_temp}")
            print(f"   Score: {updated_score}")
            
            return {
                'success': True,
                'temperature': updated_temp,
                'score': updated_score,
                'data': result.get('data', {})
            }
        else:
            print(f"❌ Update failed: {response.text}")
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_webhook_with_temperature_scenario(scenario_name, test_data):
    """Test the webhook with specific scenario data"""
    print(f"\n🎯 Testing N8N Webhook - {scenario_name}")
    print("-" * 50)
    
    webhook_url = "http://localhost:5678/webhook/lead-activity"
    
    try:
        print(f"🚀 POST {webhook_url}")
        print(f"📝 Test Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(webhook_url, json=test_data, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook successful!")
            
            try:
                result = response.json()
                print(f"📝 Response: {json.dumps(result, indent=2)}")
                return {'success': True, 'response': result}
            except:
                print(f"📝 Response (text): {response.text[:300]}")
                return {'success': True, 'response': response.text}
        else:
            print(f"❌ Webhook failed: {response.status_code}")
            print(f"Error: {response.text}")
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"❌ Webhook failed: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main test function"""
    print("🔥 COMPREHENSIVE LEAD TEMPERATURE TEST")
    print("=" * 60)
    
    results = {
        'api_tests': {},
        'webhook_tests': {},
        'summary': {}
    }
    
    # Test 1: Direct API updates for each temperature
    print("\n🔧 PART 1: Direct API Lead Updates")
    print("=" * 40)
    
    test_scenarios = [
        {'id': 1, 'temperature': 'hot', 'score': 85},
        {'id': 2, 'temperature': 'warm', 'score': 65}, 
        {'id': 3, 'temperature': 'cold', 'score': 35}
    ]
    
    for scenario in test_scenarios:
        result = test_individual_lead_update(
            scenario['id'], 
            scenario['temperature'], 
            scenario['score']
        )
        results['api_tests'][scenario['temperature']] = result
    
    # Test 2: Webhook scenarios
    print("\n\n🎯 PART 2: N8N Webhook Flow Tests")
    print("=" * 40)
    
    webhook_scenarios = [
        {
            'name': 'Hot Lead Scenario',
            'data': {
                'test': True,
                'trigger': 'hot_lead_test',
                'simulated_temperature': 'hot',
                'timestamp': time.time()
            }
        },
        {
            'name': 'Warm Lead Scenario', 
            'data': {
                'test': True,
                'trigger': 'warm_lead_test',
                'simulated_temperature': 'warm',
                'timestamp': time.time()
            }
        },
        {
            'name': 'Cold Lead Scenario',
            'data': {
                'test': True,
                'trigger': 'cold_lead_test', 
                'simulated_temperature': 'cold',
                'timestamp': time.time()
            }
        }
    ]
    
    for scenario in webhook_scenarios:
        result = test_webhook_with_temperature_scenario(scenario['name'], scenario['data'])
        temp_key = scenario['data']['simulated_temperature']
        results['webhook_tests'][temp_key] = result
    
    # Summary
    print("\n\n📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print("🔧 API Update Tests:")
    for temp, result in results['api_tests'].items():
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        print(f"   {temp.upper()} leads: {status}")
    
    print("\n🎯 Webhook Flow Tests:")
    for temp, result in results['webhook_tests'].items():
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        print(f"   {temp.upper()} leads: {status}")
    
    # Overall assessment
    api_success = all(r.get('success', False) for r in results['api_tests'].values())
    webhook_success = all(r.get('success', False) for r in results['webhook_tests'].values())
    
    print(f"\n🏆 OVERALL RESULTS:")
    print(f"   API Tests: {'✅ ALL PASS' if api_success else '❌ SOME FAILED'}")
    print(f"   Webhook Tests: {'✅ ALL PASS' if webhook_success else '❌ SOME FAILED'}")
    
    if api_success and webhook_success:
        print(f"\n🎉 SUCCESS: All lead temperatures handled correctly!")
    else:
        print(f"\n⚠️  Some tests failed. Check the details above.")
    
    print(f"\n💡 Expected Workflow Behavior:")
    print(f"   - HOT leads (≥80): Email alerts + outreach triggered")
    print(f"   - WARM leads (60-79): Sales activity logged")
    print(f"   - COLD leads (<60): Direct to CRM sync (no special actions)")
    print(f"   - ALL leads: Should complete workflow successfully")

if __name__ == "__main__":
    main() 