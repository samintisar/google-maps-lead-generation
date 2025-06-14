"""
Application configuration settings.
Centralized configuration management with environment variable support.
PostgreSQL/Neon database only - no SQLite support.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Lead Management Application"
    version: str = "3.0.0"
    environment: str = "development"
    debug: bool = True
    port: int = 18000
    
    # Database settings - REQUIRE PostgreSQL/Neon (no SQLite fallback)
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # API Keys (loaded from .env file)
    perplexity_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None  # Added from .env
    
    # Frontend/App configuration (from .env)
    secret_key: Optional[str] = None
    vite_api_url: Optional[str] = None
    public_api_url: Optional[str] = None
    compose_project_name: Optional[str] = None
    
    # CORS settings
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:15173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:15173"
    ]
    
    # Logging settings
    log_level: str = "INFO"
    
    # Database connection settings for PostgreSQL/Neon
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600  # 1 hour
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL (Neon) database."""
        return self.database_url.startswith(("postgresql://", "postgres://"))
    
    def __post_init__(self):
        """Validate database URL is set and is PostgreSQL only."""
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please set it in your .env file with your Neon PostgreSQL connection string."
            )
        if not self.is_postgresql:
            if self.database_url.startswith("sqlite:"):
                raise ValueError(
                    "SQLite databases are not supported. This application requires PostgreSQL/Neon. "
                    "Please update your DATABASE_URL to use a PostgreSQL connection string."
                )
            else:
                raise ValueError(
                    "Only PostgreSQL/Neon databases are supported. "
                    "DATABASE_URL must start with 'postgresql://' or 'postgres://'"
                )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()
    settings.__post_init__()
    return settings
