"""
Main FastAPI application for the Lead Management Application (LMA).
Clean, organized entry point with proper configuration and middleware.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.database import create_tables, test_connection
from app.api.v1 import organizations, users, campaigns, leads
from app.domains.workflow_execution import router as workflow_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get application settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Lead Management Application API",
    description="A modern lead management system with unified activity tracking, workflows, and analytics",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)


def configure_middleware():
    """Configure application middleware."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:15173",
            "http://localhost:15174",
            "http://localhost:15175",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:15173",
            "http://127.0.0.1:15174",
            "http://127.0.0.1:15175"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def configure_routes():
    """Configure application routes."""
    # Include API routers
    app.include_router(organizations.router, prefix="/api", tags=["Organizations"])
    app.include_router(users.router, prefix="/api", tags=["Users"])
    app.include_router(campaigns.router, prefix="/api", tags=["Campaigns"])
    app.include_router(leads.router, prefix="/api", tags=["Leads"])
    app.include_router(workflow_router, prefix="/api/v1/workflows", tags=["Workflows"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Lead Management Application...")
    
    # Test database connection first
    if not test_connection():
        logger.error("❌ Cannot connect to database. Please check your DATABASE_URL in .env file.")
        logger.error("Make sure your Neon PostgreSQL database URL is correctly set in the .env file.")
        raise Exception("Database connection failed")
    
    logger.info("✅ Database connection successful")
    
    # Create base tables if they don't exist
    create_tables()
    logger.info("✅ Database tables created/verified")
    
    logger.info("🚀 Application startup complete - Ready to serve requests!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Lead Management Application...")


@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "message": "Lead Management Application API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "environment": settings.environment,
        "database": "PostgreSQL (Neon)" if settings.is_postgresql else "Unknown"
    }


@app.get("/health")
async def simple_health_check():
    """Simple health check endpoint for Docker/monitoring."""
    return {"status": "healthy", "version": "3.0.0"}


@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint for monitoring."""
    db_status = "healthy" if test_connection() else "unhealthy"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "3.0.0",
        "environment": settings.environment,
        "database": db_status,
        "database_type": "PostgreSQL (Neon)" if settings.is_postgresql else "Unknown"
    }


# Configure the application
configure_middleware()
configure_routes()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )