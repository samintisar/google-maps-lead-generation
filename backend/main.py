from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import os

# Import database and models
from database import engine, Base
from models import User, Organization, Lead, WorkflowExecution, ActivityLog

# Import routers
from routers.auth import router as auth_router
from routers.leads import router as leads_router
from routers.organizations import router as organizations_router
from routers.workflows import router as workflows_router
from routers.enrichment import router as enrichment_router
from routers.metrics import router as metrics_router
from routers.sales import router as sales_router

# Create tables
Base.metadata.create_all(bind=engine)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
APP_INFO = Gauge('app_info', 'Application info', ['version', 'environment'])

# Create FastAPI instance
app = FastAPI(
    title="Lead Management Automation - Analytics API",
    description="Analytics-focused FastAPI backend for the n8n-first LMA Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set app info metric
APP_INFO.labels(version="1.0.0", environment=os.getenv("ENVIRONMENT", "development")).set(1)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server (original)
        "http://localhost:5174",  # Frontend prod build (original)
        "http://localhost:15173", # Frontend dev server (updated port)
        "http://localhost:15174", # Frontend prod build (updated port)
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",  # Alternative localhost format
        "http://127.0.0.1:5174",  # Alternative localhost format
        "http://127.0.0.1:15173", # Alternative localhost format (updated port)
        "http://127.0.0.1:15174", # Alternative localhost format (updated port)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(organizations_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(enrichment_router)
app.include_router(metrics_router, prefix="/api")
app.include_router(sales_router, prefix="/api")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect Prometheus metrics"""
    start_time = time.time()
    ACTIVE_CONNECTIONS.inc()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    ACTIVE_CONNECTIONS.dec()
    
    return response

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lead Management Automation - Analytics API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks"""
    return {"status": "healthy", "service": "lma-backend"}

@app.get("/api/v1/metrics")
async def get_metrics():
    """Get SaaS metrics - placeholder for now"""
    return {
        "mrr": 0,
        "cac": 0,
        "ltv": 0,
        "churn_rate": 0,
        "active_leads": 0,
        "conversion_rate": 0
    }

@app.get("/api/models")
async def get_models():
    """Get available models - placeholder for now"""
    return {
        "models": ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"],
        "default": "gpt-3.5-turbo"
    }

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint - placeholder for now"""
    return {
        "response": "This is a placeholder response from the Python FastAPI backend",
        "model": request.get("model", "gpt-3.5-turbo"),
        "timestamp": "2025-06-01T02:30:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
