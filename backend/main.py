from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import os
import asyncio

# Import database and models
from database import engine, Base
from models import User, Organization, Lead, WorkflowExecution, ActivityLog

# Import routers
from routers.auth import router as auth_router
from routers.leads import router as leads_router
from routers.organizations import router as organizations_router
# Legacy enrichment router removed - now using workflows
from routers.metrics import router as metrics_router
from routers.sales import router as sales_router
from routers.workflows import router as workflows_router
from routers.google_maps_workflow import router as google_maps_workflow_router

# Import analytics router
try:
    from routers.analytics import router as analytics_router
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Analytics system not available: {e}")
    analytics_router = None
    ANALYTICS_AVAILABLE = False

# Import automation system (conditionally)
# Temporarily disabled for testing
AUTOMATION_AVAILABLE = False
automation_router = None
webhooks_router = None
# try:
#     from routers.automation import router as automation_router, init_automation_system
#     from routers.webhooks import router as webhooks_router, init_webhook_system
#     AUTOMATION_AVAILABLE = True
# except ImportError as e:
#     print(f"Warning: Automation system not available: {e}")
#     automation_router = None
#     webhooks_router = None
#     AUTOMATION_AVAILABLE = False

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
    description="Analytics-focused FastAPI backend for the Python automation-powered LMA Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set app info metric
APP_INFO.labels(version="1.0.0", environment=os.getenv("ENVIRONMENT", "development")).set(1)

# Configure CORS - Allow specific origins with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:15173",  # Frontend development
        "http://localhost:15174",  # Frontend production  
        "http://127.0.0.1:15173",  # Alternative localhost format
        "http://127.0.0.1:15174",  # Alternative localhost format
    ],
    allow_credentials=True,  # Enable credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(organizations_router, prefix="/api")
# Legacy enrichment router removed - now using workflows
app.include_router(metrics_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(workflows_router)
app.include_router(google_maps_workflow_router)

# Include analytics router if available
if ANALYTICS_AVAILABLE and analytics_router:
    app.include_router(analytics_router, prefix="/api")

# Include automation routers if available
if AUTOMATION_AVAILABLE:
    if automation_router:
        app.include_router(automation_router, prefix="/api")
    if webhooks_router:
        app.include_router(webhooks_router, prefix="/api")

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

@app.on_event("startup")
async def startup_event():
    """Initialize the automation system and webhook system on startup"""
    if AUTOMATION_AVAILABLE:
        try:
            database_url = os.getenv("DATABASE_URL", "postgresql://lma_user:lma_password@localhost:15432/lma_db")
            
            # Initialize automation system first
            # automation_engine = await init_automation_system(database_url)
            
            # Initialize webhook system with automation engine
            # await init_webhook_system(automation_engine)
            
            print("✅ Automation and webhook systems initialized successfully")
            
        except Exception as e:
            print(f"Warning: Failed to initialize automation/webhook systems: {e}")
            # Don't fail startup if initialization fails
    else:
        print("✅ Backend started successfully - Automation system disabled for testing")

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
