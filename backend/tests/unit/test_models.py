"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from models import User, Organization, Lead, UserRole, LeadStatus, LeadSource
from auth import get_password_hash, verify_password


@pytest.mark.unit
class TestOrganization:
    """Test Organization model."""
    
    def test_create_organization(self, db_session):
        """Test creating an organization."""
        org = Organization(
            name="Test Org",
            slug="test-org",
            description="A test organization"
        )
        db_session.add(org)
        db_session.commit()
        
        assert org.id is not None
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.is_active is True
        assert isinstance(org.created_at, datetime)
        assert isinstance(org.updated_at, datetime)
    
    def test_organization_slug_unique(self, db_session):
        """Test that organization slug must be unique."""
        org1 = Organization(name="Org 1", slug="test-org")
        org2 = Organization(name="Org 2", slug="test-org")
        
        db_session.add(org1)
        db_session.commit()
        
        db_session.add(org2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_organization_repr(self, db_session):
        """Test organization string representation."""
        org = Organization(name="Test Org", slug="test-org")
        db_session.add(org)
        db_session.commit()
        
        assert str(org) == "Test Org"


@pytest.mark.unit
class TestUser:
    """Test User model."""
    
    def test_create_user(self, db_session, test_organization):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRole.SALES_REP
        assert user.is_active is True
        assert user.organization_id == test_organization.id
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_email_unique(self, db_session, test_organization):
        """Test that user email must be unique."""
        user1 = User(
            email="test@example.com",
            username="user1",
            first_name="User",
            last_name="One",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id
        )
        user2 = User(
            email="test@example.com",
            username="user2",
            first_name="User",
            last_name="Two",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_full_name_property(self, db_session, test_organization):
        """Test user full_name property."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.full_name == "John Doe"
    
    def test_user_organization_relationship(self, db_session, test_organization):
        """Test user-organization relationship."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.organization.id == test_organization.id
        assert user.organization.name == test_organization.name


@pytest.mark.unit
class TestLead:
    """Test Lead model."""
    
    def test_create_lead(self, db_session, test_organization):
        """Test creating a lead."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="Test Company",
            job_title="CEO",
            organization_id=test_organization.id
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.id is not None
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john.doe@example.com"
        assert lead.status == LeadStatus.NEW
        assert lead.source == LeadSource.OTHER
        assert lead.organization_id == test_organization.id
        assert isinstance(lead.created_at, datetime)
        assert isinstance(lead.updated_at, datetime)
    
    def test_lead_full_name_property(self, db_session, test_organization):
        """Test lead full_name property."""
        lead = Lead(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            organization_id=test_organization.id
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.full_name == "Jane Smith"
    
    def test_lead_organization_relationship(self, db_session, test_organization):
        """Test lead-organization relationship."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            organization_id=test_organization.id
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.organization.id == test_organization.id
        assert lead.organization.name == test_organization.name
    
    def test_lead_user_assignment(self, db_session, test_organization, test_user):
        """Test lead assignment to user."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            organization_id=test_organization.id,
            assigned_to_id=test_user.id
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.assigned_to.id == test_user.id
        assert lead.assigned_to.email == test_user.email


@pytest.mark.unit
class TestEnums:
    """Test enum values."""
    
    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.MANAGER.value == "manager"
        assert UserRole.SALES_REP.value == "sales_rep"
    
    def test_lead_status_enum(self):
        """Test LeadStatus enum values."""
        assert LeadStatus.NEW.value == "new"
        assert LeadStatus.CONTACTED.value == "contacted"
        assert LeadStatus.QUALIFIED.value == "qualified"
        assert LeadStatus.PROPOSAL.value == "proposal"
        assert LeadStatus.NEGOTIATION.value == "negotiation"
        assert LeadStatus.CLOSED_WON.value == "closed_won"
        assert LeadStatus.CLOSED_LOST.value == "closed_lost"
    
    def test_lead_source_enum(self):
        """Test LeadSource enum values."""
        assert LeadSource.WEBSITE.value == "website"
        assert LeadSource.EMAIL.value == "email"
        assert LeadSource.SOCIAL_MEDIA.value == "social_media"
        assert LeadSource.REFERRAL.value == "referral"
        assert LeadSource.ADVERTISING.value == "advertising"
        assert LeadSource.OTHER.value == "other" 