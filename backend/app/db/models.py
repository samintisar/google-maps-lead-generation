"""
Unified Models Import.
This file imports all models from different domains to maintain backward compatibility
and provide a single point of access for database operations.
"""

# Import Base from core models
from .core_models import Base, Organization, User

# Import domain models
from ..domains.lead_management.models import Lead, Activity, LeadScoringRule
from ..domains.campaign_management.models import Campaign, CampaignLead
from ..domains.workflow_execution.models import Workflow, WorkflowExecution
from ..domains.analytics.models import Integration, AnalyticsReport

# Export all models for backward compatibility
__all__ = [
    "Base",
    "Organization",
    "User",
    "Lead",
    "Activity", 
    "LeadScoringRule",
    "Campaign",
    "CampaignLead",
    "Workflow",
    "WorkflowExecution",
    "Integration",
    "AnalyticsReport"
]