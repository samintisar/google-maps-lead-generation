"""
Leads API endpoints.
Clean and optimized implementation with proper error handling and logging.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.db.database import get_db
from app.domains.lead_management.models import Lead
from app.db.schemas import LeadCreate, LeadUpdate, Lead as LeadResponse
from app.shared.services.perplexity_service import PerplexityEnrichmentService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by lead status"),
    source: Optional[str] = Query(None, description="Filter by lead source"),
    search: Optional[str] = Query(None, description="Search in name, email, or company"),
    db: Session = Depends(get_db)
):
    """
    Get all leads with optional filtering and pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-1000)
    - **status**: Filter by lead status (new, contacted, qualified, etc.)
    - **source**: Filter by lead source (website, referral, etc.)
    - **search**: Search in name, email, or company fields
    """
    try:
        query = db.query(Lead)
        
        # Apply filters
        if status:
            query = query.filter(Lead.status == status)
        if source:
            query = query.filter(Lead.source == source)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Lead.name.ilike(search_term)) |
                (Lead.email.ilike(search_term)) |
                (Lead.company.ilike(search_term))
            )
        
        # Apply pagination
        leads = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(leads)} leads with filters: status={status}, source={source}, search={search}")
        return leads
        
    except Exception as e:
        logger.error(f"Error retrieving leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving leads")


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID.
    
    - **lead_id**: The ID of the lead to retrieve
    """
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        logger.info(f"Retrieved lead: {lead_id}")
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving lead")


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lead.
    
    - **lead**: Lead data to create
    """
    try:
        db_lead = Lead(**lead.dict())
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Created new lead: {db_lead.id} - {db_lead.name}")
        return db_lead
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating lead")


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead: LeadUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing lead.
    
    - **lead_id**: The ID of the lead to update
    - **lead**: Updated lead data
    """
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for update: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update only provided fields
        update_data = lead.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_lead, field, value)
        
        db_lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Updated lead: {lead_id}")
        return db_lead
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating lead")


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a lead.
    
    - **lead_id**: The ID of the lead to delete
    """
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for deletion: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        db.delete(db_lead)
        db.commit()
        
        logger.info(f"Deleted lead: {lead_id}")
        return {"message": "Lead deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting lead")


@router.patch("/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update only the status of a lead.
    
    - **lead_id**: The ID of the lead to update
    - **status**: New status for the lead
    """
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for status update: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        old_status = db_lead.status
        db_lead.status = status
        db_lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Updated lead {lead_id} status: {old_status} -> {status}")
        return db_lead
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating lead {lead_id} status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating lead status")


@router.post("/{lead_id}/enrich")
async def enrich_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Enrich a lead with Perplexity AI.
    
    - **lead_id**: The ID of the lead to enrich
    """
    try:
        # Get the lead
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for enrichment: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Check if already enriched recently
        if db_lead.enrichment_status == "completed" and db_lead.enriched_at:
            from datetime import timedelta
            # Convert both to offset-naive for comparison
            enriched_at_naive = db_lead.enriched_at.replace(tzinfo=None) if db_lead.enriched_at.tzinfo else db_lead.enriched_at
            if datetime.utcnow() - enriched_at_naive < timedelta(days=7):
                logger.info(f"Lead {lead_id} was recently enriched, returning existing data")
                return {
                    "success": True,
                    "message": "Lead was recently enriched. Using existing data.",
                    "enrichment_data": {
                        "linkedin_profile": db_lead.linkedin_profile,
                        "twitter_profile": db_lead.twitter_profile,
                        "facebook_profile": db_lead.facebook_profile,
                        "instagram_profile": db_lead.instagram_profile,
                        "ideal_customer_profile": db_lead.ideal_customer_profile,
                        "pain_points": db_lead.pain_points,
                        "key_goals": db_lead.key_goals,
                        "company_description": db_lead.company_description,
                        "recent_news": db_lead.recent_news,
                        "key_personnel": db_lead.key_personnel,
                    },
                    "confidence_score": db_lead.enrichment_confidence
                }
        
        # Set enrichment status to pending
        db_lead.enrichment_status = "pending"
        db.commit()
        
        logger.info(f"Starting enrichment for lead: {lead_id}")
        
        # Initialize Perplexity service and perform enrichment
        try:
            perplexity_service = PerplexityEnrichmentService()
            enrichment_data = await perplexity_service.enrich_lead(db_lead)
            
            # Update lead with enrichment data
            db_lead.linkedin_profile = enrichment_data.get("linkedin_profile")
            db_lead.twitter_profile = enrichment_data.get("twitter_profile")
            db_lead.facebook_profile = enrichment_data.get("facebook_profile")
            db_lead.instagram_profile = enrichment_data.get("instagram_profile")
            db_lead.ideal_customer_profile = enrichment_data.get("ideal_customer_profile")
            db_lead.pain_points = enrichment_data.get("pain_points")
            db_lead.key_goals = enrichment_data.get("key_goals")
            db_lead.company_description = enrichment_data.get("company_description")
            db_lead.recent_news = enrichment_data.get("recent_news")
            # Convert key_personnel list to JSONB for database storage
            key_personnel = enrichment_data.get("key_personnel", [])
            db_lead.key_personnel = key_personnel if key_personnel else None
            db_lead.enrichment_confidence = enrichment_data.get("enrichment_confidence", 0.0)
            db_lead.enrichment_status = "completed"
            db_lead.enriched_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_lead)
            
            logger.info(f"Successfully enriched lead: {lead_id} with confidence: {db_lead.enrichment_confidence}")
            
            return {
                "success": True,
                "message": "Lead enrichment completed successfully.",
                "enrichment_data": {
                    "linkedin_profile": db_lead.linkedin_profile,
                    "twitter_profile": db_lead.twitter_profile,
                    "facebook_profile": db_lead.facebook_profile,
                    "instagram_profile": db_lead.instagram_profile,
                    "ideal_customer_profile": db_lead.ideal_customer_profile,
                    "pain_points": db_lead.pain_points,
                    "key_goals": db_lead.key_goals,
                    "company_description": db_lead.company_description,
                    "recent_news": db_lead.recent_news,
                    "key_personnel": db_lead.key_personnel,
                },
                "confidence_score": db_lead.enrichment_confidence
            }
            
        except Exception as enrichment_error:
            # Set enrichment status to failed
            db_lead.enrichment_status = "failed"
            db.commit()
            
            logger.error(f"Enrichment failed for lead {lead_id}: {str(enrichment_error)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Lead enrichment failed: {str(enrichment_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting enrichment for lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting lead enrichment")


@router.get("/{lead_id}/enrichment-status")
async def get_enrichment_status(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the enrichment status of a lead.
    
    - **lead_id**: The ID of the lead to check
    """
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for enrichment status: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {
            "lead_id": lead_id,
            "enrichment_status": db_lead.enrichment_status,
            "enriched_at": db_lead.enriched_at,
            "enrichment_confidence": db_lead.enrichment_confidence,
            "has_enrichment_data": bool(
                db_lead.linkedin_profile or 
                db_lead.ideal_customer_profile or 
                db_lead.pain_points or 
                db_lead.key_goals
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enrichment status for lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting enrichment status") 