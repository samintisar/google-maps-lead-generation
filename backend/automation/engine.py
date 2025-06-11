"""
Automation Engine

Core automation engine that manages script execution, 
data flow, and integration with external services.
Replaces n8n's workflow execution engine.
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import traceback
from .metrics import metrics_collector

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExecutionResult:
    """Result of script execution"""
    script_name: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_id: Optional[str] = None

class AutomationEngine:
    """
    Core automation engine for executing Python automation scripts.
    Provides execution context, error handling, and result tracking.
    """
    
    def __init__(self, db_session_factory, redis_client=None):
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client
        self.scripts: Dict[str, Callable] = {}
        self.execution_history: List[ExecutionResult] = []
        self.active_executions: Dict[str, ExecutionResult] = {}
        
    def register_script(self, name: str, script_func: Callable, metadata: Dict[str, Any] = None):
        """
        Register an automation script
        
        Args:
            name: Unique script name
            script_func: The script function to execute
            metadata: Additional metadata about the script
        """
        self.scripts[name] = {
            'function': script_func,
            'metadata': metadata or {},
            'registered_at': datetime.utcnow()
        }
        logger.info(f"Registered automation script: {name}")
    
    async def execute_script(
        self, 
        script_name: str, 
        context: Dict[str, Any] = None,
        execution_id: str = None
    ) -> ExecutionResult:
        """
        Execute a registered automation script
        
        Args:
            script_name: Name of the script to execute
            context: Execution context data
            execution_id: Optional execution ID for tracking
        
        Returns:
            ExecutionResult with execution details
        """
        if script_name not in self.scripts:
            raise ValueError(f"Script '{script_name}' not found")
        
        execution_id = execution_id or f"{script_name}_{datetime.utcnow().timestamp()}"
        context = context or {}
        
        # Create execution result
        result = ExecutionResult(
            script_name=script_name,
            status=ExecutionStatus.PENDING,
            start_time=datetime.utcnow(),
            execution_id=execution_id
        )
        
        # Track active execution
        self.active_executions[execution_id] = result
        
        # Record metrics start
        metrics_collector.record_script_execution_start(
            script_name=script_name,
            execution_id=execution_id,
            triggered_by=context.get('triggered_by', 'manual')
        )
        
        try:
            logger.info(f"Starting execution of script: {script_name} (ID: {execution_id})")
            result.status = ExecutionStatus.RUNNING
            
            # Prepare execution context
            exec_context = {
                'db_session': self.db_session_factory(),
                'redis': self.redis_client,
                'context': context,
                'execution_id': execution_id,
                'logger': logger
            }
            
            # Execute the script
            script_info = self.scripts[script_name]
            script_func = script_info['function']
            
            # Check if function is async
            if asyncio.iscoroutinefunction(script_func):
                script_result = await script_func(**exec_context)
            else:
                script_result = script_func(**exec_context)
            
            # Success
            result.status = ExecutionStatus.SUCCESS
            result.result_data = script_result if isinstance(script_result, dict) else {'result': script_result}
            result.end_time = datetime.utcnow()
            
            logger.info(f"Successfully executed script: {script_name} (ID: {execution_id})")
            
        except Exception as e:
            # Failure
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.utcnow()
            
            logger.error(f"Failed to execute script {script_name} (ID: {execution_id}): {e}")
            logger.error(traceback.format_exc())
            
        finally:
            # Record metrics end
            error_type = None
            if result.status == ExecutionStatus.FAILED:
                error_type = type(e).__name__ if 'e' in locals() else 'unknown_error'
            
            metrics_collector.record_script_execution_end(
                script_name=script_name,
                execution_id=execution_id,
                status=result.status,
                triggered_by=context.get('triggered_by', 'manual'),
                error_type=error_type
            )
            
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            # Store in history
            self.execution_history.append(result)
            
            # Close database session if exists
            if 'db_session' in exec_context:
                exec_context['db_session'].close()
        
        return result
    
    async def execute_workflow(
        self, 
        workflow_config: Dict[str, Any],
        initial_context: Dict[str, Any] = None
    ) -> List[ExecutionResult]:
        """
        Execute a workflow consisting of multiple scripts
        
        Args:
            workflow_config: Configuration defining the workflow steps
            initial_context: Initial context data for the workflow
        
        Returns:
            List of ExecutionResult for each step
        """
        results = []
        context = initial_context or {}
        workflow_id = f"workflow_{datetime.utcnow().timestamp()}"
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        steps = workflow_config.get('steps', [])
        
        for i, step in enumerate(steps):
            step_name = step.get('name', f"step_{i}")
            script_name = step.get('script')
            step_context = step.get('context', {})
            
            if not script_name:
                logger.error(f"No script specified for step: {step_name}")
                continue
            
            # Merge contexts
            merged_context = {**context, **step_context}
            
            # Execute step
            step_result = await self.execute_script(
                script_name, 
                merged_context, 
                f"{workflow_id}_{step_name}"
            )
            
            results.append(step_result)
            
            # Stop workflow on failure if configured
            if step_result.status == ExecutionStatus.FAILED:
                stop_on_error = step.get('stop_on_error', True)
                if stop_on_error:
                    logger.error(f"Workflow {workflow_id} stopped due to step failure: {step_name}")
                    break
            
            # Update context with step results
            if step_result.result_data:
                context.update(step_result.result_data)
        
        logger.info(f"Completed workflow execution: {workflow_id}")
        return results
    
    def get_script_list(self) -> List[Dict[str, Any]]:
        """Get list of registered scripts"""
        return [
            {
                'name': name,
                'metadata': info['metadata'],
                'registered_at': info['registered_at']
            }
            for name, info in self.scripts.items()
        ]
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """Get recent execution history"""
        return self.execution_history[-limit:] if limit else self.execution_history
    
    def get_active_executions(self) -> Dict[str, ExecutionResult]:
        """Get currently active executions"""
        return self.active_executions.copy()
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an active execution
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        if execution_id in self.active_executions:
            result = self.active_executions[execution_id]
            result.status = ExecutionStatus.CANCELLED
            result.end_time = datetime.utcnow()
            
            # Remove from active executions
            del self.active_executions[execution_id]
            
            # Add to history
            self.execution_history.append(result)
            
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        
        return False
    
    def create_context_builder(self):
        """Create a context builder for script execution"""
        return ContextBuilder()

class ContextBuilder:
    """Helper class for building execution contexts"""
    
    def __init__(self):
        self.context = {}
    
    def add_lead_data(self, lead_id: int):
        """Add lead data to context"""
        self.context['lead_id'] = lead_id
        return self
    
    def add_user_data(self, user_id: int):
        """Add user data to context"""
        self.context['user_id'] = user_id
        return self
    
    def add_custom_data(self, key: str, value: Any):
        """Add custom data to context"""
        self.context[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final context"""
        return self.context.copy() 