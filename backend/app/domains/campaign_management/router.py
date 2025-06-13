"""
Campaign Management Domain Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.database import get_db
from .schemas import Campaign, CampaignCreate, CampaignUpdate, CampaignLead, CampaignLeadCreate, CampaignLeadUpdate, CampaignAnalytics
from .services import CampaignService, CampaignLeadService

router = APIRouter()

# Campaign endpoints
@router.get("/campaigns/", response_model=List[Campaign])
def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all campaigns with optional filtering."""
    service = CampaignService(db)
    return service.get_campaigns(skip=skip, limit=limit, organization_id=organization_id, status=status)


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a specific campaign by ID."""
    service = CampaignService(db)
    campaign = service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    return campaign


@router.post("/campaigns/", response_model=Campaign, status_code=status.HTTP_201_CREATED)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign."""
    service = CampaignService(db)
    return service.create_campaign(campaign)


@router.put("/campaigns/{campaign_id}", response_model=Campaign)
def update_campaign(campaign_id: int, campaign_update: CampaignUpdate, db: Session = Depends(get_db)):
    """Update a campaign."""
    service = CampaignService(db)
    campaign = service.update_campaign(campaign_id, campaign_update)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    return campaign


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Delete a campaign."""
    service = CampaignService(db)
    if not service.delete_campaign(campaign_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )


@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
def get_campaign_analytics(campaign_id: int, db: Session = Depends(get_db)):
    """Get analytics for a specific campaign."""
    service = CampaignService(db)
    analytics = service.get_campaign_analytics(campaign_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    return analytics


# Campaign-Lead relationship endpoints
@router.get("/campaign-leads/", response_model=List[CampaignLead])
def get_campaign_leads(
    campaign_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get campaign-lead relationships with optional filtering."""
    service = CampaignLeadService(db)
    return service.get_campaign_leads(
        campaign_id=campaign_id,
        lead_id=lead_id,
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/campaign-leads/{campaign_lead_id}", response_model=CampaignLead)
def get_campaign_lead(campaign_lead_id: int, db: Session = Depends(get_db)):
    """Get a specific campaign-lead relationship by ID."""
    service = CampaignLeadService(db)
    campaign_lead = service.get_campaign_lead(campaign_lead_id)
    if not campaign_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign-lead relationship not found"
        )
    return campaign_lead


@router.post("/campaign-leads/", response_model=CampaignLead, status_code=status.HTTP_201_CREATED)
def add_lead_to_campaign(campaign_lead: CampaignLeadCreate, db: Session = Depends(get_db)):
    """Add a lead to a campaign."""
    service = CampaignLeadService(db)
    return service.add_lead_to_campaign(campaign_lead)


@router.put("/campaign-leads/{campaign_lead_id}", response_model=CampaignLead)
def update_campaign_lead(
    campaign_lead_id: int, 
    campaign_lead_update: CampaignLeadUpdate, 
    db: Session = Depends(get_db)
):
    """Update a campaign-lead relationship."""
    service = CampaignLeadService(db)
    campaign_lead = service.update_campaign_lead(campaign_lead_id, campaign_lead_update)
    if not campaign_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign-lead relationship not found"
        )
    return campaign_lead


@router.delete("/campaign-leads/{campaign_lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lead_from_campaign(campaign_lead_id: int, db: Session = Depends(get_db)):
    """Remove a lead from a campaign."""
    service = CampaignLeadService(db)
    if not service.remove_lead_from_campaign(campaign_lead_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign-lead relationship not found"
        )


@router.post("/campaigns/{campaign_id}/leads/bulk", response_model=List[CampaignLead])
def bulk_add_leads_to_campaign(
    campaign_id: int, 
    lead_ids: List[int], 
    db: Session = Depends(get_db)
):
    """Add multiple leads to a campaign."""
    service = CampaignLeadService(db)
    return service.bulk_add_leads_to_campaign(campaign_id, lead_ids)