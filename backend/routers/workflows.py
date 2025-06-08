"""
Workflow management router for n8n integration.
Provides API endpoints for workflow CRUD operations, execution management, and monitoring.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from database import get_db
from models import Workflow, WorkflowExecution, Organization, User, Lead, LeadSource, LeadStatus, LeadTemperature, ActivityLog
from schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowExecutionResponse, APIResponse
from auth import get_current_user
from routers.auth import get_dev_user
from n8n_client import N8nClient, get_n8n_client, LEAD_NURTURING_WORKFLOW_TEMPLATE
from services.n8n_service import N8nService
from services.workflow_service import WorkflowService
from utils.logging_config import get_n8n_logger, check_logging_health, LoggingConfig
from utils.error_handling import get_error_handling_health, error_metrics, error_recovery_manager

logger = get_n8n_logger("workflows_router")
router = APIRouter(prefix="/workflows", tags=["workflows"])

# Background task for syncing workflow executions
async def sync_workflow_execution(execution_id: str, workflow_id: str, lead_id: int, db: Session):
    """Background task to sync n8n execution with database."""
    try:
        async with N8nClient() as n8n_client:
            execution = await n8n_client.get_execution(execution_id)
            if execution:
                # Update or create workflow execution record
                db_execution = db.query(WorkflowExecution).filter(
                    WorkflowExecution.execution_id == execution_id
                ).first()
                
                if not db_execution:
                    db_execution = WorkflowExecution(
                        workflow_id=workflow_id,
                        execution_id=execution_id,
                        lead_id=lead_id,
                        status=execution.status,
                        started_at=execution.start_time,
                        finished_at=execution.end_time,
                        error_message=execution.error,
                        execution_data=execution.data
                    )
                    db.add(db_execution)
                else:
                    db_execution.status = execution.status
                    db_execution.finished_at = execution.end_time
                    db_execution.error_message = execution.error
                    db_execution.execution_data = execution.data
                
                db.commit()
                logger.info(f"Synced execution {execution_id} with database")
    except Exception as e:
        logger.error(f"Failed to sync execution {execution_id}: {e}")

# Workflow CRUD endpoints
@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(
    active_only: Optional[bool] = Query(None, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workflows for the current user's organization."""
    try:
        query = db.query(Workflow).filter(Workflow.organization_id == current_user.organization_id)
        
        if active_only is not None:
            query = query.filter(Workflow.is_active == active_only)
        
        if category:
            query = query.filter(Workflow.category == category)
        
        workflows = query.offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(workflows)} workflows for organization {current_user.organization_id}")
        return workflows
        
    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflows"
        )

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workflow by ID."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        logger.info(f"Retrieved workflow {workflow_id}")
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow"
        )

@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workflow."""
    try:
        # Verify organization access
        if workflow_data.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create workflow for different organization"
            )
        
        # Check if n8n workflow ID already exists
        existing = db.query(Workflow).filter(
            Workflow.n8n_workflow_id == workflow_data.n8n_workflow_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow with this n8n ID already exists"
            )
        
        # Create workflow in database
        db_workflow = Workflow(
            **workflow_data.model_dump(),
            created_by=current_user.id
        )
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        logger.info(f"Created workflow {db_workflow.id}: {db_workflow.name}")
        return db_workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow"
        )

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing workflow."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Update workflow fields
        update_data = workflow_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        
        logger.info(f"Updated workflow {workflow_id}")
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow"
        )

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workflow."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Also try to delete from n8n if possible
        try:
            async with N8nClient() as n8n_client:
                await n8n_client.delete_workflow(workflow.n8n_workflow_id)
        except Exception as e:
            logger.warning(f"Failed to delete workflow from n8n: {e}")
        
        db.delete(workflow)
        db.commit()
        
        logger.info(f"Deleted workflow {workflow_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workflow"
        )

# Workflow execution endpoints
@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    execution_data: Dict[str, Any] = None,
    lead_id: Optional[int] = Query(None, description="Lead ID to associate with execution"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a workflow manually."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Execute workflow via n8n API
        async with N8nClient() as n8n_client:
            execution_result = await n8n_client.execute_workflow(
                workflow.n8n_workflow_id,
                execution_data or {}
            )
        
        # Create execution record in database
        if lead_id:
            db_execution = WorkflowExecution(
                workflow_id=workflow.n8n_workflow_id,
                execution_id=execution_result.execution_id,
                lead_id=lead_id,
                status=execution_result.status,
                started_at=execution_result.start_time,
                finished_at=execution_result.end_time,
                error_message=execution_result.error,
                execution_data=execution_result.data
            )
            db.add(db_execution)
            db.commit()
            
            # Schedule background sync
            background_tasks.add_task(
                sync_workflow_execution,
                execution_result.execution_id,
                workflow.n8n_workflow_id,
                lead_id,
                db
            )
        
        logger.info(f"Executed workflow {workflow_id}, execution ID: {execution_result.execution_id}")
        return {
            "execution_id": execution_result.execution_id,
            "status": execution_result.status,
            "message": "Workflow execution started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def get_workflow_executions(
    workflow_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get executions for a specific workflow."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        query = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow.n8n_workflow_id
        )
        
        if status_filter:
            query = query.filter(WorkflowExecution.status == status_filter)
        
        executions = query.order_by(WorkflowExecution.started_at.desc()).offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(executions)} executions for workflow {workflow_id}")
        return executions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get executions for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve executions"
        )

@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a workflow in both database and n8n."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Activate in n8n
        async with N8nClient() as n8n_client:
            await n8n_client.activate_workflow(workflow.n8n_workflow_id)
        
        # Update database
        workflow.is_active = True
        workflow.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Activated workflow {workflow_id}")
        return {"message": "Workflow activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate workflow {workflow_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate workflow"
        )

@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a workflow in both database and n8n."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == current_user.organization_id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Deactivate in n8n
        async with N8nClient() as n8n_client:
            await n8n_client.deactivate_workflow(workflow.n8n_workflow_id)
        
        # Update database
        workflow.is_active = False
        workflow.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Deactivated workflow {workflow_id}")
        return {"message": "Workflow deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate workflow"
        )

# n8n integration endpoints
@router.get("/n8n/sync")
async def sync_n8n_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync workflows from n8n to database."""
    try:
        async with N8nClient() as n8n_client:
            n8n_workflows = await n8n_client.get_workflows()
        
        synced_count = 0
        for n8n_workflow in n8n_workflows:
            # Check if workflow exists in database
            existing = db.query(Workflow).filter(
                Workflow.n8n_workflow_id == n8n_workflow.id
            ).first()
            
            if not existing:
                # Create new workflow record
                new_workflow = Workflow(
                    organization_id=current_user.organization_id,
                    n8n_workflow_id=n8n_workflow.id,
                    name=n8n_workflow.name,
                    description=f"Synced from n8n: {n8n_workflow.name}",
                    category="synced",
                    trigger_type="unknown",
                    is_active=n8n_workflow.active,
                    created_by=current_user.id,
                    configuration={"nodes": n8n_workflow.nodes, "connections": n8n_workflow.connections}
                )
                db.add(new_workflow)
                synced_count += 1
            else:
                # Update existing workflow
                existing.name = n8n_workflow.name
                existing.is_active = n8n_workflow.active
                existing.updated_at = datetime.utcnow()
                existing.configuration = {"nodes": n8n_workflow.nodes, "connections": n8n_workflow.connections}
        
        db.commit()
        
        logger.info(f"Synced {synced_count} workflows from n8n")
        return {
            "message": f"Successfully synced {synced_count} workflows from n8n",
            "total_n8n_workflows": len(n8n_workflows),
            "synced_new": synced_count
        }
        
    except Exception as e:
        logger.error(f"Failed to sync n8n workflows: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync workflows from n8n"
        )

@router.get("/n8n/statistics")
async def get_n8n_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get n8n workflow statistics."""
    try:
        async with N8nClient() as n8n_client:
            stats = await n8n_client.get_workflow_statistics()
        
        logger.info("Retrieved n8n statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get n8n statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve n8n statistics"
        )

@router.post("/n8n/webhook/{webhook_path}")
async def trigger_n8n_webhook(
    webhook_path: str,
    webhook_data: Dict[str, Any],
    method: str = Query("POST", description="HTTP method for webhook"),
    current_user: User = Depends(get_current_user)
):
    """Trigger an n8n webhook."""
    try:
        async with N8nClient() as n8n_client:
            result = await n8n_client.trigger_webhook(webhook_path, webhook_data, method)
        
        logger.info(f"Triggered webhook {webhook_path}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger webhook {webhook_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger webhook"
        )

# Template endpoints
@router.get("/templates/")
async def get_workflow_templates():
    """Get available workflow templates."""
    templates = {
        "lead_nurturing": {
            "name": "Lead Nurturing Email Sequence",
            "description": "Automated email sequence for nurturing new leads",
            "category": "lead_nurturing",
            "template": LEAD_NURTURING_WORKFLOW_TEMPLATE
        }
    }
    
    logger.info("Retrieved workflow templates")
    return templates

@router.post("/templates/{template_name}/create")
async def create_workflow_from_template(
    template_name: str,
    template_config: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a workflow from a template."""
    try:
        if template_name == "lead_nurturing":
            template = LEAD_NURTURING_WORKFLOW_TEMPLATE.copy()
            
            # Apply any configuration overrides
            if "name" in template_config:
                template["name"] = template_config["name"]
            
            # Create workflow in n8n
            async with N8nClient() as n8n_client:
                n8n_workflow = await n8n_client.create_workflow(
                    name=template["name"],
                    nodes=template["nodes"],
                    connections=template["connections"],
                    settings=template["settings"],
                    tags=template["tags"]
                )
            
            # Create workflow record in database
            db_workflow = Workflow(
                organization_id=current_user.organization_id,
                n8n_workflow_id=n8n_workflow.id,
                name=n8n_workflow.name,
                description=f"Created from template: {template_name}",
                category="lead_nurturing",
                trigger_type="webhook",
                trigger_conditions={"template": template_name},
                configuration={"template": template_name, **template_config},
                is_active=False,
                created_by=current_user.id
            )
            db.add(db_workflow)
            db.commit()
            db.refresh(db_workflow)
            
            logger.info(f"Created workflow from template {template_name}: {db_workflow.id}")
            return {
                "workflow_id": db_workflow.id,
                "n8n_workflow_id": n8n_workflow.id,
                "message": f"Workflow created successfully from {template_name} template"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_name} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow from template {template_name}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow from template"
        )

# Service-based endpoints using the new service layer
@router.get("/service/health")
async def check_n8n_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check n8n service health using the service layer."""
    try:
        n8n_service = N8nService(db)
        health_status = await n8n_service.health_check()
        await n8n_service.close()
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "n8n_service": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.post("/service/sync")
async def sync_workflows_with_service(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync workflows using the enhanced service layer."""
    try:
        n8n_service = N8nService(db)
        sync_result = await n8n_service.sync_workflows_from_n8n(current_user.organization_id)
        await n8n_service.close()
        
        return sync_result
        
    except Exception as e:
        logger.error(f"Service-based workflow sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync workflows"
        )

@router.post("/service/templates/{template_name}")
async def create_workflow_from_template_service(
    template_name: str,
    workflow_name: str,
    configuration: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create workflow from template using the service layer."""
    try:
        n8n_service = N8nService(db)
        db_workflow, n8n_workflow = await n8n_service.create_workflow_from_template(
            organization_id=current_user.organization_id,
            template_name=template_name,
            workflow_name=workflow_name,
            configuration=configuration,
            created_by=current_user.id
        )
        await n8n_service.close()
        
        return {
            "workflow_id": db_workflow.id,
            "n8n_workflow_id": n8n_workflow.id,
            "name": workflow_name,
            "template": template_name,
            "message": "Workflow created successfully from template"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create workflow from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow from template"
        )

@router.post("/{workflow_id}/execute-for-lead/{lead_id}")
async def execute_workflow_for_lead(
    workflow_id: int,
    lead_id: int,
    execution_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a workflow for a specific lead using the service layer."""
    try:
        n8n_service = N8nService(db)
        execution = await n8n_service.execute_workflow_for_lead(
            workflow_id=workflow_id,
            lead_id=lead_id,
            execution_data=execution_data
        )
        await n8n_service.close()
        
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "lead_id": execution.lead_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "message": "Workflow execution started successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute workflow for lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )

@router.get("/service/statistics")
async def get_workflow_statistics_service(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive workflow statistics using the service layer."""
    try:
        n8n_service = N8nService(db)
        stats = await n8n_service.get_workflow_statistics(current_user.organization_id)
        await n8n_service.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow statistics"
        )

@router.post("/{workflow_id}/validate")
async def validate_workflow_configuration(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate workflow configuration and connectivity."""
    try:
        n8n_service = N8nService(db)
        validation_result = await n8n_service.validate_workflow_configuration(workflow_id)
        await n8n_service.close()
        
        return validation_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to validate workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate workflow"
        )

# Workflow service endpoints for business logic
@router.post("/lead/{lead_id}/auto-assign")
async def auto_assign_workflows_to_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Automatically assign appropriate workflows to a lead."""
    try:
        workflow_service = WorkflowService(db)
        assignments = await workflow_service.auto_assign_workflows_to_lead(lead_id)
        await workflow_service.close()
        
        return {
            "lead_id": lead_id,
            "assigned_workflows": assignments,
            "total_assigned": len(assignments)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to auto-assign workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to auto-assign workflows"
        )

@router.post("/lead/{lead_id}/nurturing-sequence")
async def execute_lead_nurturing_sequence(
    lead_id: int,
    sequence_type: str = "new_lead",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a lead nurturing sequence."""
    try:
        workflow_service = WorkflowService(db)
        result = await workflow_service.execute_lead_nurturing_sequence(lead_id, sequence_type)
        await workflow_service.close()
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute nurturing sequence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute nurturing sequence"
        )

@router.get("/performance-metrics")
async def get_workflow_performance_metrics(
    workflow_id: Optional[int] = Query(None, description="Specific workflow ID (optional)"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workflow performance metrics."""
    try:
        workflow_service = WorkflowService(db)
        metrics = await workflow_service.get_workflow_performance_metrics(
            organization_id=current_user.organization_id,
            workflow_id=workflow_id,
            days_back=days_back
        )
        await workflow_service.close()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )

@router.post("/validate-and-sync-all")
async def validate_and_sync_all_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate and sync all workflows for the organization."""
    try:
        workflow_service = WorkflowService(db)
        result = await workflow_service.validate_and_sync_all_workflows(current_user.organization_id)
        await workflow_service.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to validate and sync all workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate and sync workflows"
        )

# Enhanced error handling and logging endpoints
@router.get("/monitoring/health")
async def get_monitoring_health(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive health status of error handling and logging systems."""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {
                "logging_system": check_logging_health(),
                "error_handling": get_error_handling_health(),
                "n8n_service": None
            }
        }
        
        # Test n8n service health
        try:
            n8n_service = N8nService(db=None)  # Temporary service for health check
            n8n_healthy = await n8n_service.health_check()
            health_status["components"]["n8n_service"] = {
                "status": "healthy" if n8n_healthy else "unhealthy",
                "n8n_reachable": n8n_healthy
            }
            await n8n_service.close()
        except Exception as e:
            health_status["components"]["n8n_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall status
        unhealthy_components = [
            name for name, component in health_status["components"].items()
            if component and component.get("status") == "unhealthy"
        ]
        
        if unhealthy_components:
            health_status["overall_status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_components
        
        logger.info(
            "Monitoring health check completed",
            extra_fields={
                "overall_status": health_status["overall_status"],
                "unhealthy_components": unhealthy_components
            }
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Failed to get monitoring health status",
            error_category=ErrorCategory.SYSTEM_ERROR,
            extra_fields={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitoring health status"
        )

@router.get("/monitoring/error-metrics")
async def get_error_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get error metrics and statistics."""
    try:
        metrics = error_metrics.get_error_summary()
        
        logger.info(
            "Error metrics retrieved",
            extra_fields={
                "total_errors": metrics.get("total_errors", 0),
                "categories_count": len(metrics.get("error_categories", {}))
            }
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(
            "Failed to retrieve error metrics",
            error_category=ErrorCategory.SYSTEM_ERROR,
            extra_fields={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error metrics"
        )

@router.post("/monitoring/test-error-handling")
async def test_error_handling(
    error_type: str = Query(..., description="Type of error to simulate: connection, authentication, timeout, validation"),
    current_user: User = Depends(get_current_user)
):
    """Test error handling mechanisms by simulating different error types."""
    try:
        logger.info(
            f"Testing error handling for type: {error_type}",
            extra_fields={"error_type": error_type, "user_id": current_user.id}
        )
        
        # Simulate different error types for testing
        test_context = WorkflowLogContext(
            workflow_id="test_workflow",
            execution_id="test_execution",
            organization_id=current_user.organization_id
        )
        
        if error_type == "connection":
            test_error = N8nConnectionError(
                "Simulated connection error for testing",
                context=test_context
            )
        elif error_type == "authentication":
            test_error = N8nAuthenticationError(
                "Simulated authentication error for testing",
                context=test_context
            )
        elif error_type == "timeout":
            test_error = N8nTimeoutError(
                "Simulated timeout error for testing",
                timeout_duration=30.0,
                context=test_context
            )
        elif error_type == "validation":
            test_error = N8nValidationError(
                "Simulated validation error for testing",
                context=test_context
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported error type: {error_type}"
            )
        
        # Test error recovery
        recovery_result = await error_recovery_manager.handle_error(test_error)
        
        logger.info(
            "Error handling test completed",
            extra_fields={
                "error_type": error_type,
                "recovery_successful": recovery_result["recovery_successful"]
            }
        )
        
        return {
            "test_type": error_type,
            "error_details": test_error.to_dict(),
            "recovery_result": recovery_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error handling test failed for type {error_type}",
            error_category=ErrorCategory.SYSTEM_ERROR,
            extra_fields={"error_type": error_type, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error handling test failed"
        )

@router.post("/monitoring/setup-logging")
async def setup_logging_configuration(
    log_level: str = Query("INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    enable_structured: bool = Query(True, description="Enable structured JSON logging"),
    current_user: User = Depends(get_current_user)
):
    """Configure logging system settings."""
    try:
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log level. Must be one of: {valid_levels}"
            )
        
        # Setup logging with new configuration
        LoggingConfig.setup_logging(
            log_level=log_level.upper(),
            enable_structured=enable_structured
        )
        
        logger.info(
            "Logging configuration updated",
            extra_fields={
                "log_level": log_level.upper(),
                "structured_logging": enable_structured,
                "updated_by": current_user.id
            }
        )
        
        return {
            "message": "Logging configuration updated successfully",
            "configuration": {
                "log_level": log_level.upper(),
                "structured_logging": enable_structured
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update logging configuration",
            error_category=ErrorCategory.CONFIGURATION_ERROR,
            extra_fields={"log_level": log_level, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update logging configuration"
        )

# === ADDITIONAL N8N WORKFLOW ENDPOINTS ===

@router.post("/leads/create", response_model=APIResponse)
async def create_lead_workflow(
    lead_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Create a new lead from n8n workflow."""
    try:
        # Extract lead data
        email = lead_data.get("email")
        first_name = lead_data.get("firstName") or lead_data.get("first_name")
        last_name = lead_data.get("lastName") or lead_data.get("last_name")
        company = lead_data.get("company")
        source = lead_data.get("source", "website")
        
        if not email or not first_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and first name are required"
            )
        
        # Check if lead already exists
        existing_lead = db.query(Lead).filter(
            Lead.email == email,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if existing_lead:
            return APIResponse(
                success=True,
                data={
                    "lead_id": existing_lead.id,
                    "email": existing_lead.email,
                    "first_name": existing_lead.first_name,
                    "last_name": existing_lead.last_name,
                    "company": existing_lead.company,
                    "existing": True
                },
                message="Lead already exists"
            )
        
        # Create new lead
        new_lead = Lead(
            organization_id=current_user.organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            source=LeadSource(source) if source else LeadSource.WEBSITE,
            status=LeadStatus.NEW,
            score=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        
        return APIResponse(
            success=True,
            data={
                "lead_id": new_lead.id,
                "email": new_lead.email,
                "first_name": new_lead.first_name,
                "last_name": new_lead.last_name,
                "company": new_lead.company,
                "created_at": new_lead.created_at.isoformat(),
                "existing": False
            },
            message="Lead created successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


@router.post("/leads/{lead_id}/update-status", response_model=APIResponse)
async def update_lead_status_workflow(
    lead_id: int,
    status_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Update lead status from n8n workflow."""
    try:
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Update fields if provided
        if "status" in status_data:
            lead.status = LeadStatus(status_data["status"])
        
        if "last_contacted_at" in status_data:
            lead.last_engagement_date = datetime.fromisoformat(status_data["last_contacted_at"].replace('Z', '+00:00'))
        
        if "notes" in status_data:
            existing_notes = lead.notes or ""
            new_notes = status_data["notes"]
            lead.notes = f"{existing_notes}\n{new_notes}" if existing_notes else new_notes
        
        lead.updated_at = datetime.utcnow()
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "status": lead.status.value if lead.status else None,
                "updated_at": lead.updated_at.isoformat()
            },
            message="Lead status updated successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update lead status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead status: {str(e)}"
        )


@router.get("/leads/social-outreach", response_model=APIResponse)
async def get_leads_for_social_outreach(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of leads to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Get leads for social media outreach."""
    try:
        # Query leads with high scores that haven't been contacted recently
        leads = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id,
            Lead.linkedin_url.isnot(None),
            Lead.lead_temperature.in_([LeadTemperature.HOT, LeadTemperature.WARM]),
            or_(
                Lead.last_engagement_date.is_(None),
                Lead.last_engagement_date < datetime.utcnow() - timedelta(days=7)
            )
        ).order_by(Lead.score.desc()).limit(limit).all()
        
        # Format for n8n workflow
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "linkedin_url": lead.linkedin_url,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "score": lead.score or 0,
                "industry": "technology",  # Default - would come from enrichment
                "linkedin_connection_status": "pending",
                "linkedin_messages_sent": 0,
                "last_linkedin_outreach": lead.last_engagement_date.isoformat() if lead.last_engagement_date else None
            })
        
        return APIResponse(
            success=True,
            data=formatted_leads,
            message=f"Retrieved {len(formatted_leads)} leads for social outreach"
        )
        
    except Exception as e:
        logger.error(f"Failed to get leads for social outreach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leads for social outreach: {str(e)}"
        )


@router.post("/leads/{lead_id}/social-outreach", response_model=APIResponse)
async def log_social_outreach(
    lead_id: int,
    outreach_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Log social media outreach activity."""
    try:
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Update lead engagement
        lead.last_engagement_date = datetime.utcnow()
        lead.updated_at = datetime.utcnow()
        
        # Log activity
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type="social_outreach",
            description=f"LinkedIn {outreach_data.get('outreach_type', 'outreach')} sent",
            activity_metadata={
                "platform": "linkedin",
                "outreach_type": outreach_data.get("outreach_type"),
                "message_sent": outreach_data.get("message_sent"),
                "status": outreach_data.get("status", "sent"),
                "linkedin_connection_status": outreach_data.get("linkedin_connection_status"),
                "linkedin_connection_message": outreach_data.get("linkedin_connection_message"),
                "linkedin_follow_up_message": outreach_data.get("linkedin_follow_up_message")
            },
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "outreach_logged": True,
                "activity_log_id": activity_log.id,
                "last_linkedin_outreach": datetime.utcnow().isoformat(),
                "linkedin_messages_sent": 1
            },
            message="Social outreach activity logged successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log social outreach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log social outreach: {str(e)}"
        )


@router.get("/leads/crm-sync", response_model=APIResponse)
async def get_leads_for_crm_sync(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of leads to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Get leads that need CRM synchronization."""
    try:
        # Query leads updated in last hour or never synced
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        leads = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id,
            or_(
                Lead.updated_at >= cutoff_time,
                and_(
                    Lead.notes.is_(None),
                    Lead.created_at >= cutoff_time
                )
            )
        ).order_by(Lead.updated_at.desc()).limit(limit).all()
        
        # Format for CRM sync
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "company": lead.company,
                "phone": lead.phone,
                "source": lead.source.value if lead.source else None,
                "status": lead.status.value if lead.status else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "tags": lead.tags or [],
                "synced_to_crm": "crm_sync" in (lead.notes or ""),
                "last_crm_sync": lead.updated_at.isoformat() if lead.updated_at else None
            })
        
        return APIResponse(
            success=True,
            data=formatted_leads,
            message=f"Retrieved {len(formatted_leads)} leads for CRM sync"
        )
        
    except Exception as e:
        logger.error(f"Failed to get leads for CRM sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leads for CRM sync: {str(e)}"
        )


@router.post("/leads/crm-sync", response_model=APIResponse)
async def update_crm_sync_status(
    sync_updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Update CRM sync status for multiple leads."""
    try:
        updated_leads = []
        failed_updates = []
        
        for sync_data in sync_updates:
            try:
                lead_id = sync_data.get("id")
                crm_id = sync_data.get("crm_id")
                
                lead = db.query(Lead).filter(
                    Lead.id == lead_id,
                    Lead.organization_id == current_user.organization_id
                ).first()
                
                if not lead:
                    failed_updates.append({
                        "lead_id": lead_id,
                        "error": "Lead not found"
                    })
                    continue
                
                # Update sync status in notes
                sync_note = f"CRM Sync: synced to {sync_data.get('crm_type', 'CRM')} (ID: {crm_id})"
                existing_notes = lead.notes or ""
                lead.notes = f"{existing_notes}\ncrm_sync: {sync_note}" if existing_notes else f"crm_sync: {sync_note}"
                
                lead.updated_at = datetime.utcnow()
                
                # Log activity
                activity_log = ActivityLog(
                    lead_id=lead_id,
                    activity_type="crm_sync",
                    description=f"Lead synced to {sync_data.get('crm_type', 'CRM')}",
                    activity_metadata={
                        "crm_type": sync_data.get("crm_type"),
                        "crm_id": crm_id,
                        "synced_to_crm": True,
                        "last_crm_sync": datetime.utcnow().isoformat()
                    },
                    created_at=datetime.utcnow()
                )
                
                db.add(activity_log)
                
                updated_leads.append({
                    "lead_id": lead_id,
                    "crm_id": crm_id,
                    "synced_to_crm": True,
                    "last_crm_sync": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                failed_updates.append({
                    "lead_id": sync_data.get("id", "unknown"),
                    "error": str(e)
                })
        
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "updated_leads": updated_leads,
                "failed_updates": failed_updates,
                "summary": {
                    "successful_updates": len(updated_leads),
                    "failed_updates": len(failed_updates),
                    "total_processed": len(sync_updates)
                }
            },
            message=f"CRM sync completed: {len(updated_leads)} successful, {len(failed_updates)} failed"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update CRM sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update CRM sync status: {str(e)}"
        )


@router.post("/webhook/crm-update", response_model=APIResponse)
async def handle_crm_webhook(
    webhook_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Handle incoming CRM webhook updates."""
    try:
        # Extract data based on CRM type
        email = webhook_data.get("email")
        crm_id = webhook_data.get("leadId") or webhook_data.get("objectId")
        
        if not email and not crm_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or CRM ID required"
            )
        
        # Find lead by email
        lead = None
        if email:
            lead = db.query(Lead).filter(
                Lead.email == email,
                Lead.organization_id == current_user.organization_id
            ).first()
        
        if not lead:
            return APIResponse(
                success=False,
                data={"reason": "Lead not found"},
                message="Lead not found for CRM update"
            )
        
        # Update lead with CRM data
        updated_fields = []
        if webhook_data.get("firstName") and webhook_data["firstName"] != lead.first_name:
            lead.first_name = webhook_data["firstName"]
            updated_fields.append("first_name")
        
        if webhook_data.get("lastName") and webhook_data["lastName"] != lead.last_name:
            lead.last_name = webhook_data["lastName"]
            updated_fields.append("last_name")
        
        if webhook_data.get("company") and webhook_data["company"] != lead.company:
            lead.company = webhook_data["company"]
            updated_fields.append("company")
        
        if webhook_data.get("status"):
            try:
                new_status = LeadStatus(webhook_data["status"].lower())
                if new_status != lead.status:
                    lead.status = new_status
                    updated_fields.append("status")
            except ValueError:
                pass  # Invalid status
        
        lead.updated_at = datetime.utcnow()
        
        # Log the CRM update
        activity_log = ActivityLog(
            lead_id=lead.id,
            activity_type="crm_webhook",
            description=f"Lead updated from {webhook_data.get('crmType', 'CRM')} webhook",
            activity_metadata={
                "crm_type": webhook_data.get("crmType"),
                "crm_id": crm_id,
                "updated_fields": updated_fields
            },
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead.id,
                "updated_fields": updated_fields,
                "processed_at": datetime.utcnow().isoformat()
            },
            message="Lead updated from CRM webhook"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process CRM webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CRM webhook: {str(e)}"
        ) 