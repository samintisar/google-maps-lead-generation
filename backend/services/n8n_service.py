"""
N8n Service Layer - Provides high-level workflow operations and business logic.
Abstracts the n8n client and provides organization-specific workflow management.
Enhanced with comprehensive error handling and structured logging.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from n8n_client import N8nClient, N8nWorkflow, WorkflowExecutionResult
from models import Workflow, WorkflowExecution, Organization, User, Lead
from config import Settings

# Import enhanced error handling and logging
from utils.logging_config import get_n8n_logger, LoggingConfig, WorkflowLogContext, ErrorCategory
from utils.error_handling import (
    N8nConnectionError, N8nAuthenticationError, N8nApiError, N8nTimeoutError, 
    N8nValidationError, N8nWorkflowExecutionError, N8nConfigurationError,
    handle_n8n_exception, with_retry, RetryConfig, ErrorSeverity,
    error_recovery_manager
)

# Initialize enhanced logging
logger = get_n8n_logger("service")
settings = Settings()

class N8nService:
    """
    Enhanced service layer for n8n workflow operations.
    Provides business logic and abstracts the n8n client with comprehensive error handling.
    """
    
    def __init__(self, db: Session):
        """Initialize the n8n service with database session and enhanced logging."""
        self.db = db
        self._n8n_client = None
        
        logger.info(
            "Initialized N8nService",
            extra_fields={"database_connected": bool(db)}
        )
    
    async def get_n8n_client(self) -> N8nClient:
        """Get or create n8n client instance with error handling."""
        if self._n8n_client is None:
            try:
                self._n8n_client = N8nClient()
                logger.info("Created new n8n client instance")
            except Exception as e:
                logger.error(
                    "Failed to create n8n client",
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    extra_fields={"error": str(e)}
                )
                raise N8nConfigurationError(
                    f"Failed to initialize n8n client: {e}",
                    original_exception=e
                )
        return self._n8n_client
    
    async def close(self):
        """Clean up resources with logging."""
        if self._n8n_client:
            try:
                await self._n8n_client.__aexit__(None, None, None)
                logger.info("Closed n8n client connection")
            except Exception as e:
                logger.warning(
                    "Error closing n8n client",
                    error_category=ErrorCategory.CONNECTION_ERROR,
                    extra_fields={"error": str(e)}
                )
    
    @handle_n8n_exception
    @with_retry(
        config=RetryConfig(max_attempts=2, base_delay=1.0),
        circuit_breaker_key="api_calls"
    )
    async def health_check(self) -> bool:
        """Check if n8n service is healthy with enhanced error handling."""
        try:
            client = await self.get_n8n_client()
            is_healthy = await client.health_check()
            
            logger.info(
                "n8n health check completed",
                extra_fields={"healthy": is_healthy}
            )
            return is_healthy
            
        except Exception as e:
            logger.error(
                "n8n health check failed",
                error_category=ErrorCategory.CONNECTION_ERROR,
                extra_fields={"error": str(e)}
            )
            return False
    
    @handle_n8n_exception
    @with_retry(
        config=RetryConfig(max_attempts=3, base_delay=2.0),
        circuit_breaker_key="api_calls"
    )
    async def sync_workflows_from_n8n(self, organization_id: int) -> Dict[str, Any]:
        """
        Sync workflows from n8n to database with enhanced error handling and logging.
        """
        context = WorkflowLogContext(organization_id=organization_id)
        
        try:
            logger.info(
                f"Starting workflow sync for organization {organization_id}",
                extra_fields={"organization_id": organization_id}
            )
            
            # Initialize sync summary
            sync_summary = {
                "organization_id": organization_id,
                "total_n8n_workflows": 0,
                "synced_workflows": 0,
                "updated_workflows": 0,
                "errors": [],
                "start_time": datetime.utcnow().isoformat()
            }
            
            # Get workflows from n8n
            client = await self.get_n8n_client()
            n8n_workflows = await client.get_workflows()
            sync_summary["total_n8n_workflows"] = len(n8n_workflows)
            
            logger.info(
                f"Retrieved {len(n8n_workflows)} workflows from n8n",
                extra_fields={"workflow_count": len(n8n_workflows)}
            )
            
            # Sync each workflow
            for n8n_workflow in n8n_workflows:
                workflow_context = WorkflowLogContext(
                    workflow_id=n8n_workflow.id,
                    organization_id=organization_id
                )
                
                try:
                    # Check if workflow exists in database
                    existing_workflow = self.db.query(Workflow).filter(
                        Workflow.n8n_workflow_id == n8n_workflow.id,
                        Workflow.organization_id == organization_id
                    ).first()
                    
                    if existing_workflow:
                        # Update existing workflow
                        existing_workflow.name = n8n_workflow.name
                        existing_workflow.is_active = n8n_workflow.active
                        existing_workflow.updated_at = datetime.utcnow()
                        existing_workflow.configuration = {
                            "nodes": n8n_workflow.nodes,
                            "connections": n8n_workflow.connections,
                            "settings": n8n_workflow.settings
                        }
                        sync_summary["updated_workflows"] += 1
                        
                        logger.debug(
                            f"Updated existing workflow {n8n_workflow.id}",
                            extra_fields={
                                "workflow_id": n8n_workflow.id,
                                "workflow_name": n8n_workflow.name,
                                "active": n8n_workflow.active
                            }
                        )
                    else:
                        # Create new workflow
                        new_workflow = Workflow(
                            organization_id=organization_id,
                            n8n_workflow_id=n8n_workflow.id,
                            name=n8n_workflow.name,
                            description=f"Synced from n8n: {n8n_workflow.name}",
                            category="synced",
                            trigger_type="manual",  # Default, can be updated later
                            is_active=n8n_workflow.active,
                            configuration={
                                "nodes": n8n_workflow.nodes,
                                "connections": n8n_workflow.connections,
                                "settings": n8n_workflow.settings
                            }
                        )
                        self.db.add(new_workflow)
                        sync_summary["synced_workflows"] += 1
                        
                        logger.debug(
                            f"Created new workflow {n8n_workflow.id}",
                            extra_fields={
                                "workflow_id": n8n_workflow.id,
                                "workflow_name": n8n_workflow.name,
                                "active": n8n_workflow.active
                            }
                        )
                    
                except Exception as e:
                    error_msg = f"Failed to sync workflow {n8n_workflow.id}: {str(e)}"
                    logger.error(
                        error_msg,
                        error_category=ErrorCategory.DATA_ERROR,
                        extra_fields={
                            "workflow_id": n8n_workflow.id,
                            "workflow_name": n8n_workflow.name,
                            "error": str(e)
                        }
                    )
                    sync_summary["errors"].append(error_msg)
            
            # Commit changes
            self.db.commit()
            
            sync_summary["end_time"] = datetime.utcnow().isoformat()
            sync_summary["success"] = len(sync_summary["errors"]) == 0
            
            logger.info(
                f"Workflow sync completed for organization {organization_id}",
                extra_fields=sync_summary
            )
            
            return sync_summary
            
        except Exception as e:
            logger.error(
                f"Failed to sync workflows from n8n for organization {organization_id}",
                error_category=ErrorCategory.SYSTEM_ERROR,
                extra_fields={"organization_id": organization_id, "error": str(e)}
            )
            self.db.rollback()
            raise
    
    @handle_n8n_exception
    async def execute_workflow_for_lead(
        self, 
        workflow_id: int, 
        lead_id: int, 
        execution_data: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow for a specific lead with enhanced error handling and tracking.
        """
        context = WorkflowLogContext(lead_id=lead_id)
        
        try:
            # Get workflow from database
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise N8nValidationError(
                    f"Workflow {workflow_id} not found",
                    context=context
                )
            
            # Get lead from database
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise N8nValidationError(
                    f"Lead {lead_id} not found",
                    context=context
                )
            
            # Update context with workflow information
            context.workflow_id = workflow.n8n_workflow_id
            context.organization_id = workflow.organization_id
            
            logger.info(
                f"Executing workflow {workflow_id} for lead {lead_id}",
                extra_fields={
                    "workflow_id": workflow_id,
                    "workflow_name": workflow.name,
                    "lead_id": lead_id,
                    "lead_email": lead.email,
                    "organization_id": workflow.organization_id
                }
            )
            
            # Prepare execution data with lead information
            lead_data = {
                "lead": {
                    "id": lead.id,
                    "email": lead.email,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "company": lead.company,
                    "status": lead.status.value,
                    "score": lead.score,
                    "custom_fields": lead.custom_fields or {}
                }
            }
            
            if execution_data:
                lead_data.update(execution_data)
            
            # Execute workflow in n8n
            client = await self.get_n8n_client()
            client.set_workflow_context(context)
            
            try:
                execution_result = await client.execute_workflow(
                    workflow_id=workflow.n8n_workflow_id,
                    data=lead_data
                )
                
                # Update context with execution ID
                context.execution_id = execution_result.execution_id
                
                # Create execution record
                workflow_execution = WorkflowExecution(
                    workflow_id=workflow.n8n_workflow_id,
                    execution_id=execution_result.execution_id,
                    lead_id=lead_id,
                    status=execution_result.status,
                    started_at=execution_result.start_time,
                    finished_at=execution_result.end_time,
                    error_message=execution_result.error,
                    execution_data=execution_result.data
                )
                
                self.db.add(workflow_execution)
                self.db.commit()
                self.db.refresh(workflow_execution)
                
                logger.info(
                    f"Successfully executed workflow {workflow_id} for lead {lead_id}",
                    extra_fields={
                        "execution_id": execution_result.execution_id,
                        "status": execution_result.status,
                        "duration": (execution_result.end_time - execution_result.start_time).total_seconds() if execution_result.end_time else None
                    }
                )
                
                return workflow_execution
                
            except N8nWorkflowExecutionError as e:
                # Handle workflow execution errors gracefully
                logger.error(
                    f"Workflow execution failed for workflow {workflow_id} and lead {lead_id}",
                    error_category=ErrorCategory.WORKFLOW_EXECUTION_ERROR,
                    extra_fields={
                        "workflow_id": workflow_id,
                        "lead_id": lead_id,
                        "error": str(e)
                    }
                )
                
                # Still create execution record to track the failure
                workflow_execution = WorkflowExecution(
                    workflow_id=workflow.n8n_workflow_id,
                    execution_id=context.execution_id or f"failed_{datetime.utcnow().timestamp()}",
                    lead_id=lead_id,
                    status="error",
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                    error_message=str(e),
                    execution_data=lead_data
                )
                
                self.db.add(workflow_execution)
                self.db.commit()
                self.db.refresh(workflow_execution)
                
                # Attempt error recovery
                recovery_result = await error_recovery_manager.handle_error(e)
                logger.info(
                    "Error recovery attempted",
                    extra_fields=recovery_result
                )
                
                return workflow_execution
                
            finally:
                client.clear_workflow_context()
            
        except Exception as e:
            logger.error(
                f"Failed to execute workflow {workflow_id} for lead {lead_id}",
                error_category=ErrorCategory.SYSTEM_ERROR,
                extra_fields={
                    "workflow_id": workflow_id,
                    "lead_id": lead_id,
                    "error": str(e)
                }
            )
            self.db.rollback()
            raise
    
    async def create_workflow_from_template(
        self, 
        organization_id: int, 
        template_name: str, 
        workflow_name: str,
        configuration: Dict[str, Any] = None,
        created_by: int = None
    ) -> Tuple[Workflow, N8nWorkflow]:
        """
        Create a new workflow from a template in both n8n and local database.
        """
        try:
            # Get the template configuration (you might want to store these in database)
            template_config = await self._get_workflow_template(template_name)
            if not template_config:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Merge provided configuration with template
            if configuration:
                template_config.update(configuration)
            
            # Create workflow in n8n
            client = await self.get_n8n_client()
            n8n_workflow = await client.create_workflow(
                name=workflow_name,
                nodes=template_config.get("nodes", []),
                connections=template_config.get("connections", {}),
                settings=template_config.get("settings", {}),
                tags=template_config.get("tags", [])
            )
            
            # Create workflow in local database
            db_workflow = Workflow(
                organization_id=organization_id,
                n8n_workflow_id=n8n_workflow.id,
                name=workflow_name,
                description=f"Created from template: {template_name}",
                category=template_config.get("category", "general"),
                trigger_type=template_config.get("trigger_type", "manual"),
                trigger_conditions=template_config.get("trigger_conditions", {}),
                configuration={
                    "template": template_name,
                    "nodes": n8n_workflow.nodes,
                    "connections": n8n_workflow.connections,
                    "settings": n8n_workflow.settings,
                    "tags": n8n_workflow.tags
                },
                is_active=False,  # Start inactive for safety
                created_by=created_by
            )
            
            self.db.add(db_workflow)
            self.db.commit()
            self.db.refresh(db_workflow)
            
            logger.info(f"Created workflow {workflow_name} from template {template_name}")
            return db_workflow, n8n_workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow from template: {e}")
            self.db.rollback()
            raise
    
    async def get_workflow_statistics(self, organization_id: int) -> Dict[str, Any]:
        """Get workflow statistics for an organization."""
        try:
            # Database statistics
            total_workflows = self.db.query(Workflow).filter(
                Workflow.organization_id == organization_id
            ).count()
            
            active_workflows = self.db.query(Workflow).filter(
                Workflow.organization_id == organization_id,
                Workflow.is_active == True
            ).count()
            
            total_executions = self.db.query(WorkflowExecution).join(Workflow).filter(
                Workflow.organization_id == organization_id
            ).count()
            
            # n8n statistics
            client = await self.get_n8n_client()
            n8n_stats = await client.get_workflow_statistics()
            
            return {
                "database_stats": {
                    "total_workflows": total_workflows,
                    "active_workflows": active_workflows,
                    "inactive_workflows": total_workflows - active_workflows,
                    "total_executions": total_executions
                },
                "n8n_stats": n8n_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow statistics: {e}")
            raise
    
    async def activate_workflow(self, workflow_id: int) -> bool:
        """Activate a workflow in both database and n8n."""
        try:
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            client = await self.get_n8n_client()
            success = await client.activate_workflow(workflow.n8n_workflow_id)
            
            if success:
                workflow.is_active = True
                workflow.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Activated workflow {workflow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {e}")
            self.db.rollback()
            raise
    
    async def deactivate_workflow(self, workflow_id: int) -> bool:
        """Deactivate a workflow in both database and n8n."""
        try:
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            client = await self.get_n8n_client()
            success = await client.deactivate_workflow(workflow.n8n_workflow_id)
            
            if success:
                workflow.is_active = False
                workflow.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Deactivated workflow {workflow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
            self.db.rollback()
            raise
    
    async def _get_workflow_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get workflow template configuration. This could be enhanced to load from database."""
        templates = {
            "lead_nurturing": {
                "category": "lead_nurturing",
                "trigger_type": "lead_status_change",
                "trigger_conditions": {"status": "NEW"},
                "nodes": [],  # Would contain actual n8n node configuration
                "connections": {},
                "settings": {},
                "tags": ["lead_nurturing", "automation"]
            },
            "follow_up": {
                "category": "follow_up",
                "trigger_type": "scheduled",
                "trigger_conditions": {"days_after": 3},
                "nodes": [],
                "connections": {},
                "settings": {},
                "tags": ["follow_up", "email"]
            }
        }
        
        return templates.get(template_name)
    
    async def validate_workflow_configuration(self, workflow_id: int) -> Dict[str, Any]:
        """Validate workflow configuration and connectivity."""
        try:
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            client = await self.get_n8n_client()
            
            validation_result = {
                "workflow_exists_in_n8n": False,
                "configuration_valid": False,
                "n8n_active_status": False,
                "database_active_status": workflow.is_active,
                "sync_status": "unknown",
                "errors": []
            }
            
            # Check if workflow exists in n8n
            n8n_workflow = await client.get_workflow(workflow.n8n_workflow_id)
            if n8n_workflow:
                validation_result["workflow_exists_in_n8n"] = True
                validation_result["n8n_active_status"] = n8n_workflow.active
                validation_result["configuration_valid"] = bool(n8n_workflow.nodes)
                
                # Check sync status
                if workflow.is_active == n8n_workflow.active:
                    validation_result["sync_status"] = "synced"
                else:
                    validation_result["sync_status"] = "out_of_sync"
                    validation_result["errors"].append(
                        f"Active status mismatch: DB={workflow.is_active}, n8n={n8n_workflow.active}"
                    )
            else:
                validation_result["errors"].append(f"Workflow {workflow.n8n_workflow_id} not found in n8n")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate workflow {workflow_id}: {e}")
            return {
                "workflow_exists_in_n8n": False,
                "configuration_valid": False,
                "errors": [str(e)]
            } 