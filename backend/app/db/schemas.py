"""
Pydantic schemas for API request/response models based on the new ER diagram.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums for common status fields
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ActivityType(str, Enum):
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Organization schemas
class OrganizationBase(BaseSchema):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class Organization(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime


# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    name: str = Field(..., max_length=255)
    role: str = Field(default="user", max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    organization_id: int


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


# Lead schemas
class LeadBase(BaseSchema):
    name: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    google_maps_url: Optional[str] = Field(None, max_length=500)
    status: LeadStatus = LeadStatus.NEW
    source: Optional[str] = Field(None, max_length=100)
    score: float = Field(default=0.0, ge=0.0)
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    organization_id: int


class LeadUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    google_maps_url: Optional[str] = Field(None, max_length=500)
    status: Optional[LeadStatus] = None
    source: Optional[str] = Field(None, max_length=100)
    score: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None


class Lead(LeadBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


# Campaign schemas
class CampaignBase(BaseSchema):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0.0)


class CampaignCreate(CampaignBase):
    organization_id: int


class CampaignUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0.0)


class Campaign(CampaignBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


# Activity schemas
class ActivityBase(BaseSchema):
    type: ActivityType
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="completed", max_length=100)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    activity_data: Optional[Dict[str, Any]] = None


class ActivityCreate(ActivityBase):
    lead_id: int
    user_id: int


class ActivityUpdate(BaseSchema):
    type: Optional[ActivityType] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=100)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    activity_data: Optional[Dict[str, Any]] = None


class Activity(ActivityBase):
    id: int
    lead_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Workflow schemas
class WorkflowBase(BaseSchema):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[str] = Field(None, max_length=100)
    trigger_conditions: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: bool = True


class WorkflowCreate(WorkflowBase):
    organization_id: int
    user_id: int


class WorkflowUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[str] = Field(None, max_length=100)
    trigger_conditions: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class Workflow(WorkflowBase):
    id: int
    organization_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Lead Scoring Rule schemas
class LeadScoringRuleBase(BaseSchema):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., max_length=100)
    conditions: Dict[str, Any]
    score_value: float
    is_active: bool = True


class LeadScoringRuleCreate(LeadScoringRuleBase):
    organization_id: int
    lead_id: Optional[int] = None


class LeadScoringRuleUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, max_length=100)
    conditions: Optional[Dict[str, Any]] = None
    score_value: Optional[float] = None
    is_active: Optional[bool] = None


class LeadScoringRule(LeadScoringRuleBase):
    id: int
    organization_id: int
    lead_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Campaign Lead schemas
class CampaignLeadBase(BaseSchema):
    status: str = Field(default="active", max_length=100)


class CampaignLeadCreate(CampaignLeadBase):
    campaign_id: int
    lead_id: int


class CampaignLeadUpdate(BaseSchema):
    status: Optional[str] = Field(None, max_length=100)


class CampaignLead(CampaignLeadBase):
    id: int
    campaign_id: int
    lead_id: int
    joined_at: datetime


# Integration schemas
class IntegrationBase(BaseSchema):
    name: str = Field(..., max_length=255)
    type: str = Field(..., max_length=100)
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: bool = True


class IntegrationCreate(IntegrationBase):
    organization_id: int


class IntegrationUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=100)
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Integration(IntegrationBase):
    id: int
    organization_id: int
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Response schemas with relationships
class LeadWithActivities(Lead):
    activities: List[Activity] = []


class CampaignWithLeads(Campaign):
    campaign_leads: List[CampaignLead] = []


class OrganizationWithDetails(Organization):
    users: List[User] = []
    leads: List[Lead] = []
    campaigns: List[Campaign] = []