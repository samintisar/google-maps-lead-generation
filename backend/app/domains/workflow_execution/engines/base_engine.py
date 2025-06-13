"""
Base Workflow Engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
import time
from datetime import datetime

from ..models import WorkflowExecution
from ..schemas import WorkflowExecutionCreate, WorkflowExecutionUpdate


class BaseWorkflowEngine(ABC):
    """Base class for all workflow engines."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def get_workflow_type(self) -> str:
        """Return the workflow type identifier."""
        pass
    
    @abstractmethod
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate the workflow request data."""
        pass
    
    @abstractmethod
    def execute_workflow(self, execution_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow logic."""
        pass
    
    def start_workflow(
        self, 
        request_data: Dict[str, Any], 
        organization_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """Start a workflow execution."""
        try:
            # Validate request
            if not self.validate_request(request_data):
                return {
                    "success": False,
                    "message": "Invalid request data"
                }
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Create execution record
            execution_data = WorkflowExecutionCreate(
                id=execution_id,
                workflow_id=None,  # Use None for dynamic workflows
                organization_id=organization_id,
                user_id=user_id,
                status="running",
                current_step=f"Starting {self.get_workflow_type()} workflow...",
                progress_percentage=0,
                execution_data=request_data
            )
            
            db_execution = WorkflowExecution(**execution_data.dict())
            self.db.add(db_execution)
            self.db.commit()
            
            # Execute workflow directly (no threading for now)
            try:
                self.execute_workflow(execution_id, request_data)
            except Exception as e:
                self.handle_workflow_error(execution_id, e)
            
            return {
                "success": True,
                "message": f"{self.get_workflow_type()} workflow started successfully",
                "data": {
                    "execution_id": execution_id,
                    "workflow_type": self.get_workflow_type()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start workflow: {str(e)}"
            }
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution."""
        execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        return {
            "execution_id": execution.id,
            "workflow_type": self.get_workflow_type(),
            "status": execution.status,
            "current_step": execution.current_step,
            "progress_percentage": execution.progress_percentage,
            "execution_data": execution.execution_data,
            "error_message": execution.error_message,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    def update_execution_status(
        self, 
        execution_id: str, 
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        progress_percentage: Optional[int] = None,
        execution_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        completed: bool = False
    ) -> None:
        """Update workflow execution status."""
        if not self.db:
            # No database session - just print progress for testing
            if current_step:
                print(f"Progress {progress_percentage or 0}%: {current_step}")
            return
            
        execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return
        
        if status:
            execution.status = status
        if current_step:
            execution.current_step = current_step
        if progress_percentage is not None:
            execution.progress_percentage = progress_percentage
        if execution_data:
            # Replace execution_data with new data
                execution.execution_data = execution_data
        if error_message:
            execution.error_message = error_message
        if completed:
            execution.completed_at = datetime.utcnow()
        
        self.db.commit()
    
    def handle_workflow_error(self, execution_id: str, error: Exception) -> None:
        """Handle workflow execution errors."""
        if not self.db:
            print(f"❌ Workflow failed: {str(error)}")
            return
            
        self.update_execution_status(
            execution_id=execution_id,
            status="failed",
            current_step="Workflow failed",
            error_message=str(error),
            completed=True
        )