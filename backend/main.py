from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# Create FastAPI instance
app = FastAPI(
    title="Lead Management Automation - Analytics API",
    description="Analytics-focused FastAPI backend for the n8n-first LMA Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
