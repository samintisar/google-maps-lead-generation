#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import base64

def get_fresh_token():
    """Get a fresh authentication token"""
    print("🔐 Getting fresh authentication token...")
    
    auth_data = {"username": "dev@example.com", "password": "password"}
    
    try:
        response = requests.post("http://localhost:8000/api/auth/login", json=auth_data)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            
            print(f"✅ Fresh Bearer Token:")
            print(f"Bearer {token}")
            
            # Try to decode token info
            try:
                parts = token.split('.')
                if len(parts) >= 2:
                    # Add padding if needed
                    payload = parts[1]
                    padding = len(payload) % 4
                    if padding:
                        payload += '=' * (4 - padding)
                    decoded = base64.b64decode(payload)
                    payload_json = json.loads(decoded)
                    exp = payload_json.get('exp', 0)
                    sub = payload_json.get('sub', 'unknown')
                    exp_time = datetime.fromtimestamp(exp)
                    print(f"📅 Token subject: {sub}")
                    print(f"📅 Token expires at: {exp_time}")
                    
                    return f"Bearer {token}"
            except Exception as e:
                print(f"ℹ️ Could not decode token details: {e}")
                return f"Bearer {token}"
                
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

if __name__ == "__main__":
    token = get_fresh_token()
    if token:
        print(f"\n🎯 Use this token in n8n: {token}")
    else:
        print("\n❌ Could not get fresh token") 