"""
Analytics Domain.
"""

from .models import Integration, AnalyticsReport
from .schemas import (
    Integration as IntegrationSchema,
    IntegrationCreate,
    IntegrationUpdate,
    AnalyticsReport as AnalyticsReportSchema,
    AnalyticsReportCreate,
    LeadAnalytics,
    CampaignAnalytics,
    WorkflowAnalytics,
    DashboardAnalytics
)
from .services import IntegrationService, AnalyticsService
from .router import router

__all__ = [
    "Integration",
    "AnalyticsReport",
    "IntegrationSchema",
    "IntegrationCreate",
    "IntegrationUpdate",
    "AnalyticsReportSchema",
    "AnalyticsReportCreate",
    "LeadAnalytics",
    "CampaignAnalytics",
    "WorkflowAnalytics",
    "DashboardAnalytics",
    "IntegrationService",
    "AnalyticsService",
    "router"
]