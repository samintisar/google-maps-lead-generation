"""
Unit tests for authentication utilities.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    verify_token
)
from config import settings


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords generate different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "testpassword123"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to salt, hashes should be different
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode token to verify structure
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_with_expiry(self):
        """Test creating an access token with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        # Record the time before creating the token
        before_creation = datetime.utcnow()
        token = create_access_token(data, expires_delta=expires_delta)
        after_creation = datetime.utcnow()
        
        # Decode token to verify expiry
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)  # Use UTC
        
        # Token should expire between 14-16 minutes from creation time
        min_expected_exp = before_creation + timedelta(minutes=14)
        max_expected_exp = after_creation + timedelta(minutes=16)
        
        assert min_expected_exp <= exp_datetime <= max_expected_exp
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload["sub"] == "test@example.com"
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # FastAPI HTTPException or JWTError
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(Exception):  # FastAPI HTTPException or JWTError
            verify_token(token)
    
    def test_token_contains_required_fields(self):
        """Test that tokens contain required fields."""
        data = {"sub": "test@example.com", "user_id": 123}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert "sub" in payload
        assert "user_id" in payload
        assert "exp" in payload
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 123
    
    def test_token_security_constants(self):
        """Test that security constants are properly set."""
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0
        assert settings.algorithm == "HS256"


@pytest.mark.unit
class TestAuthConfiguration:
    """Test authentication configuration."""
    
    def test_settings_loaded(self):
        """Test that settings are properly loaded."""
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'access_token_expire_minutes')
        
        # Verify default values or environment variables
        assert settings.access_token_expire_minutes > 0 