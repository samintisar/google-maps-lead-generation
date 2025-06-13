"""
Workflow Execution Domain Services.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from .models import Workflow, WorkflowExecution
from .schemas import WorkflowCreate, WorkflowUpdate, WorkflowExecutionCreate, WorkflowExecutionUpdate
from .engines import GoogleMapsWorkflowEngine, EmailCampaignWorkflowEngine, LeadScoringWorkflowEngine


class WorkflowService:
    """Service for workflow management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[Workflow]:
        """Get workflows with optional filtering."""
        query = self.db.query(Workflow)
        
        if organization_id:
            query = query.filter(Workflow.organization_id == organization_id)
        
        if user_id:
            query = query.filter(Workflow.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Workflow.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get a specific workflow by ID."""
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    def create_workflow(self, workflow_data: WorkflowCreate) -> Workflow:
        """Create a new workflow."""
        db_workflow = Workflow(**workflow_data.dict())
        self.db.add(db_workflow)
        self.db.commit()
        self.db.refresh(db_workflow)
        return db_workflow
    
    def update_workflow(self, workflow_id: int, workflow_data: WorkflowUpdate) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        update_data = workflow_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)
        
        self.db.commit()
        self.db.refresh(workflow)
        return workflow
    
    def delete_workflow(self, workflow_id: int) -> bool:
        """Delete a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        self.db.delete(workflow)
        self.db.commit()
        return True
    
    def activate_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Activate a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        workflow.is_active = True
        self.db.commit()
        self.db.refresh(workflow)
        return workflow
    
    def deactivate_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Deactivate a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        workflow.is_active = False
        self.db.commit()
        self.db.refresh(workflow)
        return workflow


class WorkflowExecutionService:
    """Service for workflow execution operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.engines = {
            "google-maps": GoogleMapsWorkflowEngine(db),
            "email-campaign": EmailCampaignWorkflowEngine(db),
            "lead-scoring": LeadScoringWorkflowEngine(db)
        }
    
    def start_workflow(
        self, 
        workflow_type: str, 
        request_data: Dict[str, Any], 
        organization_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """Start a workflow execution."""
        if workflow_type not in self.engines:
            return {
                "success": False,
                "message": f"Unknown workflow type: {workflow_type}"
            }
        
        engine = self.engines[workflow_type]
        return engine.start_workflow(request_data, organization_id, user_id)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "current_step": execution.current_step,
            "progress_percentage": execution.progress_percentage,
            "execution_data": execution.execution_data,
            "error_message": execution.error_message,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    def get_executions(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[WorkflowExecution]:
        """Get workflow executions with optional filtering."""
        query = self.db.query(WorkflowExecution)
        
        if organization_id:
            query = query.filter(WorkflowExecution.organization_id == organization_id)
        
        if user_id:
            query = query.filter(WorkflowExecution.user_id == user_id)
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution."""
        execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution or execution.status in ["completed", "failed", "cancelled"]:
            return False
        
        execution.status = "cancelled"
        execution.current_step = "Workflow cancelled"
        self.db.commit()
        return True