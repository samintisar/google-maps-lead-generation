#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

def test_all_workflows():
    """Test all fixed n8n workflows"""
    
    print("🧪 TESTING ALL FIXED N8N WORKFLOWS")
    print("=" * 60)
    
    # Webhook URLs for the workflows
    workflows = {
        'Lead Scoring': {
            'url': 'http://localhost:5678/webhook/lead-activity',
            'payload': {
                "test": True,
                "trigger": "manual_test",
                "timestamp": time.time()
            },
            'expected_status': 200
        },
        'Lead Nurturing': {
            'url': 'http://localhost:5678/webhook/lead-nurturing',
            'payload': {
                "email": "test.nurturing@example.com",
                "firstName": "Test",
                "lastName": "Nurturing",
                "company": "Test Nurturing Co",
                "source": "website_test"
            },
            'expected_status': 200
        },
        'Social Media Outreach': {
            'url': 'http://localhost:5678/webhook/social-outreach',
            'payload': {
                "test_mode": True,
                "leads_to_process": 5
            },
            'expected_status': 200
        },
        'CRM Sync': {
            'url': 'http://localhost:5678/webhook/crm-webhook',
            'payload': {
                "sync_trigger": "manual_test",
                "limit": 10
            },
            'expected_status': 200
        }
    }
    
    results = {}
    
    for workflow_name, config in workflows.items():
        print(f"🔍 Testing {workflow_name}...")
        
        try:
            response = requests.post(
                config['url'],
                json=config['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=45  # Longer timeout for complex workflows
            )
            
            status = response.status_code
            
            if status == config['expected_status']:
                print(f"  ✅ {workflow_name} - PASS ({status})")
                results[workflow_name] = {'status': 'PASS', 'code': status}
                
                # Try to parse response for additional info
                try:
                    response_data = response.json()
                    if 'processed_leads' in response_data:
                        print(f"     📊 Processed {response_data['processed_leads']} leads")
                    if 'message' in response_data:
                        print(f"     💬 {response_data['message']}")
                except:
                    print(f"     📄 Response: {response.text[:100]}...")
                    
            else:
                print(f"  ❌ {workflow_name} - FAIL ({status})")
                print(f"     🔍 Error: {response.text[:200]}...")
                results[workflow_name] = {'status': 'FAIL', 'code': status, 'error': response.text[:200]}
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {workflow_name} - ERROR")
            print(f"     🔍 Exception: {e}")
            results[workflow_name] = {'status': 'ERROR', 'error': str(e)}
        
        time.sleep(2)  # Brief delay between tests
    
    # Summary
    print("\\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    total = len(results)
    
    for workflow_name, result in results.items():
        status_emoji = "✅" if result['status'] == 'PASS' else "❌"
        print(f"{status_emoji} {workflow_name}: {result['status']}")
    
    print(f"\\n📊 Overall: {passed}/{total} workflows passing")
    
    if passed == total:
        print("🎉 ALL WORKFLOWS ARE WORKING CORRECTLY!")
    else:
        print("⚠️  Some workflows need attention")
    
    return results

def test_lead_scoring_detailed():
    """Detailed test of lead scoring workflow with different scenarios"""
    
    print("\\n🎯 DETAILED LEAD SCORING TESTS")
    print("=" * 60)
    
    webhook_url = "http://localhost:5678/webhook/lead-activity"
    
    test_scenarios = [
        {
            "name": "HOT Lead Scenario",
            "payload": {
                "test": True,
                "scenario": "hot_lead",
                "trigger": "detailed_test"
            }
        },
        {
            "name": "WARM Lead Scenario", 
            "payload": {
                "test": True,
                "scenario": "warm_lead",
                "trigger": "detailed_test"
            }
        },
        {
            "name": "COLD Lead Scenario",
            "payload": {
                "test": True,
                "scenario": "cold_lead", 
                "trigger": "detailed_test"
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"🔍 Testing {scenario['name']}...")
        
        try:
            response = requests.post(
                webhook_url,
                json=scenario['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"  ✅ {scenario['name']} - PASS")
                try:
                    data = response.json()
                    if 'processed_leads' in data:
                        print(f"     📊 Processed: {data['processed_leads']} leads")
                    if 'workflow_execution' in data:
                        print(f"     🔧 Execution: {data['workflow_execution']}")
                except:
                    pass
            else:
                print(f"  ❌ {scenario['name']} - FAIL ({response.status_code})")
                print(f"     Error: {response.text[:150]}...")
                
        except Exception as e:
            print(f"  ❌ {scenario['name']} - ERROR: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("🚀 Starting comprehensive workflow testing...")
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all workflows
    results = test_all_workflows()
    
    # Detailed lead scoring test if basic test passed
    if results.get('Lead Scoring', {}).get('status') == 'PASS':
        test_lead_scoring_detailed()
    
    print("\\n✅ Testing completed!") 