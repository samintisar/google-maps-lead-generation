"""
Workflow management router for n8n integration.
Provides API endpoints for workflow CRUD operations, execution management, and monitoring.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from database import get_db
from models import Workflow, WorkflowExecution, Organization, User, Lead
from schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowExecutionResponse
from auth import get_current_user
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