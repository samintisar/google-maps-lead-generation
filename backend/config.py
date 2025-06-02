"""
Core configuration settings for the LMA backend.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    database_url: str = "postgresql://lma_user:lma_password@postgres:5432/lma_db"
    
    # Redis settings
    redis_url: str = "redis://redis:6379"
    
    # n8n settings
    n8n_webhook_url: str = "http://n8n:5678/webhook"
    n8n_api_base_url: str = "http://n8n:5678/api/v1"
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application settings
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
