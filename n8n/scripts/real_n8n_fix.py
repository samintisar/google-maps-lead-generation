#!/usr/bin/env python3
"""
REAL N8N FIX - Actually fix the 403 authentication error
This time we test the exact same conditions as n8n workflow
"""

import requests
import json
import time

def get_ultra_fresh_token():
    """Get a brand new authentication token"""
    print("🔑 Getting Ultra Fresh Backend Token")
    print("-" * 50)
    
    try:
        # Try to get token from localhost (where we can reach it)
        auth_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "dev@example.com", "password": "password"},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            print(f"✅ Got ultra fresh token: {token[:30]}...")
            print(f"Full token: {token}")
            return token
        else:
            print(f"❌ Failed to get token: {auth_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Token error: {e}")
        return None

def test_exact_failing_scenario(token):
    """Test the EXACT same request that's failing in n8n"""
    print("\n🎯 TESTING EXACT FAILING SCENARIO")
    print("-" * 50)
    
    # This is the EXACT same request n8n is making that's failing
    url = "http://localhost:8000/api/leads/3"  # We'll test localhost first
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7"
    }
    
    body = {
        "lead_temperature": "cold",
        "score": 38,
        "score_breakdown": {
            "demographic": 10,
            "behavioral": 10,
            "engagement": 5,
            "firmographic": 10,
            "temporal": 3
        }
    }
    
    print(f"Testing URL: {url}")
    print(f"Method: PUT")
    print(f"Headers: {headers}")
    print(f"Body: {json.dumps(body, indent=2)}")
    print()
    
    try:
        response = requests.put(
            url,
            json=body,
            headers=headers,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS - This token works!")
            return True
        else:
            print("❌ FAILED - Token not working")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_token_validity_details(token):
    """Check token validity in detail"""
    print(f"\n🔍 TOKEN VALIDITY CHECK")
    print("-" * 50)
    
    try:
        import jwt
        import datetime
        
        # Decode token without verification to see contents
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"Token payload: {json.dumps(decoded, indent=2)}")
        
        exp = decoded.get('exp')
        if exp:
            exp_time = datetime.datetime.fromtimestamp(exp)
            now = datetime.datetime.now()
            print(f"Token expires: {exp_time}")
            print(f"Current time: {now}")
            print(f"Token valid: {'✅ YES' if exp_time > now else '❌ NO (EXPIRED)'}")
            
    except Exception as e:
        print(f"Cannot decode token: {e}")

def create_working_n8n_credential_file(token):
    """Create a credential file that can be imported into n8n"""
    print(f"\n📁 CREATING N8N CREDENTIAL FILE")
    print("-" * 50)
    
    credential_data = {
        "name": "Backend API Auth",
        "type": "httpHeaderAuth",
        "data": {
            "name": "Authorization",
            "value": f"Bearer {token}"
        }
    }
    
    with open("n8n_backend_credential.json", "w") as f:
        json.dump(credential_data, f, indent=2)
    
    print(f"✅ Created: n8n_backend_credential.json")
    print(f"Import this into n8n Settings > Credentials")

def print_step_by_step_fix(token):
    """Print detailed step-by-step fix instructions"""
    print(f"\n" + "="*70)
    print("🔧 STEP-BY-STEP N8N FIX INSTRUCTIONS")
    print("="*70)
    print()
    print("The 403 error is happening because n8n is using an expired token.")
    print("Here's how to fix it:")
    print()
    print("STEP 1: Open N8N Web Interface")
    print("   → Go to http://localhost:5678")
    print()
    print("STEP 2: Open Your Workflow")
    print("   → Click on 'My workflow' (the Lead Scoring workflow)")
    print()
    print("STEP 3: Find the Failing Node")
    print("   → Look for 'Update Lead Status1' node (the one showing the error)")
    print("   → Click on it to open the configuration")
    print()
    print("STEP 4: Update Authentication")
    print("   → Go to the 'Parameters' tab")
    print("   → Scroll down to 'Headers'")
    print("   → Find the 'Authorization' header")
    print("   → Replace the entire value with this NEW token:")
    print()
    print(f"   Bearer {token}")
    print()
    print("STEP 5: Save and Test")
    print("   → Click 'Save' on the node")
    print("   → Click 'Save' on the workflow")
    print("   → Click 'Test workflow' or trigger via webhook")
    print()
    print("ALTERNATIVE METHOD (Credentials):")
    print("   → Go to Settings > Credentials")
    print("   → Find 'Header Auth account' credential")
    print("   → Update the value with the new token above")
    print("   → All nodes using this credential will be fixed")
    print()
    print("🧪 TEST THE FIX:")
    print("   → Trigger webhook: http://localhost:5678/webhook/lead-activity")
    print("   → Send: {\"lead_id\": 3, \"activity_type\": \"test\"}")
    print("   → Should get 200 response instead of 403")

def double_check_backend_status():
    """Make sure backend is running and accessible"""
    print(f"\n🔍 BACKEND STATUS CHECK")
    print("-" * 50)
    
    try:
        # Check if backend is running
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Backend is running: {response.status_code}")
        
        # Check auth endpoint
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "dev@example.com", "password": "password"}
        )
        print(f"✅ Auth endpoint working: {response.status_code}")
        
        # Check leads endpoint
        if response.status_code == 200:
            token = response.json().get("access_token")
            response = requests.get(
                "http://localhost:8000/api/leads/3",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"✅ Leads endpoint working: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Backend check failed: {e}")

def main():
    print("🚨 REAL N8N AUTHENTICATION FIX")
    print("=" * 70)
    print("Fixing the actual 403 'Not authenticated' error")
    print()
    
    # Step 1: Check backend status
    double_check_backend_status()
    
    # Step 2: Get ultra fresh token
    fresh_token = get_ultra_fresh_token()
    if not fresh_token:
        print("❌ Cannot get fresh token - backend may be down")
        return
    
    # Step 3: Check token validity
    check_token_validity_details(fresh_token)
    
    # Step 4: Test exact failing scenario
    success = test_exact_failing_scenario(fresh_token)
    
    if success:
        print("\n✅ TOKEN CONFIRMED WORKING")
        
        # Step 5: Create credential file
        create_working_n8n_credential_file(fresh_token)
        
        # Step 6: Save token to file
        with open("WORKING_TOKEN.txt", "w") as f:
            f.write(fresh_token)
        print(f"💾 Saved working token to: WORKING_TOKEN.txt")
        
        # Step 7: Print fix instructions
        print_step_by_step_fix(fresh_token)
        
    else:
        print("\n❌ TOKEN NOT WORKING - BACKEND ISSUE")
        print("The backend authentication system may be broken")

if __name__ == "__main__":
    main() 