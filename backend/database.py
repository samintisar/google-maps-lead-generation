"""
Database configuration and connection management.
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from config import settings

# SQLAlchemy setup
database_url = settings.get_database_url()
engine = create_engine(
    database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup with fallback
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
except Exception:
    # Mock Redis client for development
    class MockRedis:
        def ping(self): return True
        def get(self, key): return None
        def set(self, key, value, ex=None): return True
        def delete(self, key): return True
    redis_client = MockRedis()

# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis dependency  
def get_redis():
    """Get Redis client."""
    return redis_client
