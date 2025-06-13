"""
Lead Management Domain Services.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .models import Lead, Activity, LeadScoringRule
from .schemas import LeadCreate, LeadUpdate, ActivityCreate, ActivityUpdate, LeadScoringRuleCreate, LeadScoringRuleUpdate


class LeadService:
    """Service for lead management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Lead]:
        """Get leads with optional filtering."""
        query = self.db.query(Lead)
        
        if organization_id:
            query = query.filter(Lead.organization_id == organization_id)
        
        if status:
            query = query.filter(Lead.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get a specific lead by ID."""
        return self.db.query(Lead).filter(Lead.id == lead_id).first()
    
    def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create a new lead."""
        db_lead = Lead(**lead_data.dict())
        self.db.add(db_lead)
        self.db.commit()
        self.db.refresh(db_lead)
        return db_lead
    
    def update_lead(self, lead_id: int, lead_data: LeadUpdate) -> Optional[Lead]:
        """Update a lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        
        update_data = lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return False
        
        self.db.delete(lead)
        self.db.commit()
        return True
    
    def calculate_lead_score(self, lead_id: int) -> float:
        """Calculate lead score based on scoring rules."""
        lead = self.get_lead(lead_id)
        if not lead:
            return 0.0
        
        # Get all applicable scoring rules
        rules = self.db.query(LeadScoringRule).filter(
            LeadScoringRule.organization_id == lead.organization_id,
            LeadScoringRule.is_active == True
        ).all()
        
        total_score = 0.0
        for rule in rules:
            # Apply rule logic here (simplified for now)
            if self._evaluate_rule(lead, rule):
                total_score += rule.score_value
        
        # Update lead score
        lead.score = total_score
        self.db.commit()
        
        return total_score
    
    def _evaluate_rule(self, lead: Lead, rule: LeadScoringRule) -> bool:
        """Evaluate if a scoring rule applies to a lead."""
        # Simplified rule evaluation - in production, this would be more sophisticated
        conditions = rule.conditions
        
        if rule.rule_type == "demographic":
            # Example: check company size, industry, etc.
            return True
        elif rule.rule_type == "behavioral":
            # Example: check website visits, email opens, etc.
            return True
        elif rule.rule_type == "engagement":
            # Example: check activity frequency, response rate, etc.
            return True
        
        return False


class ActivityService:
    """Service for activity management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_activities(
        self,
        skip: int = 0,
        limit: int = 100,
        lead_id: Optional[int] = None,
        user_id: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> List[Activity]:
        """Get activities with optional filtering."""
        query = self.db.query(Activity)
        
        if lead_id:
            query = query.filter(Activity.lead_id == lead_id)
        
        if user_id:
            query = query.filter(Activity.user_id == user_id)
        
        if activity_type:
            query = query.filter(Activity.type == activity_type)
        
        return query.offset(skip).limit(limit).all()
    
    def get_activity(self, activity_id: int) -> Optional[Activity]:
        """Get a specific activity by ID."""
        return self.db.query(Activity).filter(Activity.id == activity_id).first()
    
    def create_activity(self, activity_data: ActivityCreate) -> Activity:
        """Create a new activity."""
        db_activity = Activity(**activity_data.dict())
        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)
        return db_activity
    
    def update_activity(self, activity_id: int, activity_data: ActivityUpdate) -> Optional[Activity]:
        """Update an activity."""
        activity = self.get_activity(activity_id)
        if not activity:
            return None
        
        update_data = activity_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activity, field, value)
        
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity."""
        activity = self.get_activity(activity_id)
        if not activity:
            return False
        
        self.db.delete(activity)
        self.db.commit()
        return True


class LeadScoringService:
    """Service for lead scoring rule management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_scoring_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        rule_type: Optional[str] = None
    ) -> List[LeadScoringRule]:
        """Get scoring rules with optional filtering."""
        query = self.db.query(LeadScoringRule)
        
        if organization_id:
            query = query.filter(LeadScoringRule.organization_id == organization_id)
        
        if rule_type:
            query = query.filter(LeadScoringRule.rule_type == rule_type)
        
        return query.offset(skip).limit(limit).all()
    
    def get_scoring_rule(self, rule_id: int) -> Optional[LeadScoringRule]:
        """Get a specific scoring rule by ID."""
        return self.db.query(LeadScoringRule).filter(LeadScoringRule.id == rule_id).first()
    
    def create_scoring_rule(self, rule_data: LeadScoringRuleCreate) -> LeadScoringRule:
        """Create a new scoring rule."""
        db_rule = LeadScoringRule(**rule_data.dict())
        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)
        return db_rule
    
    def update_scoring_rule(self, rule_id: int, rule_data: LeadScoringRuleUpdate) -> Optional[LeadScoringRule]:
        """Update a scoring rule."""
        rule = self.get_scoring_rule(rule_id)
        if not rule:
            return None
        
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        self.db.commit()
        self.db.refresh(rule)
        return rule
    
    def delete_scoring_rule(self, rule_id: int) -> bool:
        """Delete a scoring rule."""
        rule = self.get_scoring_rule(rule_id)
        if not rule:
            return False
        
        self.db.delete(rule)
        self.db.commit()
        return True