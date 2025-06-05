"""
Lead management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database import get_db
from models import Lead, User, Organization, LeadStatus, LeadSource
from schemas import (
    LeadCreate, LeadUpdate, LeadResponse, 
    APIResponse, ListResponse
)
from routers.auth import get_current_active_user
from services import LeadScoringService

router = APIRouter(prefix="/leads", tags=["leads"])


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