"""
Campaign Management Domain.
"""

from .models import Campaign, CampaignLead
from .schemas import (
    Campaign as CampaignSchema,
    CampaignCreate,
    CampaignUpdate,
    CampaignLead as CampaignLeadSchema,
    CampaignLeadCreate,
    CampaignLeadUpdate,
    CampaignAnalytics
)
from .services import CampaignService, CampaignLeadService
from .router import router

__all__ = [
    "Campaign",
    "CampaignLead",
    "CampaignSchema",
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignLeadSchema",
    "CampaignLeadCreate",
    "CampaignLeadUpdate",
    "CampaignAnalytics",
    "CampaignService",
    "CampaignLeadService",
    "router"
]