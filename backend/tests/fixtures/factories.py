"""
Factory Boy factories for generating test data.
"""
import factory
from faker import Faker
from sqlalchemy.orm import Session

from models import User, Organization, Lead, UserRole, LeadStatus, LeadSource
from auth import get_password_hash

fake = Faker()


class OrganizationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Organization instances."""
    
    class Meta:
        model = Organization
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-").replace(",", "").replace(".", ""))
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
    role = UserRole.USER
    is_active = True
    organization = factory.SubFactory(OrganizationFactory)
    organization_id = factory.LazyAttribute(lambda obj: obj.organization.id)


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""
    role = UserRole.ADMIN


class ManagerUserFactory(UserFactory):
    """Factory for creating manager User instances."""
    role = UserRole.MANAGER


class LeadFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Lead instances."""
    
    class Meta:
        model = Lead
        sqlalchemy_session_persistence = "commit"
    
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    company = factory.Faker("company")
    position = factory.Faker("job")
    source = factory.Faker("random_element", elements=[s.value for s in LeadSource])
    status = factory.Faker("random_element", elements=[s.value for s in LeadStatus])
    notes = factory.Faker("text", max_nb_chars=500)
    organization = factory.SubFactory(OrganizationFactory)
    organization_id = factory.LazyAttribute(lambda obj: obj.organization.id)


# Helper functions for setting up factories with sessions
def setup_factories(session: Session):
    """Set up factory sessions."""
    OrganizationFactory._meta.sqlalchemy_session = session
    UserFactory._meta.sqlalchemy_session = session
    AdminUserFactory._meta.sqlalchemy_session = session
    ManagerUserFactory._meta.sqlalchemy_session = session
    LeadFactory._meta.sqlalchemy_session = session


def create_test_organization(session: Session, **kwargs) -> Organization:
    """Create a test organization with custom attributes."""
    setup_factories(session)
    return OrganizationFactory(**kwargs)


def create_test_user(session: Session, organization: Organization = None, **kwargs) -> User:
    """Create a test user with custom attributes."""
    setup_factories(session)
    if organization:
        kwargs['organization'] = organization
        kwargs['organization_id'] = organization.id
    return UserFactory(**kwargs)


def create_test_admin(session: Session, organization: Organization = None, **kwargs) -> User:
    """Create a test admin user with custom attributes."""
    setup_factories(session)
    if organization:
        kwargs['organization'] = organization
        kwargs['organization_id'] = organization.id
    return AdminUserFactory(**kwargs)


def create_test_manager(session: Session, organization: Organization = None, **kwargs) -> User:
    """Create a test manager user with custom attributes."""
    setup_factories(session)
    if organization:
        kwargs['organization'] = organization
        kwargs['organization_id'] = organization.id
    return ManagerUserFactory(**kwargs)


def create_test_lead(session: Session, organization: Organization = None, **kwargs) -> Lead:
    """Create a test lead with custom attributes."""
    setup_factories(session)
    if organization:
        kwargs['organization'] = organization
        kwargs['organization_id'] = organization.id
    return LeadFactory(**kwargs) 