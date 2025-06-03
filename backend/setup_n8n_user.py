"""
Script to set up n8n user with proper credentials.
"""
import asyncio
import httpx
import json
from config import Settings

async def setup_n8n_user():
    """Set up n8n user if not exists."""
    settings = Settings()
    base_url = "http://localhost:5678"
    
    async with httpx.AsyncClient() as client:
        try:
            # Check if setup is needed
            response = await client.get(f"{base_url}/rest/owner/setup")
            if response.status_code == 200:
                # Setup is needed, create the owner
                print("Setting up n8n owner...")
                setup_data = {
                    "email": settings.n8n_email,
                    "firstName": "Admin",
                    "lastName": "User", 
                    "password": settings.n8n_password
                }
                
                response = await client.post(f"{base_url}/rest/owner/setup", json=setup_data)
                if response.status_code == 200:
                    print(f"✅ Successfully created owner: {settings.n8n_email}")
                else:
                    print(f"❌ Failed to create owner: {response.status_code} - {response.text}")
                    
            else:
                print("n8n is already set up, testing login...")
                
            # Test login with the credentials
            login_data = {
                "emailOrLdapLoginId": settings.n8n_email,
                "password": settings.n8n_password
            }
            
            response = await client.post(f"{base_url}/rest/login", json=login_data)
            if response.status_code == 200:
                print(f"✅ Successfully logged in as: {settings.n8n_email}")
                print("Credentials are working correctly!")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_n8n_user()) 