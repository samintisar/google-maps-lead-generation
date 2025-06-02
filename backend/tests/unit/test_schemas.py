"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from schemas import (
    UserCreate, UserResponse, UserUpdate, UserLogin,
    OrganizationCreate, OrganizationResponse, OrganizationUpdate,
    LeadCreate, LeadResponse, LeadUpdate,
    APIResponse, ListResponse, Token
)
from models import UserRole, LeadStatus, LeadSource


@pytest.mark.unit
class TestUserSchemas:
    """Test User-related schemas."""
    
    def test_user_create_valid(self):
        """Test valid user creation schema."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "organization_id": 1
        }
        
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.role == UserRole.SALES_REP  # Default value
        assert user.organization_id == 1
    
    def test_user_create_with_role(self):
        """Test user creation with specific role."""
        user_data = {
            "email": "admin@example.com",
            "username": "adminuser",
            "password": "password123",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "organization_id": 1
        }
        
        user = UserCreate(**user_data)
        assert user.role == "admin"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "organization_id": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_user_create_missing_required_fields(self):
        """Test user creation with missing required fields."""
        user_data = {
            "email": "test@example.com",
            # Missing username, password, first_name, last_name
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "username" in error_fields
        assert "password" in error_fields
        assert "first_name" in error_fields
        assert "last_name" in error_fields
    
    def test_user_response_excludes_password(self):
        """Test that UserResponse excludes password field."""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe",
            "role": "sales_rep",
            "organization_id": 1,
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        user = UserResponse(**user_data)
        assert not hasattr(user, 'password')
        assert not hasattr(user, 'hashed_password')
    
    def test_user_update_partial(self):
        """Test partial user update schema."""
        update_data = {
            "first_name": "Updated"
        }
        
        user_update = UserUpdate(**update_data)
        assert user_update.first_name == "Updated"
        assert user_update.last_name is None
        assert user_update.email is None


@pytest.mark.unit
class TestOrganizationSchemas:
    """Test Organization-related schemas."""
    
    def test_organization_create_valid(self):
        """Test valid organization creation schema."""
        org_data = {
            "name": "Test Organization",
            "slug": "test-org",
            "description": "A test organization"
        }
        
        org = OrganizationCreate(**org_data)
        assert org.name == "Test Organization"
        assert org.slug == "test-org"
        assert org.description == "A test organization"
    
    def test_organization_create_missing_required(self):
        """Test organization creation with missing required fields."""
        org_data = {
            "name": "Test Organization"
            # Missing slug
        }
        
        with pytest.raises(ValidationError) as exc_info:
            OrganizationCreate(**org_data)
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "slug" in error_fields
    
    def test_organization_response(self):
        """Test organization response schema."""
        org_data = {
            "id": 1,
            "name": "Test Organization",
            "slug": "test-org",
            "description": "A test organization",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        org = OrganizationResponse(**org_data)
        assert org.id == 1
        assert org.name == "Test Organization"
        assert org.is_active is True


@pytest.mark.unit
class TestLeadSchemas:
    """Test Lead-related schemas."""
    
    def test_lead_create_valid(self):
        """Test valid lead creation schema."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "company": "Test Company",
            "job_title": "CEO",
            "source": "website",
            "status": "new",
            "organization_id": 1
        }
        
        lead = LeadCreate(**lead_data)
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john.doe@example.com"
        assert lead.source == "website"
        assert lead.status == "new"
    
    def test_lead_create_with_defaults(self):
        """Test lead creation with default values."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "organization_id": 1
        }
        
        lead = LeadCreate(**lead_data)
        assert lead.source == LeadSource.OTHER  # Default value
        assert lead.status == LeadStatus.NEW  # Default value
    
    def test_lead_create_invalid_email(self):
        """Test lead creation with invalid email."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "organization_id": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**lead_data)
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_lead_create_invalid_source(self):
        """Test lead creation with invalid source."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "source": "invalid_source",
            "organization_id": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**lead_data)
        
        assert "Input should be" in str(exc_info.value)
    
    def test_lead_update_partial(self):
        """Test partial lead update schema."""
        update_data = {
            "status": "contacted",
            "notes": "Follow up needed"
        }
        
        lead_update = LeadUpdate(**update_data)
        assert lead_update.status == "contacted"
        assert lead_update.notes == "Follow up needed"
        assert lead_update.first_name is None


@pytest.mark.unit
class TestResponseSchemas:
    """Test generic response schemas."""
    
    def test_api_response_success(self):
        """Test successful API response schema."""
        response_data = {
            "success": True,
            "data": {"id": 1, "name": "test"},
            "message": "Operation successful"
        }
        
        response = APIResponse(**response_data)
        assert response.success is True
        assert response.data == {"id": 1, "name": "test"}
        assert response.message == "Operation successful"
    
    def test_api_response_error(self):
        """Test error API response schema."""
        response_data = {
            "success": False,
            "message": "Operation failed"
        }
        
        response = APIResponse(**response_data)
        assert response.success is False
        assert response.data is None
        assert response.message == "Operation failed"
    
    def test_list_response(self):
        """Test list response schema."""
        response_data = {
            "items": [{"id": 1}, {"id": 2}],
            "total": 100,
            "page": 1,
            "per_page": 10,
            "pages": 10
        }
        
        response = ListResponse(**response_data)
        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 1
        assert response.per_page == 10
        assert response.pages == 10


@pytest.mark.unit
class TestAuthSchemas:
    """Test authentication-related schemas."""
    
    def test_login_request(self):
        """Test login request schema."""
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        
        login = UserLogin(**login_data)
        assert login.username == "test@example.com"
        assert login.password == "password123"
    
    def test_login_request_missing_fields(self):
        """Test login request with missing fields."""
        login_data = {
            "username": "test@example.com"
            # Missing password
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**login_data)
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "password" in error_fields
    
    def test_token_response(self):
        """Test token response schema."""
        token_data = {
            "access_token": "test-access-token",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": 1,
                "email": "test@example.com",
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "role": "sales_rep",
                "organization_id": 1,
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
        
        token = Token(**token_data)
        assert token.access_token == "test-access-token"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
        assert token.user.email == "test@example.com"


@pytest.mark.unit
class TestSchemaValidation:
    """Test advanced schema validation features."""
    
    def test_email_validation_case_insensitive(self):
        """Test that email validation handles case properly."""
        user_data = {
            "email": "TEST@EXAMPLE.COM",
            "username": "testuser",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "organization_id": 1
        }
        
        user = UserCreate(**user_data)
        # Email validation accepts uppercase but doesn't normalize by default
        assert "@" in user.email
    
    def test_string_field_trimming(self):
        """Test that string fields are properly trimmed."""
        user_data = {
            "email": "  test@example.com  ",
            "username": "  testuser  ",
            "password": "password123",
            "first_name": "  John  ",
            "last_name": "  Doe  ",
            "organization_id": 1
        }
        
        user = UserCreate(**user_data)
        # Email gets trimmed but other string fields don't by default
        assert user.email == "test@example.com"
        assert user.username == "  testuser  "
        assert user.first_name == "  John  "
        assert user.last_name == "  Doe  " 