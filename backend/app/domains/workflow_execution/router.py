"""
Workflow Execution Domain Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ...db.database import get_db
from .schemas import (
    Workflow, WorkflowCreate, WorkflowUpdate, 
    WorkflowExecution, WorkflowResponse,
    GoogleMapsStartRequest, EmailCampaignStartRequest, LeadScoringStartRequest
)
from .services import WorkflowService, WorkflowExecutionService

router = APIRouter()

# Workflow CRUD endpoints
@router.get("/workflows/", response_model=List[Workflow])
def get_workflows(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all workflows with optional filtering."""
    service = WorkflowService(db)
    return service.get_workflows(
        skip=skip, 
        limit=limit, 
        organization_id=organization_id, 
        user_id=user_id, 
        is_active=is_active
    )


@router.get("/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow by ID."""
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.post("/workflows/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow."""
    service = WorkflowService(db)
    return service.create_workflow(workflow)


@router.put("/workflows/{workflow_id}", response_model=Workflow)
def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update a workflow."""
    service = WorkflowService(db)
    workflow = service.update_workflow(workflow_id, workflow_update)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Delete a workflow."""
    service = WorkflowService(db)
    if not service.delete_workflow(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )


@router.post("/workflows/{workflow_id}/activate", response_model=Workflow)
def activate_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Activate a workflow."""
    service = WorkflowService(db)
    workflow = service.activate_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.post("/workflows/{workflow_id}/deactivate", response_model=Workflow)
def deactivate_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Deactivate a workflow."""
    service = WorkflowService(db)
    workflow = service.deactivate_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


# Workflow Execution endpoints
@router.get("/executions/", response_model=List[WorkflowExecution])
def get_executions(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get workflow executions with optional filtering."""
    service = WorkflowExecutionService(db)
    return service.get_executions(
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        user_id=user_id,
        status=status
    )


@router.get("/executions/{execution_id}/status", response_model=WorkflowResponse)
def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    """Get the status of a workflow execution."""
    service = WorkflowExecutionService(db)
    execution_data = service.get_execution_status(execution_id)
    
    if not execution_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found"
        )
    
    return WorkflowResponse(
        success=True,
        data=execution_data
    )


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowResponse)
def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    """Cancel a workflow execution."""
    service = WorkflowExecutionService(db)
    success = service.cancel_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found or cannot be cancelled"
        )
    
    return WorkflowResponse(
        success=True,
        message="Workflow execution cancelled successfully"
    )


# Specific Workflow Type endpoints
@router.post("/google-maps/start", response_model=WorkflowResponse)
def start_google_maps_workflow(
    request: GoogleMapsStartRequest, 
    db: Session = Depends(get_db)
):
    """Start a Google Maps lead generation workflow."""
    service = WorkflowExecutionService(db)
    # TODO: Get organization_id and user_id from authentication
    result = service.start_workflow(
        workflow_type="google-maps",
        request_data=request.dict(),
        organization_id=1,  # Placeholder
        user_id=1  # Placeholder
    )
    
    return WorkflowResponse(**result)


@router.post("/email-campaign/start", response_model=WorkflowResponse)
def start_email_campaign_workflow(
    request: EmailCampaignStartRequest, 
    db: Session = Depends(get_db)
):
    """Start an email campaign workflow."""
    service = WorkflowExecutionService(db)
    # TODO: Get organization_id and user_id from authentication
    result = service.start_workflow(
        workflow_type="email-campaign",
        request_data=request.dict(),
        organization_id=1,  # Placeholder
        user_id=1  # Placeholder
    )
    
    return WorkflowResponse(**result)


@router.post("/lead-scoring/start", response_model=WorkflowResponse)
def start_lead_scoring_workflow(
    request: LeadScoringStartRequest, 
    db: Session = Depends(get_db)
):
    """Start a lead scoring workflow."""
    service = WorkflowExecutionService(db)
    # TODO: Get organization_id and user_id from authentication
    result = service.start_workflow(
        workflow_type="lead-scoring",
        request_data=request.dict(),
        organization_id=request.organization_id,
        user_id=1  # Placeholder
    )
    
    return WorkflowResponse(**result)


# Legacy Google Maps endpoints for backward compatibility
@router.get("/google-maps/status/{execution_id}", response_model=WorkflowResponse)
def get_google_maps_status(execution_id: str, db: Session = Depends(get_db)):
    """Get the status of a Google Maps workflow execution."""
    return get_execution_status(execution_id, db)


@router.post("/google-maps/leads/{lead_id}/convert", response_model=WorkflowResponse)
def convert_google_maps_lead(lead_id: int, db: Session = Depends(get_db)):
    """Convert a Google Maps lead to a CRM lead."""
    # TODO: Implement lead conversion logic
    return WorkflowResponse(
        success=True,
        message="Lead converted successfully",
        data={"lead_id": lead_id + 1000}  # Simulate new CRM lead ID
    )