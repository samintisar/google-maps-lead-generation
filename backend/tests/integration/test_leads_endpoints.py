"""
Integration tests for leads API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from models import Lead, LeadStatus, LeadSource


@pytest.mark.integration
class TestCreateLead:
    """Test lead creation endpoints."""
    
    def test_create_lead_success(self, client: TestClient, auth_headers, test_organization):
        """Test successful lead creation."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "company": "Test Company",
            "position": "CEO",
            "source": "website",
            "status": "new",
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/leads/", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "John"
        assert data["data"]["last_name"] == "Doe"
        assert data["data"]["email"] == "john.doe@example.com"
        assert data["data"]["company"] == "Test Company"
        assert data["data"]["organization_id"] == test_organization.id
    
    def test_create_lead_duplicate_email(self, client: TestClient, auth_headers, test_lead):
        """Test creating lead with duplicate email in same organization."""
        lead_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": test_lead.email,  # Same email as existing lead
            "organization_id": test_lead.organization_id
        }
        
        response = client.post("/api/leads/", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Lead with this email already exists in the organization"
    
    def test_create_lead_invalid_organization(self, client: TestClient, auth_headers):
        """Test creating lead with invalid organization."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "organization_id": 99999
        }
        
        response = client.post("/api/leads/", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Organization not found"
    
    def test_create_lead_unauthorized(self, client: TestClient, test_organization):
        """Test creating lead without authentication."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/leads/", json=lead_data)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"
    
    def test_create_lead_missing_required_fields(self, client: TestClient, auth_headers, test_organization):
        """Test creating lead with missing required fields."""
        lead_data = {
            "first_name": "John",
            # Missing last_name, email
            "organization_id": test_organization.id
        }
        
        response = client.post("/api/leads/", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 422


@pytest.mark.integration
class TestGetLeads:
    """Test lead listing endpoints."""
    
    def test_get_leads_success(self, client: TestClient, auth_headers, test_lead):
        """Test successful leads retrieval."""
        response = client.get("/api/leads/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert len(data["items"]) > 0
        
        # Check that our test lead is in the response
        lead_emails = [lead["email"] for lead in data["items"]]
        assert test_lead.email in lead_emails
    
    def test_get_leads_with_pagination(self, client: TestClient, auth_headers, test_lead):
        """Test leads retrieval with pagination."""
        response = client.get("/api/leads/?skip=0&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_get_leads_with_status_filter(self, client: TestClient, auth_headers, test_lead):
        """Test leads retrieval with status filter."""
        response = client.get(f"/api/leads/?status_filter={test_lead.status.value}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # All returned leads should have the filtered status
        for lead in data["items"]:
            assert lead["status"] == test_lead.status.value
    
    def test_get_leads_with_source_filter(self, client: TestClient, auth_headers, test_lead):
        """Test leads retrieval with source filter."""
        response = client.get(f"/api/leads/?source_filter={test_lead.source.value}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # All returned leads should have the filtered source
        for lead in data["items"]:
            assert lead["source"] == test_lead.source.value
    
    def test_get_leads_with_search(self, client: TestClient, auth_headers, test_lead):
        """Test leads retrieval with search."""
        search_term = test_lead.first_name
        response = client.get(f"/api/leads/?search={search_term}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Should find our test lead
        lead_names = [f"{lead['first_name']} {lead['last_name']}" for lead in data["items"]]
        assert any(search_term in name for name in lead_names)
    
    def test_get_leads_unauthorized(self, client: TestClient):
        """Test leads retrieval without authentication."""
        response = client.get("/api/leads/")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestGetLead:
    """Test individual lead retrieval."""
    
    def test_get_lead_success(self, client: TestClient, auth_headers, test_lead):
        """Test successful lead retrieval."""
        response = client.get(f"/api/leads/{test_lead.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_lead.id
        assert data["email"] == test_lead.email
        assert data["first_name"] == test_lead.first_name
        assert data["last_name"] == test_lead.last_name
    
    def test_get_lead_not_found(self, client: TestClient, auth_headers):
        """Test lead retrieval with invalid ID."""
        response = client.get("/api/leads/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Lead not found"
    
    def test_get_lead_unauthorized(self, client: TestClient, test_lead):
        """Test lead retrieval without authentication."""
        response = client.get(f"/api/leads/{test_lead.id}")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestUpdateLead:
    """Test lead update endpoints."""
    
    def test_update_lead_success(self, client: TestClient, auth_headers, test_lead):
        """Test successful lead update."""
        update_data = {
            "first_name": "Updated",
            "company": "Updated Company"
        }
        
        response = client.put(f"/api/leads/{test_lead.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["company"] == "Updated Company"
        # Other fields should remain unchanged
        assert data["data"]["last_name"] == test_lead.last_name
        assert data["data"]["email"] == test_lead.email
    
    def test_update_lead_not_found(self, client: TestClient, auth_headers):
        """Test updating non-existent lead."""
        update_data = {"first_name": "Updated"}
        
        response = client.put("/api/leads/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Lead not found"
    
    def test_update_lead_unauthorized(self, client: TestClient, test_lead):
        """Test lead update without authentication."""
        update_data = {"first_name": "Updated"}

        response = client.put(f"/api/leads/{test_lead.id}", json=update_data)

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestDeleteLead:
    """Test lead deletion endpoints."""
    
    def test_delete_lead_success(self, client: TestClient, auth_headers, test_lead):
        """Test successful lead deletion."""
        response = client.delete(f"/api/leads/{test_lead.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Lead deleted successfully"
        
        # Verify lead is actually deleted
        get_response = client.get(f"/api/leads/{test_lead.id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_lead_not_found(self, client: TestClient, auth_headers):
        """Test deleting non-existent lead."""
        response = client.delete("/api/leads/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Lead not found"
    
    def test_delete_lead_unauthorized(self, client: TestClient, test_lead):
        """Test lead deletion without authentication."""
        response = client.delete(f"/api/leads/{test_lead.id}")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestLeadStatusUpdate:
    """Test lead status update endpoints."""
    
    def test_update_lead_status_success(self, client: TestClient, auth_headers, test_lead):
        """Test successful lead status update."""
        new_status = LeadStatus.CONTACTED
        
        response = client.patch(
            f"/api/leads/{test_lead.id}/status?new_status={new_status.value}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == new_status.value
        assert f"Lead status updated to {new_status.value}" in data["message"]
    
    def test_update_lead_status_not_found(self, client: TestClient, auth_headers):
        """Test updating status of non-existent lead."""
        new_status = LeadStatus.CONTACTED
        
        response = client.patch(
            f"/api/leads/99999/status?new_status={new_status.value}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Lead not found"


@pytest.mark.integration
class TestLeadAssignment:
    """Test lead assignment endpoints."""
    
    def test_assign_lead_success(self, client: TestClient, auth_headers, test_lead, test_user):
        """Test successful lead assignment."""
        response = client.patch(
            f"/api/leads/{test_lead.id}/assign?user_id={test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["assigned_to_id"] == test_user.id
        assert test_user.first_name in data["message"]
        assert test_user.last_name in data["message"]
    
    def test_assign_lead_invalid_user(self, client: TestClient, auth_headers, test_lead):
        """Test assigning lead to non-existent user."""
        response = client.patch(
            f"/api/leads/{test_lead.id}/assign?user_id=99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found in this organization"
    
    def test_assign_lead_not_found(self, client: TestClient, auth_headers, test_user):
        """Test assigning non-existent lead."""
        response = client.patch(
            f"/api/leads/99999/assign?user_id={test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Lead not found" 