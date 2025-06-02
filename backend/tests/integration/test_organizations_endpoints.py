"""
Integration tests for organizations API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from models import Organization, UserRole


@pytest.mark.integration
class TestCreateOrganization:
    """Test organization creation endpoints."""
    
    def test_create_organization_success_admin(self, client: TestClient, admin_auth_headers):
        """Test successful organization creation by admin."""
        org_data = {
            "name": "New Test Organization",
            "slug": "new-test-org",
            "description": "A new test organization"
        }
        
        response = client.post("/api/organizations/", json=org_data, headers=admin_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Test Organization"
        assert data["data"]["slug"] == "new-test-org"
        assert data["data"]["description"] == "A new test organization"
        assert data["data"]["is_active"] is True
    
    def test_create_organization_forbidden_non_admin(self, client: TestClient, auth_headers):
        """Test organization creation forbidden for non-admin users."""
        org_data = {
            "name": "New Test Organization",
            "slug": "new-test-org",
            "description": "A new test organization"
        }
        
        response = client.post("/api/organizations/", json=org_data, headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Only administrators can create organizations"
    
    def test_create_organization_duplicate_slug(self, client: TestClient, admin_auth_headers, test_organization):
        """Test creating organization with duplicate slug."""
        org_data = {
            "name": "Another Organization",
            "slug": test_organization.slug,  # Same slug as existing org
            "description": "Another test organization"
        }
        
        response = client.post("/api/organizations/", json=org_data, headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Organization with this slug already exists"
    
    def test_create_organization_unauthorized(self, client: TestClient):
        """Test organization creation without authentication."""
        org_data = {
            "name": "New Test Organization",
            "slug": "new-test-org"
        }
        
        response = client.post("/api/organizations/", json=org_data)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestGetOrganizations:
    """Test organization listing endpoints."""
    
    def test_get_organizations_admin(self, client: TestClient, admin_auth_headers, test_organization):
        """Test admin can see all organizations."""
        response = client.get("/api/organizations/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert len(data["items"]) > 0
        
        # Check that test organization is in the response
        org_names = [org["name"] for org in data["items"]]
        assert test_organization.name in org_names
    
    def test_get_organizations_user_own_only(self, client: TestClient, auth_headers, test_organization):
        """Test non-admin user can only see their own organization."""
        response = client.get("/api/organizations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == test_organization.id
        assert data["items"][0]["name"] == test_organization.name
    
    def test_get_organizations_with_search(self, client: TestClient, admin_auth_headers, test_organization):
        """Test organizations retrieval with search."""
        search_term = test_organization.name[:5]  # First 5 characters
        response = client.get(f"/api/organizations/?search={search_term}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Should find our test organization
        org_names = [org["name"] for org in data["items"]]
        assert any(search_term.lower() in name.lower() for name in org_names)
    
    def test_get_organizations_active_only(self, client: TestClient, admin_auth_headers):
        """Test organizations retrieval filtering active only."""
        response = client.get("/api/organizations/?active_only=true", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # All returned organizations should be active
        for org in data["items"]:
            assert org["is_active"] is True
    
    def test_get_organizations_unauthorized(self, client: TestClient):
        """Test organizations retrieval without authentication."""
        response = client.get("/api/organizations/")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestGetOrganization:
    """Test individual organization retrieval."""
    
    def test_get_organization_success_admin(self, client: TestClient, admin_auth_headers, test_organization):
        """Test admin can access any organization."""
        response = client.get(f"/api/organizations/{test_organization.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_organization.id
        assert data["name"] == test_organization.name
        assert data["slug"] == test_organization.slug
    
    def test_get_organization_success_user_own(self, client: TestClient, auth_headers, test_organization):
        """Test user can access their own organization."""
        response = client.get(f"/api/organizations/{test_organization.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_organization.id
        assert data["name"] == test_organization.name
    
    def test_get_organization_forbidden_user_other(self, client: TestClient, auth_headers, db_session):
        """Test user cannot access other organizations."""
        # Create another organization
        other_org = Organization(name="Other Org", slug="other-org")
        db_session.add(other_org)
        db_session.commit()
        
        response = client.get(f"/api/organizations/{other_org.id}", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Access denied to this organization"
    
    def test_get_organization_not_found(self, client: TestClient, admin_auth_headers):
        """Test organization retrieval with invalid ID."""
        response = client.get("/api/organizations/99999", headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Organization not found"
    
    def test_get_organization_unauthorized(self, client: TestClient, test_organization):
        """Test organization retrieval without authentication."""
        response = client.get(f"/api/organizations/{test_organization.id}")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
class TestUpdateOrganization:
    """Test organization update endpoints."""
    
    def test_update_organization_success_admin(self, client: TestClient, admin_auth_headers, test_organization):
        """Test admin can update any organization."""
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/organizations/{test_organization.id}", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Organization Name"
        assert data["data"]["description"] == "Updated description"
        # Slug should remain unchanged
        assert data["data"]["slug"] == test_organization.slug
    
    def test_update_organization_success_manager_own(self, client: TestClient, manager_auth_headers, test_organization):
        """Test manager can update their own organization."""
        update_data = {
            "description": "Manager updated description"
        }
        
        response = client.put(f"/api/organizations/{test_organization.id}", json=update_data, headers=manager_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["description"] == "Manager updated description"
    
    def test_update_organization_forbidden_user(self, client: TestClient, auth_headers, test_organization):
        """Test regular user cannot update organization."""
        update_data = {"name": "Unauthorized Update"}
        
        response = client.put(f"/api/organizations/{test_organization.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Insufficient permissions to update this organization"
    
    def test_update_organization_not_found(self, client: TestClient, admin_auth_headers):
        """Test updating non-existent organization."""
        update_data = {"name": "Updated Name"}
        
        response = client.put("/api/organizations/99999", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Organization not found"


@pytest.mark.integration
class TestDeleteOrganization:
    """Test organization deletion endpoints."""
    
    def test_delete_organization_success_admin(self, client: TestClient, admin_auth_headers, db_session):
        """Test admin can delete organization without users."""
        # Create organization without users
        empty_org = Organization(name="Empty Org", slug="empty-org")
        db_session.add(empty_org)
        db_session.commit()
        
        response = client.delete(f"/api/organizations/{empty_org.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Organization deleted successfully"
        
        # Verify organization is deleted
        get_response = client.get(f"/api/organizations/{empty_org.id}", headers=admin_auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_organization_forbidden_non_admin(self, client: TestClient, auth_headers, test_organization):
        """Test non-admin cannot delete organization."""
        response = client.delete(f"/api/organizations/{test_organization.id}", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Only administrators can delete organizations"
    
    def test_delete_organization_with_users(self, client: TestClient, admin_auth_headers, test_organization):
        """Test cannot delete organization with existing users."""
        response = client.delete(f"/api/organizations/{test_organization.id}", headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Cannot delete organization with existing users"
    
    def test_delete_organization_not_found(self, client: TestClient, admin_auth_headers):
        """Test deleting non-existent organization."""
        response = client.delete("/api/organizations/99999", headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Organization not found"


@pytest.mark.integration
class TestOrganizationActivation:
    """Test organization activation/deactivation endpoints."""
    
    def test_deactivate_organization_success_admin(self, client: TestClient, admin_auth_headers, test_organization):
        """Test admin can deactivate organization."""
        response = client.patch(f"/api/organizations/{test_organization.id}/deactivate", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is False
        assert data["message"] == "Organization deactivated successfully"
    
    def test_activate_organization_success_admin(self, client: TestClient, admin_auth_headers, test_organization, db_session):
        """Test admin can activate organization."""
        # First deactivate the organization
        test_organization.is_active = False
        db_session.commit()
        
        response = client.patch(f"/api/organizations/{test_organization.id}/activate", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is True
        assert data["message"] == "Organization activated successfully"
    
    def test_deactivate_organization_forbidden_non_admin(self, client: TestClient, auth_headers, test_organization):
        """Test non-admin cannot deactivate organization."""
        response = client.patch(f"/api/organizations/{test_organization.id}/deactivate", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Only administrators can deactivate organizations"
    
    def test_activate_organization_forbidden_non_admin(self, client: TestClient, auth_headers, test_organization):
        """Test non-admin cannot activate organization."""
        response = client.patch(f"/api/organizations/{test_organization.id}/activate", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Only administrators can activate organizations" 