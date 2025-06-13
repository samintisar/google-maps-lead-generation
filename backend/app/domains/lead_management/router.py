"""
Lead Management Domain Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.database import get_db
from .schemas import Lead, LeadCreate, LeadUpdate, Activity, ActivityCreate, ActivityUpdate, LeadScoringRule, LeadScoringRuleCreate, LeadScoringRuleUpdate
from .services import LeadService, ActivityService, LeadScoringService

router = APIRouter()

# Lead endpoints
@router.get("/leads/", response_model=List[Lead])
def get_leads(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all leads with optional filtering."""
    service = LeadService(db)
    return service.get_leads(skip=skip, limit=limit, organization_id=organization_id, status=status)


@router.get("/leads/{lead_id}", response_model=Lead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    service = LeadService(db)
    lead = service.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead


@router.post("/leads/", response_model=Lead, status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead."""
    service = LeadService(db)
    return service.create_lead(lead)


@router.put("/leads/{lead_id}", response_model=Lead)
def update_lead(lead_id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    """Update a lead."""
    service = LeadService(db)
    lead = service.update_lead(lead_id, lead_update)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead."""
    service = LeadService(db)
    if not service.delete_lead(lead_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )


@router.post("/leads/{lead_id}/calculate-score", response_model=dict)
def calculate_lead_score(lead_id: int, db: Session = Depends(get_db)):
    """Calculate and update lead score."""
    service = LeadService(db)
    score = service.calculate_lead_score(lead_id)
    return {"lead_id": lead_id, "score": score}


# Activity endpoints
@router.get("/activities/", response_model=List[Activity])
def get_activities(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[int] = None,
    user_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all activities with optional filtering."""
    service = ActivityService(db)
    return service.get_activities(
        skip=skip, 
        limit=limit, 
        lead_id=lead_id, 
        user_id=user_id, 
        activity_type=activity_type
    )


@router.get("/activities/{activity_id}", response_model=Activity)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """Get a specific activity by ID."""
    service = ActivityService(db)
    activity = service.get_activity(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity


@router.post("/activities/", response_model=Activity, status_code=status.HTTP_201_CREATED)
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    """Create a new activity."""
    service = ActivityService(db)
    return service.create_activity(activity)


@router.put("/activities/{activity_id}", response_model=Activity)
def update_activity(activity_id: int, activity_update: ActivityUpdate, db: Session = Depends(get_db)):
    """Update an activity."""
    service = ActivityService(db)
    activity = service.update_activity(activity_id, activity_update)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """Delete an activity."""
    service = ActivityService(db)
    if not service.delete_activity(activity_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )


# Lead Scoring Rule endpoints
@router.get("/scoring-rules/", response_model=List[LeadScoringRule])
def get_scoring_rules(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all scoring rules with optional filtering."""
    service = LeadScoringService(db)
    return service.get_scoring_rules(
        skip=skip, 
        limit=limit, 
        organization_id=organization_id, 
        rule_type=rule_type
    )


@router.get("/scoring-rules/{rule_id}", response_model=LeadScoringRule)
def get_scoring_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific scoring rule by ID."""
    service = LeadScoringService(db)
    rule = service.get_scoring_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found"
        )
    return rule


@router.post("/scoring-rules/", response_model=LeadScoringRule, status_code=status.HTTP_201_CREATED)
def create_scoring_rule(rule: LeadScoringRuleCreate, db: Session = Depends(get_db)):
    """Create a new scoring rule."""
    service = LeadScoringService(db)
    return service.create_scoring_rule(rule)


@router.put("/scoring-rules/{rule_id}", response_model=LeadScoringRule)
def update_scoring_rule(rule_id: int, rule_update: LeadScoringRuleUpdate, db: Session = Depends(get_db)):
    """Update a scoring rule."""
    service = LeadScoringService(db)
    rule = service.update_scoring_rule(rule_id, rule_update)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found"
        )
    return rule


@router.delete("/scoring-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scoring_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a scoring rule."""
    service = LeadScoringService(db)
    if not service.delete_scoring_rule(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found"
        )