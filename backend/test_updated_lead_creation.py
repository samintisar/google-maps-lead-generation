import requests
import json

def test_updated_lead_creation():
    """Test creating a lead with all the new fields."""
    
    # Test data with all the new fields
    test_data = {
        "name": "Blue Sky Clothing: Commercial Drive",
        "company": "Blue Sky Clothing: Commercial Drive",
        "industry": "Clothing",
        "website": "https://blueskyClothingco.com/",
        "address": "1312 Commercial Dr, Vancouver, BC V5L 2T5, Canada",
        "google_maps_url": "https://www.google.com/maps/place/?q=place_id:ChIJ2xaFf19xhlQRd93kVQsxXE",
        "phone": "(604) 566-9976",
        "notes": "Generated from Google Maps workflow. Rating: 4.7 (77 reviews)",
        "source": "Google Maps Workflow",
        "status": "new",
        "organization_id": 1,
        "score": 4.7
    }
    
    print("🧪 Testing updated lead creation with all fields:")
    print(json.dumps(test_data, indent=2))
    print()
    
    try:
        response = requests.post(
            "http://localhost:18000/api/v1/leads/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Lead created with all fields!")
            lead_data = response.json()
            print(f"Created lead ID: {lead_data.get('id')}")
            
            # Verify all fields are stored
            print("\n📊 Stored lead data:")
            for key, value in lead_data.items():
                if key not in ['created_at', 'updated_at']:
                    print(f"  {key}: {value}")
                    
            # Check that new fields are present
            new_fields = ['industry', 'website', 'address', 'google_maps_url']
            missing_fields = [field for field in new_fields if field not in lead_data]
            
            if missing_fields:
                print(f"❌ Missing fields in response: {missing_fields}")
            else:
                print("✅ All new fields are present in the response!")
                
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_get_lead():
    """Test retrieving the created lead to verify data persistence."""
    print("\n" + "="*60)
    print("🔍 Testing lead retrieval to verify data persistence:")
    
    try:
        # Get the latest lead (assuming it has ID 5 based on previous tests)
        response = requests.get("http://localhost:18000/api/v1/leads/5")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Lead retrieved successfully!")
            lead_data = response.json()
            
            print("\n📊 Retrieved lead data:")
            for key, value in lead_data.items():
                if key not in ['created_at', 'updated_at']:
                    print(f"  {key}: {value}")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_updated_lead_creation()
    test_get_lead() 