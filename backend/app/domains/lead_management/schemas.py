"""
Lead Management Domain Schemas.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Lead Schemas
class LeadBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    google_maps_url: Optional[str] = None
    status: Optional[str] = "new"
    source: Optional[str] = None
    score: Optional[float] = 0.0
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    organization_id: int


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    google_maps_url: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    notes: Optional[str] = None


class Lead(LeadBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Activity Schemas
class ActivityBase(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = "completed"
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    activity_data: Optional[dict] = None


class ActivityCreate(ActivityBase):
    lead_id: int
    user_id: int


class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    activity_data: Optional[dict] = None


class Activity(ActivityBase):
    id: int
    lead_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lead Scoring Rule Schemas
class LeadScoringRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str
    conditions: dict
    score_value: float
    is_active: Optional[bool] = True


class LeadScoringRuleCreate(LeadScoringRuleBase):
    organization_id: int
    lead_id: Optional[int] = None


class LeadScoringRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    conditions: Optional[dict] = None
    score_value: Optional[float] = None
    is_active: Optional[bool] = None


class LeadScoringRule(LeadScoringRuleBase):
    id: int
    organization_id: int
    lead_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True