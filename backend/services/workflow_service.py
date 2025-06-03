"""
Workflow Service - High-level business logic for workflow operations.
Provides lead automation, scheduling, and business process management.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Workflow, WorkflowExecution, Lead, LeadStatus, User, Organization
from .n8n_service import N8nService

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    High-level workflow service for business process automation.
    """
    
    def __init__(self, db: Session):
        """Initialize the workflow service."""
        self.db = db
        self.n8n_service = N8nService(db)
    
    async def close(self):
        """Clean up resources."""
        await self.n8n_service.close()
    
    async def process_lead_status_change(
        self, 
        lead_id: int, 
        old_status: LeadStatus, 
        new_status: LeadStatus
    ) -> List[WorkflowExecution]:
        """
        Process workflows that should trigger on lead status changes.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Find workflows that trigger on status changes
            triggered_workflows = self.db.query(Workflow).filter(
                and_(
                    Workflow.organization_id == lead.organization_id,
                    Workflow.is_active == True,
                    Workflow.trigger_type == "lead_status_change"
                )
            ).all()
            
            executions = []
            
            for workflow in triggered_workflows:
                should_trigger = self._should_trigger_for_status_change(
                    workflow, old_status, new_status
                )
                
                if should_trigger:
                    execution_data = {
                        "trigger": {
                            "type": "lead_status_change",
                            "old_status": old_status.value,
                            "new_status": new_status.value,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                    
                    execution = await self.n8n_service.execute_workflow_for_lead(
                        workflow_id=workflow.id,
                        lead_id=lead_id,
                        execution_data=execution_data
                    )
                    executions.append(execution)
                    
                    logger.info(f"Triggered workflow {workflow.id} for lead {lead_id} status change: {old_status.value} -> {new_status.value}")
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to process lead status change for lead {lead_id}: {e}")
            raise
    
    async def schedule_follow_up_workflows(
        self, 
        lead_id: int, 
        delay_days: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Schedule follow-up workflows for a lead.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Find follow-up workflows
            follow_up_workflows = self.db.query(Workflow).filter(
                and_(
                    Workflow.organization_id == lead.organization_id,
                    Workflow.is_active == True,
                    Workflow.category == "follow_up"
                )
            ).all()
            
            scheduled_workflows = []
            
            for workflow in follow_up_workflows:
                # Calculate schedule time
                schedule_time = datetime.utcnow() + timedelta(days=delay_days)
                
                # Create scheduled workflow entry (you might want to create a scheduled_workflows table)
                scheduled_entry = {
                    "workflow_id": workflow.id,
                    "lead_id": lead_id,
                    "scheduled_for": schedule_time.isoformat(),
                    "trigger_type": "scheduled_follow_up",
                    "status": "scheduled",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                scheduled_workflows.append(scheduled_entry)
                logger.info(f"Scheduled follow-up workflow {workflow.id} for lead {lead_id} at {schedule_time}")
            
            return scheduled_workflows
            
        except Exception as e:
            logger.error(f"Failed to schedule follow-up workflows for lead {lead_id}: {e}")
            raise
    
    async def execute_lead_nurturing_sequence(
        self, 
        lead_id: int, 
        sequence_type: str = "new_lead"
    ) -> Dict[str, Any]:
        """
        Execute a lead nurturing sequence for a new or existing lead.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Find nurturing workflows based on lead characteristics
            nurturing_workflows = self._find_appropriate_nurturing_workflows(lead, sequence_type)
            
            execution_results = []
            
            for workflow, delay_hours in nurturing_workflows:
                if delay_hours == 0:
                    # Execute immediately
                    execution = await self.n8n_service.execute_workflow_for_lead(
                        workflow_id=workflow.id,
                        lead_id=lead_id,
                        execution_data={
                            "nurturing_sequence": sequence_type,
                            "lead_score": lead.score,
                            "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold"
                        }
                    )
                    execution_results.append({
                        "workflow_id": workflow.id,
                        "execution_id": execution.execution_id,
                        "scheduled": False,
                        "delay_hours": 0
                    })
                else:
                    # Schedule for later (implement scheduling logic)
                    execution_results.append({
                        "workflow_id": workflow.id,
                        "execution_id": None,
                        "scheduled": True,
                        "delay_hours": delay_hours,
                        "scheduled_for": (datetime.utcnow() + timedelta(hours=delay_hours)).isoformat()
                    })
            
            return {
                "lead_id": lead_id,
                "sequence_type": sequence_type,
                "executions": execution_results,
                "total_workflows": len(execution_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to execute nurturing sequence for lead {lead_id}: {e}")
            raise
    
    async def get_workflow_performance_metrics(
        self, 
        organization_id: int, 
        workflow_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance metrics for workflows.
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Base query for executions
            query = self.db.query(WorkflowExecution).join(Workflow).filter(
                and_(
                    Workflow.organization_id == organization_id,
                    WorkflowExecution.started_at >= start_date
                )
            )
            
            if workflow_id:
                query = query.filter(Workflow.id == workflow_id)
            
            executions = query.all()
            
            # Calculate metrics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.status == "success"])
            failed_executions = len([e for e in executions if e.status == "error"])
            running_executions = len([e for e in executions if e.status == "running"])
            
            # Calculate average execution time for completed executions
            completed_executions = [e for e in executions if e.finished_at is not None]
            avg_execution_time = None
            if completed_executions:
                total_time = sum([
                    (e.finished_at - e.started_at).total_seconds() 
                    for e in completed_executions
                ])
                avg_execution_time = total_time / len(completed_executions)
            
            # Group by workflow
            workflow_metrics = {}
            for execution in executions:
                workflow = execution.workflow_id
                if workflow not in workflow_metrics:
                    workflow_metrics[workflow] = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "running": 0
                    }
                
                workflow_metrics[workflow]["total"] += 1
                if execution.status == "success":
                    workflow_metrics[workflow]["successful"] += 1
                elif execution.status == "error":
                    workflow_metrics[workflow]["failed"] += 1
                elif execution.status == "running":
                    workflow_metrics[workflow]["running"] += 1
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "days": days_back
                },
                "overall_metrics": {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "running_executions": running_executions,
                    "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                    "average_execution_time_seconds": avg_execution_time
                },
                "workflow_metrics": workflow_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow performance metrics: {e}")
            raise
    
    async def auto_assign_workflows_to_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        """
        Automatically assign appropriate workflows to a lead based on their characteristics.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            assigned_workflows = []
            
            # Get all active workflows for the organization
            workflows = self.db.query(Workflow).filter(
                and_(
                    Workflow.organization_id == lead.organization_id,
                    Workflow.is_active == True
                )
            ).all()
            
            for workflow in workflows:
                should_assign = self._should_assign_workflow_to_lead(workflow, lead)
                if should_assign:
                    assignment = {
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "category": workflow.category,
                        "trigger_type": workflow.trigger_type,
                        "reason": self._get_assignment_reason(workflow, lead)
                    }
                    assigned_workflows.append(assignment)
            
            return assigned_workflows
            
        except Exception as e:
            logger.error(f"Failed to auto-assign workflows to lead {lead_id}: {e}")
            raise
    
    async def validate_and_sync_all_workflows(self, organization_id: int) -> Dict[str, Any]:
        """
        Validate and sync all workflows for an organization.
        """
        try:
            # Get all workflows
            workflows = self.db.query(Workflow).filter(
                Workflow.organization_id == organization_id
            ).all()
            
            validation_results = []
            sync_needed = []
            
            for workflow in workflows:
                validation = await self.n8n_service.validate_workflow_configuration(workflow.id)
                validation_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    **validation
                })
                
                if validation.get("sync_status") == "out_of_sync":
                    sync_needed.append(workflow.id)
            
            # Perform sync from n8n
            sync_result = await self.n8n_service.sync_workflows_from_n8n(organization_id)
            
            return {
                "validation_results": validation_results,
                "sync_needed": sync_needed,
                "sync_result": sync_result,
                "total_workflows": len(workflows)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate and sync workflows for organization {organization_id}: {e}")
            raise
    
    def _should_trigger_for_status_change(
        self, 
        workflow: Workflow, 
        old_status: LeadStatus, 
        new_status: LeadStatus
    ) -> bool:
        """Check if workflow should trigger for this status change."""
        trigger_conditions = workflow.trigger_conditions or {}
        
        # Check if workflow triggers on any status change
        if not trigger_conditions:
            return True
        
        # Check specific status conditions
        target_statuses = trigger_conditions.get("status", [])
        if isinstance(target_statuses, str):
            target_statuses = [target_statuses]
        
        return new_status.value in target_statuses if target_statuses else True
    
    def _find_appropriate_nurturing_workflows(
        self, 
        lead: Lead, 
        sequence_type: str
    ) -> List[tuple]:
        """Find appropriate nurturing workflows for a lead with scheduling."""
        workflows = self.db.query(Workflow).filter(
            and_(
                Workflow.organization_id == lead.organization_id,
                Workflow.is_active == True,
                Workflow.category == "lead_nurturing"
            )
        ).all()
        
        # Basic nurturing sequence with delays
        workflow_schedule = []
        for workflow in workflows:
            # Simple logic - could be enhanced with more sophisticated scheduling
            if sequence_type == "new_lead":
                if "welcome" in workflow.name.lower():
                    workflow_schedule.append((workflow, 0))  # Immediate
                elif "follow_up" in workflow.name.lower():
                    workflow_schedule.append((workflow, 72))  # 3 days later
                elif "nurture" in workflow.name.lower():
                    workflow_schedule.append((workflow, 168))  # 1 week later
        
        return workflow_schedule
    
    def _should_assign_workflow_to_lead(self, workflow: Workflow, lead: Lead) -> bool:
        """Determine if a workflow should be assigned to a lead."""
        # Basic assignment logic - could be enhanced
        if workflow.trigger_type == "manual":
            return False
        
        if workflow.category == "lead_nurturing" and lead.status == LeadStatus.NEW:
            return True
        
        if workflow.category == "follow_up" and lead.status in [LeadStatus.CONTACTED, LeadStatus.QUALIFIED]:
            return True
        
        return False
    
    def _get_assignment_reason(self, workflow: Workflow, lead: Lead) -> str:
        """Get reason for workflow assignment."""
        if workflow.category == "lead_nurturing":
            return f"Lead is new ({lead.status.value}) and qualifies for nurturing"
        
        if workflow.category == "follow_up":
            return f"Lead status ({lead.status.value}) indicates follow-up needed"
        
        return f"Workflow matches lead profile (category: {workflow.category})" 