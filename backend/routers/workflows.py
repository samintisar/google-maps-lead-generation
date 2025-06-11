"""
Workflow Management API Routes

Handles lead enrichment workflow execution, credential management, 
and workflow monitoring.
"""

import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import User
from schemas import (
    WorkflowCredentialsCreate, WorkflowCredentialsUpdate, WorkflowCredentials,
    WorkflowRunRequest, WorkflowRunResponse, WorkflowStatusResponse,
    WorkflowExecution, WorkflowServiceCredentials
)
from services.enrichment_workflow_service import EnrichmentWorkflowService

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)

# Dependency to get workflow service
def get_workflow_service(db: Session = Depends(get_db)) -> EnrichmentWorkflowService:
    try:
        return EnrichmentWorkflowService(db)
    except Exception as e:
        logger.error(f"Failed to initialize EnrichmentWorkflowService: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow service initialization failed: {str(e)}")

@router.post("/credentials/{service_name}", response_model=WorkflowCredentials)
async def save_service_credentials(
    service_name: str,
    credentials: WorkflowCredentialsCreate,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Save encrypted credentials for a specific service."""
    try:
        if service_name not in ["hubspot", "openai", "google"]:
            raise HTTPException(status_code=400, detail="Invalid service name")
        
        saved_creds = await workflow_service.save_credentials(
            current_user.id, service_name, credentials.credentials
        )
        return saved_creds
    except Exception as e:
        logger.error(f"Failed to save credentials for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credentials", response_model=List[WorkflowCredentials])
async def get_user_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all stored credentials for the current user (without decrypted data)."""
    try:
        credentials = db.query(WorkflowCredentials).filter(
            WorkflowCredentials.user_id == current_user.id,
            WorkflowCredentials.is_active == True
        ).all()
        return credentials
    except Exception as e:
        logger.error(f"Failed to get user credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/credentials/{service_name}")
async def delete_service_credentials(
    service_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete credentials for a specific service."""
    try:
        credentials = db.query(WorkflowCredentials).filter(
            WorkflowCredentials.user_id == current_user.id,
            WorkflowCredentials.service_name == service_name
        ).first()
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials not found")
        
        credentials.is_active = False
        db.commit()
        
        return {"message": f"Credentials for {service_name} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete credentials for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-credentials/{service_name}")
async def test_service_credentials(
    service_name: str,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Test if stored credentials are valid for a service."""
    try:
        credentials = workflow_service.get_credentials(current_user.id, service_name)
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials not found")
        
        if service_name == "hubspot":
            # Test HubSpot API connection
            try:
                leads = await workflow_service.fetch_hubspot_leads(credentials, {"limit": 1})
                return {"status": "success", "message": "HubSpot credentials are valid", "test_result": f"Found {len(leads)} lead(s)"}
            except Exception as e:
                return {"status": "error", "message": f"HubSpot test failed: {str(e)}"}
                
        elif service_name == "openai":
            # Test OpenAI API connection
            try:
                test_data = {"email": "test@example.com", "name": "Test User"}
                enriched_data, confidence = await workflow_service.enrich_lead_with_ai(test_data, credentials)
                return {"status": "success", "message": "OpenAI credentials are valid", "test_result": f"Test enrichment confidence: {confidence}"}
            except Exception as e:
                return {"status": "error", "message": f"OpenAI test failed: {str(e)}"}
                
        elif service_name == "google":
            # For Google, we'll just validate the structure since testing requires more setup
            required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id"]
            missing_fields = [field for field in required_fields if field not in credentials]
            if missing_fields:
                return {"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}
            return {"status": "success", "message": "Google credentials structure is valid"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid service name")
            
    except Exception as e:
        logger.error(f"Failed to test credentials for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_request: WorkflowRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Start a workflow execution."""
    try:
        # Create execution record
        execution = await workflow_service.create_execution(current_user.id, workflow_request)
        
        # Run workflow in background
        background_tasks.add_task(
            workflow_service.run_lead_enrichment_workflow,
            current_user.id,
            workflow_request
        )
        
        return WorkflowRunResponse(
            execution_id=execution.id,
            status="started",
            message="Workflow started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions", response_model=List[WorkflowExecution])
async def get_user_executions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Get user's workflow execution history."""
    try:
        executions = workflow_service.get_user_executions(current_user.id, limit)
        return executions
    except Exception as e:
        logger.error(f"Failed to get user executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=WorkflowStatusResponse)
async def get_execution_status(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Get detailed status of a specific workflow execution."""
    try:
        execution = workflow_service.get_execution_status(execution_id, current_user.id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return WorkflowStatusResponse(
            execution_id=execution.id,
            status=execution.status,
            leads_processed=execution.leads_processed,
            leads_enriched=execution.leads_enriched,
            confidence_score=execution.confidence_score,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_message=execution.error_message,
            logs=execution.workflow_logs
        )
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Cancel a running workflow execution."""
    try:
        execution = workflow_service.get_execution_status(execution_id, current_user.id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed execution")
        
        await workflow_service.update_execution_status(execution_id, "cancelled")
        
        return {"message": "Execution cancelled successfully"}
    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def workflow_health_check():
    """Health check for workflow system - no authentication required."""
    try:
        from config import Settings
        settings = Settings()
        has_encryption_key = hasattr(settings, 'encryption_key')
        return {
            "status": "healthy",
            "service": "workflows",
            "encryption_configured": has_encryption_key
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "workflows",
            "error": str(e)
        }

@router.get("/template")
async def get_workflow_template():
    """Get the N8N workflow template configuration."""
    # This could return the actual N8N JSON template
    # For now, return a simplified template description
    return {
        "name": "Lead Enrichment Workflow",
        "description": "Automated lead enrichment using HubSpot, AI, and validation",
        "steps": [
            {
                "id": 1,
                "name": "HubSpot Trigger",
                "description": "Fetch new contacts from HubSpot",
                "type": "trigger"
            },
            {
                "id": 2,
                "name": "Filter Leads",
                "description": "Filter leads that need enrichment",
                "type": "filter"
            },
            {
                "id": 3,
                "name": "AI Enrichment", 
                "description": "Use OpenAI to enrich lead data",
                "type": "enrichment"
            },
            {
                "id": 4,
                "name": "Validate Data",
                "description": "Validate enriched data quality",
                "type": "validation"
            },
            {
                "id": 5,
                "name": "Update HubSpot",
                "description": "Update HubSpot with enriched data",
                "type": "update"
            },
            {
                "id": 6,
                "name": "Update Google Sheets",
                "description": "Log results to Google Sheets",
                "type": "logging"
            }
        ],
        "required_credentials": ["hubspot", "openai", "google"],
        "estimated_time": "2-5 minutes per lead"
    }

@router.get("/stats")
async def get_workflow_stats(
    current_user: User = Depends(get_current_user),
    workflow_service: EnrichmentWorkflowService = Depends(get_workflow_service)
):
    """Get workflow execution statistics for the user."""
    try:
        executions = workflow_service.get_user_executions(current_user.id, 1000)  # Get more for stats
        
        total_executions = len(executions)
        completed_executions = len([e for e in executions if e.status == "completed"])
        failed_executions = len([e for e in executions if e.status == "failed"])
        running_executions = len([e for e in executions if e.status in ["pending", "running"]])
        
        total_leads_processed = sum(e.leads_processed for e in executions)
        total_leads_enriched = sum(e.leads_enriched for e in executions)
        
        avg_confidence = None
        confidence_scores = [e.confidence_score for e in executions if e.confidence_score is not None]
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "success_rate": (completed_executions / total_executions * 100) if total_executions > 0 else 0,
            "total_leads_processed": total_leads_processed,
            "total_leads_enriched": total_leads_enriched,
            "enrichment_rate": (total_leads_enriched / total_leads_processed * 100) if total_leads_processed > 0 else 0,
            "average_confidence_score": avg_confidence
        }
    except Exception as e:
        logger.error(f"Failed to get workflow stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 