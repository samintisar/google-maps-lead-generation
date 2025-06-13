"""
Analytics Domain Schemas.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


# Integration Schemas
class IntegrationBase(BaseModel):
    name: str
    type: str
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True


class IntegrationCreate(IntegrationBase):
    organization_id: int


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    last_sync: Optional[datetime] = None


class Integration(IntegrationBase):
    id: int
    organization_id: int
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Analytics Report Schemas
class AnalyticsReportBase(BaseModel):
    report_type: str
    title: str
    description: Optional[str] = None
    report_data: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None


class AnalyticsReportCreate(AnalyticsReportBase):
    organization_id: int
    user_id: int


class AnalyticsReport(AnalyticsReportBase):
    id: int
    organization_id: int
    user_id: int
    generated_at: datetime

    class Config:
        from_attributes = True


# Analytics Data Schemas
class LeadAnalytics(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    converted_leads: int
    conversion_rate: float
    average_score: float
    leads_by_source: Dict[str, int]
    leads_by_status: Dict[str, int]


class CampaignAnalytics(BaseModel):
    total_campaigns: int
    active_campaigns: int
    completed_campaigns: int
    total_budget: float
    total_spent: float
    average_roi: float
    campaigns_by_status: Dict[str, int]


class WorkflowAnalytics(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_execution_time: float
    executions_by_type: Dict[str, int]
    executions_by_status: Dict[str, int]


class DashboardAnalytics(BaseModel):
    lead_analytics: LeadAnalytics
    campaign_analytics: CampaignAnalytics
    workflow_analytics: WorkflowAnalytics
    recent_activities: List[Dict[str, Any]]