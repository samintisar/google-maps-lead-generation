"""
Core configuration settings for the LMA backend.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    database_url: str = "postgresql://lma_db_owner:npg_mRQX3eAio4tL@ep-old-butterfly-a6ids19o-pooler.us-west-2.aws.neon.tech/lma_db?sslmode=require"
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None  
    postgres_password: Optional[str] = None
    
    # Redis settings
    redis_url: str = "redis://redis:6379"
    
    # n8n settings
    n8n_webhook_url: str = "https://your-n8n-cloud-instance.app.n8n.cloud/webhook"
    n8n_api_base_url: str = "https://your-n8n-cloud-instance.app.n8n.cloud/api/v1"
    n8n_email: str = "admin@lma.com"  # Default fallback - update with your n8n Cloud email
    n8n_password: str = "Admin123"    # Default fallback - update with your n8n Cloud password
    n8n_basic_auth_user: Optional[str] = None
    n8n_basic_auth_password: Optional[str] = None
    n8n_encryption_key: Optional[str] = None
    n8n_api_key: Optional[str] = None  # Add API key for n8n Cloud authentication
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: Optional[str] = None
    jwt_expiration_hours: Optional[str] = None
    
    # Workflow encryption key for credentials
    encryption_key: str = Fernet.generate_key().decode()
    
    # Application settings
    environment: str = "development"
    debug: bool = True
    
    # API Keys for AI services
    anthropic_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    
    # Frontend settings
    vite_api_url: Optional[str] = None
    vite_n8n_webhook_url: Optional[str] = None
    
    # Docker settings
    compose_project_name: Optional[str] = None
    
    def get_database_url(self) -> str:
        """Get database URL with development fallback to SQLite."""
        # Try PostgreSQL first
        if "postgres" not in self.database_url or self.environment == "development":
            # Check if we can connect to PostgreSQL
            try:
                import psycopg2
                # Try to connect to postgres
                conn = psycopg2.connect(self.database_url)
                conn.close()
                return self.database_url
            except Exception:
                # Fall back to SQLite for development
                return "sqlite:///./lma_dev.db"
        return self.database_url
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields instead of raising validation errors

# Global settings instance
settings = Settings()
