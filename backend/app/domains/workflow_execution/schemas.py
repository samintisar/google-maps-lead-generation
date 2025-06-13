"""
Workflow Execution Domain Schemas.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


# Workflow Schemas
class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: Optional[str] = "manual"
    trigger_conditions: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = True


class WorkflowCreate(WorkflowBase):
    organization_id: int
    user_id: int


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class Workflow(WorkflowBase):
    id: int
    organization_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workflow Execution Schemas
class WorkflowExecutionBase(BaseModel):
    status: Optional[str] = "running"
    current_step: Optional[str] = None
    progress_percentage: Optional[int] = 0
    execution_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowExecutionCreate(WorkflowExecutionBase):
    id: str  # UUID
    workflow_id: Optional[int] = None  # Made optional for dynamic workflows
    organization_id: int
    user_id: int


class WorkflowExecutionUpdate(BaseModel):
    status: Optional[str] = None
    current_step: Optional[str] = None
    progress_percentage: Optional[int] = None
    execution_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class WorkflowExecution(WorkflowExecutionBase):
    id: str
    workflow_id: Optional[int] = None  # Made optional for dynamic workflows
    organization_id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Workflow Engine Schemas
class WorkflowResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}


# Google Maps Workflow Schemas
class GoogleMapsStartRequest(BaseModel):
    location: str
    industry: str
    max_results: int = 10


class GoogleMapsLead(BaseModel):
    id: int
    business_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: str
    location: str
    enrichment_status: str = "pending"
    conversion_status: str = "pending"


# Email Campaign Workflow Schemas
class EmailCampaignStartRequest(BaseModel):
    campaign_id: int
    template_id: Optional[int] = None
    subject: str
    content: str
    send_immediately: bool = False
    scheduled_at: Optional[datetime] = None


# Lead Scoring Workflow Schemas
class LeadScoringStartRequest(BaseModel):
    organization_id: int
    lead_ids: Optional[List[int]] = None  # If None, score all leads
    rule_ids: Optional[List[int]] = None  # If None, use all active rules