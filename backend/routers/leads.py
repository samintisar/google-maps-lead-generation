"""
Lead management API endpoints.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import os

from database import get_db
from models import Lead, User, Organization, LeadStatus, LeadSource, LeadTemperature, LeadScoreHistory, ActivityLog
from schemas import (
    LeadCreate, LeadUpdate, LeadResponse, 
    APIResponse, ListResponse
)
from routers.auth import get_current_active_user, get_dev_user
from services import LeadScoringService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


# Development endpoint - no auth required
@router.get("/dev", response_model=ListResponse)
async def get_leads_dev(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    status_filter: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    source_filter: Optional[LeadSource] = Query(None, description="Filter by lead source"),
    search: Optional[str] = Query(None, description="Search in name, email, or company"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    test_scoring: bool = Query(False, description="Test the scoring logic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads with filtering and pagination for development."""
    
    # If test_scoring is True, return the same data as for-scoring endpoint
    if test_scoring:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow (same as for-scoring endpoint)
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat(),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
                # Mock behavioral data - in real implementation, this would come from tracking
                "website_visits": 0,
                "pages_viewed": 0,
                "email_opens": 0,
                "email_clicks": 0,
                "downloads": 0,
                "company_size": 100,  # Default company size
                "industry": "technology",  # Default industry
                "unsubscribed": False,
                "bounced_emails": 0
            })
        
        # Return as ListResponse to match the endpoint signature
        return ListResponse(
            items=formatted_leads,
            total=len(formatted_leads),
            page=1,
            per_page=len(formatted_leads),
            pages=1
        )
    
    # Original dev endpoint logic
    # Duplicate the logic from get_leads since we can't call it directly
    query = db.query(Lead).filter(Lead.organization_id == current_user.organization_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if source_filter:
        query = query.filter(Lead.source == source_filter)
    
    if assigned_to_id:
        query = query.filter(Lead.assigned_to_id == assigned_to_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.first_name.ilike(search_term),
                Lead.last_name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.company.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    leads = query.offset(skip).limit(limit).all()
    
    return ListResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.post("/dev", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_dev(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Create a new lead for development."""
    # Set organization_id to the dev user's organization if not provided
    if not hasattr(lead_data, 'organization_id') or not lead_data.organization_id:
        lead_data.organization_id = current_user.organization_id
    
    # Check if lead with same email already exists in this organization
    existing_lead = db.query(Lead).filter(
        Lead.email == lead_data.email,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists in the organization"
        )
    
    # Create new lead
    lead_dict = lead_data.model_dump()
    lead_dict['organization_id'] = current_user.organization_id
    db_lead = Lead(**lead_dict)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    return APIResponse(
        success=True,
        data=LeadResponse.model_validate(db_lead),
        message="Lead created successfully"
    )


@router.get("/dev/{lead_id}", response_model=LeadResponse)
async def get_lead_dev(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get a specific lead by ID for development."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return LeadResponse.model_validate(lead)


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new lead."""
    # Validate organization exists and user has access
    organization = db.query(Organization).filter(
        Organization.id == lead_data.organization_id,
        Organization.is_active == True
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if user belongs to the organization (for multi-tenancy)
    if current_user.organization_id and current_user.organization_id != lead_data.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    # Check if lead with same email already exists in this organization
    existing_lead = db.query(Lead).filter(
        Lead.email == lead_data.email,
        Lead.organization_id == lead_data.organization_id
    ).first()
    
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists in the organization"
        )
    
    # Create new lead
    db_lead = Lead(**lead_data.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    return APIResponse(
        success=True,
        data=LeadResponse.model_validate(db_lead),
        message="Lead created successfully"
    )


@router.get("/", response_model=ListResponse)
async def get_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    status_filter: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    source_filter: Optional[LeadSource] = Query(None, description="Filter by lead source"),
    search: Optional[str] = Query(None, description="Search in name, email, or company"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get leads with filtering and pagination."""
    query = db.query(Lead).filter(Lead.organization_id == current_user.organization_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if source_filter:
        query = query.filter(Lead.source == source_filter)
    
    if assigned_to_id:
        query = query.filter(Lead.assigned_to_id == assigned_to_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.first_name.ilike(search_term),
                Lead.last_name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.company.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    leads = query.offset(skip).limit(limit).all()
    
    return ListResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific lead by ID."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=APIResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a lead."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Update fields
    update_data = lead_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    db.commit()
    db.refresh(lead)
    
    return APIResponse(
        success=True,
        data=LeadResponse.model_validate(lead),
        message="Lead updated successfully"
    )


@router.delete("/{lead_id}", response_model=APIResponse)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a lead."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    db.delete(lead)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Lead deleted successfully"
    )


@router.patch("/{lead_id}/status", response_model=APIResponse)
async def update_lead_status(
    lead_id: int,
    new_status: LeadStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lead status."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    old_status = lead.status
    lead.status = new_status
    db.commit()
    
    return APIResponse(
        success=True,
        data={"old_status": old_status.value, "new_status": new_status.value},
        message="Lead status updated successfully"
    )


@router.patch("/{lead_id}/assign", response_model=APIResponse)
async def assign_lead(
    lead_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign lead to a user."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Validate user exists and belongs to the same organization
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this organization"
        )
    
    lead.assigned_to_id = user_id
    db.commit()
    
    return APIResponse(
        success=True,
        data={"assigned_to": user.full_name},
        message="Lead assigned successfully"
    )


# Lead Scoring Endpoints

@router.get("/{lead_id}/score/calculate", response_model=APIResponse)
async def calculate_lead_score(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate lead score without updating it."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    try:
        scoring_service = LeadScoringService(db)
        score_result = await scoring_service.calculate_lead_score(lead_id)
        
        return APIResponse(
            success=True,
            data=score_result,
            message="Lead score calculated successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate lead score: {str(e)}"
        )


@router.post("/{lead_id}/score/update", response_model=APIResponse)
async def update_lead_score(
    lead_id: int,
    reason: Optional[str] = Query("Manual score update", description="Reason for score update"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lead score and track the change."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    try:
        scoring_service = LeadScoringService(db)
        update_result = await scoring_service.update_lead_score(lead_id, reason)
        
        return APIResponse(
            success=True,
            data=update_result,
            message="Lead score updated successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead score: {str(e)}"
        )


@router.get("/{lead_id}/score/history", response_model=APIResponse)
async def get_lead_score_history(
    lead_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of history records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lead score change history."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    try:
        scoring_service = LeadScoringService(db)
        history = await scoring_service.get_lead_score_history(lead_id, limit)
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "current_score": lead.score,
                "history": history
            },
            message="Lead score history retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lead score history: {str(e)}"
        )


@router.post("/score/bulk-update", response_model=APIResponse)
async def bulk_update_lead_scores(
    lead_ids: Optional[List[int]] = Query(None, description="Specific lead IDs to update, if empty all leads in organization will be updated"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update lead scores for organization."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    try:
        scoring_service = LeadScoringService(db)
        results = await scoring_service.bulk_update_scores(
            current_user.organization_id, 
            lead_ids
        )
        
        return APIResponse(
            success=True,
            data=results,
            message=f"Bulk score update completed: {results['summary']['successful_updates']} successful, {results['summary']['failed_updates']} failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update scores: {str(e)}"
        )


@router.get("/score/analytics", response_model=APIResponse)
async def get_scoring_analytics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get scoring analytics for the organization."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    try:
        scoring_service = LeadScoringService(db)
        analytics = await scoring_service.get_scoring_analytics(
            current_user.organization_id,
            days_back
        )
        
        return APIResponse(
            success=True,
            data=analytics,
            message="Scoring analytics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring analytics: {str(e)}"
        )


# === N8N WORKFLOW SPECIFIC ENDPOINTS ===

# Test endpoint without authentication
@router.get("/test-no-auth", response_model=APIResponse)
async def test_endpoint_no_auth():
    """Test endpoint without authentication to verify backend is working."""
    return APIResponse(
        success=True,
        data={"message": "Backend is working!", "timestamp": datetime.utcnow().isoformat()},
        message="Test endpoint working"
    )

# Debug endpoint to test get_dev_user function
@router.get("/debug-dev-user", response_model=APIResponse)
async def debug_dev_user_endpoint(
    db: Session = Depends(get_db)
):
    """Debug endpoint to test get_dev_user function."""
    try:
        from config import settings
        env_info = {
            "environment": settings.environment,
            "environment_raw": os.getenv("ENVIRONMENT", "not_set")
        }
        
        # Try to call get_dev_user manually
        dev_user = get_dev_user(db)
        
        return APIResponse(
            success=True,
            data={
                "env_info": env_info,
                "dev_user": {
                    "id": dev_user.id,
                    "email": dev_user.email,
                    "username": dev_user.username,
                    "organization_id": dev_user.organization_id
                }
            },
            message="get_dev_user working"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            data={"error": str(e), "type": type(e).__name__},
            message="get_dev_user failed"
        )

@router.get("/for-scoring-test", response_model=APIResponse)
async def get_leads_for_scoring_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Simple test version of get leads for scoring."""
    return APIResponse(
        success=True,
        data={"message": "for-scoring-test working!", "user_id": current_user.id},
        message="Test successful"
    )

@router.get("/for-scoring")
async def get_leads_for_scoring(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for leads"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads that need scoring (for n8n workflow)."""
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat(),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
                # Mock behavioral data - in real implementation, this would come from tracking
                "website_visits": 0,
                "pages_viewed": 0,
                "email_opens": 0,
                "email_clicks": 0,
                "downloads": 0,
                "company_size": 100,  # Default company size
                "industry": "technology",  # Default industry
                "unsubscribed": False,
                "bounced_emails": 0
            })
        
        return {
            "success": True,
            "data": formatted_leads,
            "message": f"Retrieved {len(formatted_leads)} leads for scoring"
        }
        
    except Exception as e:
        logger.error(f"Failed to get leads for scoring: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"Failed to get leads for scoring: {str(e)}"
        }


@router.post("/score/bulk-update-n8n", response_model=APIResponse)
async def bulk_update_lead_scores_n8n(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Bulk update lead scores from n8n workflow."""
    try:
        updated_leads = []
        failed_updates = []
        
        for update_data in updates:
            try:
                lead_id = update_data.get("id")
                new_score = update_data.get("score", 0)
                lead_temperature = update_data.get("lead_temperature", "cold")
                score_breakdown = update_data.get("score_breakdown", {})
                
                # Get the lead
                lead = db.query(Lead).filter(
                    Lead.id == lead_id,
                    Lead.organization_id == current_user.organization_id
                ).first()
                
                if not lead:
                    failed_updates.append({
                        "lead_id": lead_id,
                        "error": "Lead not found"
                    })
                    continue
                
                # Track previous score
                previous_score = lead.score or 0
                score_change = new_score - previous_score
                
                # Update lead
                lead.score = new_score
                lead.lead_temperature = LeadTemperature(lead_temperature)
                lead.updated_at = datetime.utcnow()
                
                # Add score history
                score_history = LeadScoreHistory(
                    lead_id=lead_id,
                    previous_score=previous_score,
                    new_score=new_score,
                    score_change=score_change,
                    reason="n8n automated scoring",
                    created_at=datetime.utcnow()
                )
                db.add(score_history)
                
                # Add activity log
                activity_log = ActivityLog(
                    lead_id=lead_id,
                    activity_type="score_updated",
                    description=f"Lead score updated by n8n workflow from {previous_score} to {new_score} ({score_change:+d})",
                    activity_metadata={
                        "previous_score": previous_score,
                        "new_score": new_score,
                        "score_change": score_change,
                        "score_breakdown": score_breakdown,
                        "lead_temperature": lead_temperature,
                        "source": "n8n_workflow"
                    },
                    created_at=datetime.utcnow()
                )
                db.add(activity_log)
                
                updated_leads.append({
                    "lead_id": lead_id,
                    "previous_score": previous_score,
                    "new_score": new_score,
                    "score_change": score_change,
                    "lead_temperature": lead_temperature
                })
                
            except Exception as e:
                failed_updates.append({
                    "lead_id": update_data.get("id", "unknown"),
                    "error": str(e)
                })
        
        # Commit all changes
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "updated_leads": updated_leads,
                "failed_updates": failed_updates,
                "summary": {
                    "successful_updates": len(updated_leads),
                    "failed_updates": len(failed_updates),
                    "total_processed": len(updates)
                }
            },
            message=f"Bulk update completed: {len(updated_leads)} successful, {len(failed_updates)} failed"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bulk update scores from n8n: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update scores: {str(e)}"
        )


@router.post("/activity/log", response_model=APIResponse)
async def log_lead_activity(
    activity_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Log lead activity from n8n workflow."""
    try:
        lead_id = activity_data.get("lead_id")
        activity_type = activity_data.get("activity_type", "workflow_activity")
        description = activity_data.get("description", "Activity logged by n8n workflow")
        metadata = activity_data.get("activity_data", {})
        
        # Verify lead exists and belongs to organization
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Create activity log
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type=activity_type,
            description=description,
            activity_metadata=metadata,
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "activity_id": activity_log.id,
                "lead_id": lead_id,
                "activity_type": activity_type,
                "logged_at": activity_log.created_at.isoformat()
            },
            message="Activity logged successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log activity: {str(e)}"
        )

# Working alternative for n8n - using a route pattern we know works
@router.get("/n8n-scoring", response_model=APIResponse)
async def get_leads_for_n8n_scoring(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for leads"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads that need scoring (for n8n workflow) - working alternative endpoint."""
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat(),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
                # Mock behavioral data - in real implementation, this would come from tracking
                "website_visits": 0,
                "pages_viewed": 0,
                "email_opens": 0,
                "email_clicks": 0,
                "downloads": 0,
                "company_size": 100,  # Default company size
                "industry": "technology",  # Default industry
                "unsubscribed": False,
                "bounced_emails": 0
            })
        
        return APIResponse(
            success=True,
            data=formatted_leads,
            message=f"Retrieved {len(formatted_leads)} leads for scoring"
        )
        
    except Exception as e:
        logger.error(f"Failed to get leads for scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leads for scoring: {str(e)}"
        ) 