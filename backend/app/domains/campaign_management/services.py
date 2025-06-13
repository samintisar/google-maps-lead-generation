"""
Campaign Management Domain Services.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from .models import Campaign, CampaignLead
from .schemas import CampaignCreate, CampaignUpdate, CampaignLeadCreate, CampaignLeadUpdate, CampaignAnalytics


class CampaignService:
    """Service for campaign management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_campaigns(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Campaign]:
        """Get campaigns with optional filtering."""
        query = self.db.query(Campaign)
        
        if organization_id:
            query = query.filter(Campaign.organization_id == organization_id)
        
        if status:
            query = query.filter(Campaign.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get a specific campaign by ID."""
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    def create_campaign(self, campaign_data: CampaignCreate) -> Campaign:
        """Create a new campaign."""
        db_campaign = Campaign(**campaign_data.dict())
        self.db.add(db_campaign)
        self.db.commit()
        self.db.refresh(db_campaign)
        return db_campaign
    
    def update_campaign(self, campaign_id: int, campaign_data: CampaignUpdate) -> Optional[Campaign]:
        """Update a campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        update_data = campaign_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete a campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return False
        
        self.db.delete(campaign)
        self.db.commit()
        return True
    
    def get_campaign_analytics(self, campaign_id: int) -> Optional[CampaignAnalytics]:
        """Get analytics for a specific campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        # Calculate analytics
        total_leads = self.db.query(func.count(CampaignLead.id)).filter(
            CampaignLead.campaign_id == campaign_id
        ).scalar()
        
        active_leads = self.db.query(func.count(CampaignLead.id)).filter(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.status == "active"
        ).scalar()
        
        completed_leads = self.db.query(func.count(CampaignLead.id)).filter(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.status == "completed"
        ).scalar()
        
        conversion_rate = (completed_leads / total_leads * 100) if total_leads > 0 else 0.0
        
        # Calculate cost metrics if budget is available
        cost_per_lead = None
        roi = None
        if campaign.budget and total_leads > 0:
            cost_per_lead = campaign.budget / total_leads
            # ROI calculation would need revenue data
        
        return CampaignAnalytics(
            campaign_id=campaign_id,
            total_leads=total_leads,
            active_leads=active_leads,
            completed_leads=completed_leads,
            conversion_rate=conversion_rate,
            total_budget_spent=campaign.budget,
            cost_per_lead=cost_per_lead,
            roi=roi
        )


class CampaignLeadService:
    """Service for campaign-lead relationship management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_campaign_leads(
        self,
        campaign_id: Optional[int] = None,
        lead_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CampaignLead]:
        """Get campaign-lead relationships with optional filtering."""
        query = self.db.query(CampaignLead)
        
        if campaign_id:
            query = query.filter(CampaignLead.campaign_id == campaign_id)
        
        if lead_id:
            query = query.filter(CampaignLead.lead_id == lead_id)
        
        if status:
            query = query.filter(CampaignLead.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_campaign_lead(self, campaign_lead_id: int) -> Optional[CampaignLead]:
        """Get a specific campaign-lead relationship by ID."""
        return self.db.query(CampaignLead).filter(CampaignLead.id == campaign_lead_id).first()
    
    def add_lead_to_campaign(self, campaign_lead_data: CampaignLeadCreate) -> CampaignLead:
        """Add a lead to a campaign."""
        # Check if relationship already exists
        existing = self.db.query(CampaignLead).filter(
            CampaignLead.campaign_id == campaign_lead_data.campaign_id,
            CampaignLead.lead_id == campaign_lead_data.lead_id
        ).first()
        
        if existing:
            # Update existing relationship
            existing.status = campaign_lead_data.status
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new relationship
        db_campaign_lead = CampaignLead(**campaign_lead_data.dict())
        self.db.add(db_campaign_lead)
        self.db.commit()
        self.db.refresh(db_campaign_lead)
        return db_campaign_lead
    
    def update_campaign_lead(
        self, 
        campaign_lead_id: int, 
        campaign_lead_data: CampaignLeadUpdate
    ) -> Optional[CampaignLead]:
        """Update a campaign-lead relationship."""
        campaign_lead = self.get_campaign_lead(campaign_lead_id)
        if not campaign_lead:
            return None
        
        update_data = campaign_lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign_lead, field, value)
        
        self.db.commit()
        self.db.refresh(campaign_lead)
        return campaign_lead
    
    def remove_lead_from_campaign(self, campaign_lead_id: int) -> bool:
        """Remove a lead from a campaign."""
        campaign_lead = self.get_campaign_lead(campaign_lead_id)
        if not campaign_lead:
            return False
        
        self.db.delete(campaign_lead)
        self.db.commit()
        return True
    
    def bulk_add_leads_to_campaign(self, campaign_id: int, lead_ids: List[int]) -> List[CampaignLead]:
        """Add multiple leads to a campaign."""
        campaign_leads = []
        
        for lead_id in lead_ids:
            campaign_lead_data = CampaignLeadCreate(
                campaign_id=campaign_id,
                lead_id=lead_id
            )
            campaign_lead = self.add_lead_to_campaign(campaign_lead_data)
            campaign_leads.append(campaign_lead)
        
        return campaign_leads