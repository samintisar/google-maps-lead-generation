"""
Campaign Management Domain Schemas.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Campaign Schemas
class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "draft"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None


class CampaignCreate(CampaignBase):
    organization_id: int


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None


class Campaign(CampaignBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Campaign Lead Schemas
class CampaignLeadBase(BaseModel):
    status: Optional[str] = "active"


class CampaignLeadCreate(CampaignLeadBase):
    campaign_id: int
    lead_id: int


class CampaignLeadUpdate(BaseModel):
    status: Optional[str] = None


class CampaignLead(CampaignLeadBase):
    id: int
    campaign_id: int
    lead_id: int
    joined_at: datetime

    class Config:
        from_attributes = True


# Campaign Analytics Schemas
class CampaignAnalytics(BaseModel):
    campaign_id: int
    total_leads: int
    active_leads: int
    completed_leads: int
    conversion_rate: float
    total_budget_spent: Optional[float] = None
    cost_per_lead: Optional[float] = None
    roi: Optional[float] = None