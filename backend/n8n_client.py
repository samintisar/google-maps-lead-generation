"""
n8n API Client for Lead Management Automation Platform.
Handles all interactions with the n8n workflow engine.
"""
import httpx
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

@dataclass
class WorkflowExecutionResult:
    """Result of a workflow execution."""
    execution_id: str
    workflow_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class N8nWorkflow:
    """n8n workflow representation."""
    id: str
    name: str
    active: bool
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    settings: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

class N8nClient:
    """
    Client for interacting with n8n API.
    Handles workflow management, execution, and monitoring.
    """
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """Initialize n8n client."""
        self.base_url = base_url or settings.n8n_api_base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        logger.info(f"Initialized n8n client with base URL: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if n8n service is healthy."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"n8n health check failed: {e}")
            return False
    
    # Workflow Management
    async def get_workflows(self, active_only: bool = None) -> List[N8nWorkflow]:
        """Get all workflows from n8n."""
        try:
            params = {}
            if active_only is not None:
                params["active"] = str(active_only).lower()
            
            response = await self.client.get("/workflows", params=params)
            response.raise_for_status()
            
            workflows_data = response.json()
            workflows = []
            
            for workflow_data in workflows_data.get("data", []):
                workflow = N8nWorkflow(
                    id=workflow_data["id"],
                    name=workflow_data["name"],
                    active=workflow_data.get("active", False),
                    nodes=workflow_data.get("nodes", []),
                    connections=workflow_data.get("connections", {}),
                    settings=workflow_data.get("settings", {}),
                    tags=workflow_data.get("tags", []),
                    created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00"))
                )
                workflows.append(workflow)
            
            logger.info(f"Retrieved {len(workflows)} workflows from n8n")
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[N8nWorkflow]:
        """Get a specific workflow by ID."""
        try:
            response = await self.client.get(f"/workflows/{workflow_id}")
            response.raise_for_status()
            
            workflow_data = response.json()
            workflow = N8nWorkflow(
                id=workflow_data["id"],
                name=workflow_data["name"],
                active=workflow_data.get("active", False),
                nodes=workflow_data.get("nodes", []),
                connections=workflow_data.get("connections", {}),
                settings=workflow_data.get("settings", {}),
                tags=workflow_data.get("tags", []),
                created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00"))
            )
            
            logger.info(f"Retrieved workflow {workflow_id}: {workflow.name}")
            return workflow
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Workflow {workflow_id} not found")
                return None
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise
    
    async def create_workflow(self, name: str, nodes: List[Dict], connections: Dict[str, Any], 
                            settings: Dict[str, Any] = None, tags: List[str] = None) -> N8nWorkflow:
        """Create a new workflow in n8n."""
        try:
            workflow_data = {
                "name": name,
                "nodes": nodes,
                "connections": connections,
                "settings": settings or {},
                "tags": tags or []
            }
            
            response = await self.client.post("/workflows", json=workflow_data)
            response.raise_for_status()
            
            created_workflow = response.json()
            workflow = N8nWorkflow(
                id=created_workflow["id"],
                name=created_workflow["name"],
                active=created_workflow.get("active", False),
                nodes=created_workflow.get("nodes", []),
                connections=created_workflow.get("connections", {}),
                settings=created_workflow.get("settings", {}),
                tags=created_workflow.get("tags", []),
                created_at=datetime.fromisoformat(created_workflow["createdAt"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(created_workflow["updatedAt"].replace("Z", "+00:00"))
            )
            
            logger.info(f"Created workflow {workflow.id}: {workflow.name}")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def update_workflow(self, workflow_id: str, **kwargs) -> N8nWorkflow:
        """Update an existing workflow."""
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            
            response = await self.client.patch(f"/workflows/{workflow_id}", json=update_data)
            response.raise_for_status()
            
            updated_workflow = response.json()
            workflow = N8nWorkflow(
                id=updated_workflow["id"],
                name=updated_workflow["name"],
                active=updated_workflow.get("active", False),
                nodes=updated_workflow.get("nodes", []),
                connections=updated_workflow.get("connections", {}),
                settings=updated_workflow.get("settings", {}),
                tags=updated_workflow.get("tags", []),
                created_at=datetime.fromisoformat(updated_workflow["createdAt"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(updated_workflow["updatedAt"].replace("Z", "+00:00"))
            )
            
            logger.info(f"Updated workflow {workflow_id}")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow from n8n."""
        try:
            response = await self.client.delete(f"/workflows/{workflow_id}")
            response.raise_for_status()
            
            logger.info(f"Deleted workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            raise
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        try:
            response = await self.client.post(f"/workflows/{workflow_id}/activate")
            response.raise_for_status()
            
            logger.info(f"Activated workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {e}")
            raise
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        try:
            response = await self.client.post(f"/workflows/{workflow_id}/deactivate")
            response.raise_for_status()
            
            logger.info(f"Deactivated workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
            raise
    
    # Workflow Execution
    async def execute_workflow(self, workflow_id: str, data: Dict[str, Any] = None) -> WorkflowExecutionResult:
        """Execute a workflow manually with optional input data."""
        try:
            execution_data = {
                "workflowData": data or {}
            }
            
            response = await self.client.post(f"/workflows/{workflow_id}/execute", json=execution_data)
            response.raise_for_status()
            
            execution = response.json()
            
            result = WorkflowExecutionResult(
                execution_id=execution["data"]["executionId"],
                workflow_id=workflow_id,
                status=execution["data"]["status"],
                start_time=datetime.fromisoformat(execution["data"]["startedAt"].replace("Z", "+00:00")),
                end_time=datetime.fromisoformat(execution["data"]["stoppedAt"].replace("Z", "+00:00")) if execution["data"].get("stoppedAt") else None,
                error=execution["data"].get("error"),
                data=execution["data"].get("data")
            )
            
            logger.info(f"Executed workflow {workflow_id}, execution ID: {result.execution_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise
    
    async def get_executions(self, workflow_id: str = None, limit: int = 50, status: str = None) -> List[WorkflowExecutionResult]:
        """Get workflow executions."""
        try:
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id
            if status:
                params["status"] = status
            
            response = await self.client.get("/executions", params=params)
            response.raise_for_status()
            
            executions_data = response.json()
            executions = []
            
            for execution_data in executions_data.get("data", []):
                execution = WorkflowExecutionResult(
                    execution_id=execution_data["id"],
                    workflow_id=execution_data["workflowId"],
                    status=execution_data["status"],
                    start_time=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")),
                    end_time=datetime.fromisoformat(execution_data["stoppedAt"].replace("Z", "+00:00")) if execution_data.get("stoppedAt") else None,
                    error=execution_data.get("error"),
                    data=execution_data.get("data")
                )
                executions.append(execution)
            
            logger.info(f"Retrieved {len(executions)} executions")
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions: {e}")
            raise
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionResult]:
        """Get a specific execution by ID."""
        try:
            response = await self.client.get(f"/executions/{execution_id}")
            response.raise_for_status()
            
            execution_data = response.json()
            execution = WorkflowExecutionResult(
                execution_id=execution_data["id"],
                workflow_id=execution_data["workflowId"],
                status=execution_data["status"],
                start_time=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")),
                end_time=datetime.fromisoformat(execution_data["stoppedAt"].replace("Z", "+00:00")) if execution_data.get("stoppedAt") else None,
                error=execution_data.get("error"),
                data=execution_data.get("data")
            )
            
            logger.info(f"Retrieved execution {execution_id}")
            return execution
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Execution {execution_id} not found")
                return None
            logger.error(f"Failed to get execution {execution_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            raise
    
    async def stop_execution(self, execution_id: str) -> bool:
        """Stop a running execution."""
        try:
            response = await self.client.post(f"/executions/{execution_id}/stop")
            response.raise_for_status()
            
            logger.info(f"Stopped execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop execution {execution_id}: {e}")
            raise
    
    # Webhook Management
    async def trigger_webhook(self, webhook_path: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """Trigger an n8n webhook."""
        try:
            webhook_url = f"{self.base_url.replace('/api/v1', '')}/webhook/{webhook_path}"
            
            if method.upper() == "GET":
                response = await self.client.get(webhook_url, params=data)
            else:
                response = await self.client.post(webhook_url, json=data)
            
            response.raise_for_status()
            
            result = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"message": "Webhook triggered successfully"}
            
            logger.info(f"Triggered webhook {webhook_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to trigger webhook {webhook_path}: {e}")
            raise
    
    # Utility Methods
    async def get_active_workflows_count(self) -> int:
        """Get count of active workflows."""
        try:
            workflows = await self.get_workflows(active_only=True)
            return len(workflows)
        except Exception as e:
            logger.error(f"Failed to get active workflows count: {e}")
            return 0
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        try:
            # Get all workflows
            all_workflows = await self.get_workflows()
            active_workflows = [w for w in all_workflows if w.active]
            
            # Get recent executions
            recent_executions = await self.get_executions(limit=100)
            successful_executions = [e for e in recent_executions if e.status == "success"]
            failed_executions = [e for e in recent_executions if e.status == "error"]
            
            stats = {
                "total_workflows": len(all_workflows),
                "active_workflows": len(active_workflows),
                "inactive_workflows": len(all_workflows) - len(active_workflows),
                "total_executions": len(recent_executions),
                "successful_executions": len(successful_executions),
                "failed_executions": len(failed_executions),
                "success_rate": (len(successful_executions) / len(recent_executions) * 100) if recent_executions else 0
            }
            
            logger.info("Generated workflow statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get workflow statistics: {e}")
            return {}

# Convenience function for creating client instances
async def get_n8n_client() -> N8nClient:
    """Get an n8n client instance."""
    return N8nClient()

# Example workflow templates for lead management
LEAD_NURTURING_WORKFLOW_TEMPLATE = {
    "name": "Lead Nurturing Email Sequence",
    "nodes": [
        {
            "parameters": {},
            "name": "When clicking \"Test workflow\"",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [740, 240],
            "id": "start"
        },
        {
            "parameters": {
                "httpMethod": "POST",
                "path": "lead-nurture",
                "responseMode": "responseNode",
                "options": {}
            },
            "name": "Lead Data Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [740, 380],
            "webhookId": "lead-nurture"
        },
        {
            "parameters": {
                "amount": 24,
                "unit": "hours"
            },
            "name": "Wait 24 Hours",
            "type": "n8n-nodes-base.wait",
            "typeVersion": 1,
            "position": [960, 380]
        },
        {
            "parameters": {
                "subject": "Welcome to our platform!",
                "emailType": "html",
                "html": "<h1>Welcome {{$json.firstName}}!</h1><p>Thank you for your interest in our platform.</p>",
                "toEmail": "={{$json.email}}"
            },
            "name": "Send Welcome Email",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2,
            "position": [1180, 380]
        }
    ],
    "connections": {
        "When clicking \"Test workflow\"": {
            "main": [
                [
                    {
                        "node": "Send Welcome Email",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "Lead Data Webhook": {
            "main": [
                [
                    {
                        "node": "Wait 24 Hours",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "Wait 24 Hours": {
            "main": [
                [
                    {
                        "node": "Send Welcome Email",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    },
    "settings": {
        "timezone": "America/New_York"
    },
    "tags": ["lead-management", "nurturing", "email"]
} 