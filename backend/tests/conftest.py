"""
Test configuration and fixtures for the LMA API testing suite.
"""
import os
import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from httpx import AsyncClient
from unittest.mock import Mock

# Set test environment before any imports
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from database import Base, get_db, get_redis
from main import app
from models import User, Organization, Lead, UserRole
from auth import get_password_hash

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    mock = Mock()
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.get.return_value = None
    return mock


def override_get_redis(mock_redis):
    """Override the get_redis dependency."""
    def _get_redis():
        return mock_redis
    return _get_redis


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


def override_get_db(db_session: Session):
    """Override the get_db dependency."""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db


@pytest.fixture
def client(db_session: Session, mock_redis) -> TestClient:
    """Create a test client with database and Redis dependency overrides."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_redis] = override_get_redis(mock_redis)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        description="A test organization for testing"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_user(db_session: Session, test_organization: Organization) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("testpassword123"),
        organization_id=test_organization.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session, test_organization: Organization) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN,
        organization_id=test_organization.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def manager_user(db_session: Session, test_organization: Organization) -> User:
    """Create a test manager user."""
    user = User(
        email="manager@example.com",
        username="manageruser",
        first_name="Manager",
        last_name="User",
        hashed_password=get_password_hash("managerpassword123"),
        role=UserRole.MANAGER,
        organization_id=test_organization.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_lead(db_session: Session, test_organization: Organization) -> Lead:
    """Create a test lead."""
    lead = Lead(
        first_name="Test",
        last_name="Lead",
        email="testlead@example.com",
        phone="+1234567890",
        company="Test Lead Company",
        organization_id=test_organization.id
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def auth_token(client: TestClient, test_user: User) -> str:
    """Get authentication token for test user."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def admin_auth_token(client: TestClient, admin_user: User) -> str:
    """Get authentication token for admin user."""
    login_data = {
        "username": admin_user.email,
        "password": "adminpassword123"
    }
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def manager_auth_token(client: TestClient, manager_user: User) -> str:
    """Get authentication token for manager user."""
    login_data = {
        "username": manager_user.email,
        "password": "managerpassword123"
    }
    response = client.post("/api/auth/login", json=login_data)
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Get authorization headers for regular user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_auth_headers(admin_auth_token: str) -> Dict[str, str]:
    """Get authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_auth_token}"}


@pytest.fixture
def manager_auth_headers(manager_auth_token: str) -> Dict[str, str]:
    """Get authorization headers for manager user."""
    return {"Authorization": f"Bearer {manager_auth_token}"}


# Factory functions for creating test data
def create_test_user(session: Session, organization: Organization, **kwargs) -> User:
    """Factory function to create a test user."""
    defaults = {
        "email": "factory@example.com",
        "username": "factoryuser",
        "first_name": "Factory",
        "last_name": "User",
        "hashed_password": get_password_hash("factorypassword123"),
        "organization_id": organization.id
    }
    defaults.update(kwargs)
    
    user = User(**defaults)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_test_lead(session: Session, organization: Organization, **kwargs) -> Lead:
    """Factory function to create a test lead."""
    defaults = {
        "first_name": "Factory",
        "last_name": "Lead",
        "email": "factorylead@example.com",
        "organization_id": organization.id
    }
    defaults.update(kwargs)
    
    lead = Lead(**defaults)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead 