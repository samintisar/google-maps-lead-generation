"""
Main FastAPI application for the Lead Management Application (LMA).
Updated to use domain-driven architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.db.database import create_tables
# from app.core.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware

# Import domain routers
from app.domains.lead_management.router import router as lead_management_router
from app.domains.campaign_management.router import router as campaign_management_router
from app.domains.workflow_execution.router import router as workflow_execution_router
from app.domains.analytics.router import router as analytics_router

# Import legacy routers for backward compatibility
from app.api.v1 import organizations, users, leads, campaigns

# Create FastAPI app
app = FastAPI(
    title="Lead Management Application API",
    description="A domain-driven lead management system with unified activity tracking, workflows, and analytics",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
# app.add_middleware(ErrorHandlingMiddleware)
# app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:15173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:15173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include domain routers
app.include_router(lead_management_router, prefix="/api/v1", tags=["Lead Management"])
app.include_router(campaign_management_router, prefix="/api/v1", tags=["Campaign Management"])
app.include_router(workflow_execution_router, prefix="/api/v1/workflows", tags=["Workflow Execution"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

# Include legacy routers for backward compatibility
app.include_router(organizations.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    create_tables()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Lead Management Application API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "architecture": "domain-driven"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "architecture": "domain-driven"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=18000,
        reload=True
    )