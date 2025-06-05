"""
Lead Scoring Service - Comprehensive lead scoring and enrichment system.
Implements rule-based scoring, score tracking, and automated enrichment.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models import (
    Lead, LeadScoringRule, LeadScoreHistory, Organization, 
    LeadStatus, LeadSource, LeadTemperature, Communication, 
    ActivityLog, User
)

logger = logging.getLogger(__name__)

class LeadScoringService:
    """
    Comprehensive lead scoring service for automated lead qualification.
    """
    
    def __init__(self, db: Session):
        """Initialize the lead scoring service."""
        self.db = db
        
        # Default scoring rules that can be applied to any organization
        self.default_scoring_rules = {
            # Demographic scoring
            "has_company": {"points": 10, "description": "Lead has company information"},
            "has_job_title": {"points": 8, "description": "Lead has job title"},
            "has_phone": {"points": 5, "description": "Lead has phone number"},
            "has_linkedin": {"points": 5, "description": "Lead has LinkedIn profile"},
            
            # Engagement scoring
            "email_opened": {"points": 2, "description": "Email was opened"},
            "email_clicked": {"points": 5, "description": "Email link was clicked"},
            "website_visit": {"points": 3, "description": "Visited website"},
            "form_submission": {"points": 15, "description": "Submitted a form"},
            "demo_request": {"points": 25, "description": "Requested a demo"},
            
            # Behavioral scoring
            "recent_activity": {"points": 10, "description": "Active in last 7 days"},
            "multiple_interactions": {"points": 8, "description": "Multiple interactions"},
            "inbound_contact": {"points": 12, "description": "Initiated contact"},
            
            # Source-based scoring
            "referral_source": {"points": 20, "description": "Came from referral"},
            "social_media_source": {"points": 8, "description": "Came from social media"},
            "paid_advertising": {"points": 12, "description": "Came from paid advertising"},
            
            # Temperature adjustments
            "hot_temperature": {"points": 15, "description": "Marked as hot lead"},
            "warm_temperature": {"points": 8, "description": "Marked as warm lead"},
            "cold_temperature": {"points": 0, "description": "Cold lead (no bonus)"},
        }
    
    async def calculate_lead_score(self, lead_id: int) -> Dict[str, Any]:
        """
        Calculate comprehensive score for a lead based on all applicable rules.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Get organization-specific scoring rules
            org_rules = self.db.query(LeadScoringRule).filter(
                and_(
                    LeadScoringRule.organization_id == lead.organization_id,
                    LeadScoringRule.is_active == True
                )
            ).order_by(LeadScoringRule.priority.desc()).all()
            
            score_breakdown = {
                "lead_id": lead_id,
                "previous_score": lead.score,
                "calculated_score": 0,
                "max_possible_score": 100,
                "scoring_details": [],
                "applied_rules": [],
                "demographic_score": 0,
                "engagement_score": 0,
                "behavioral_score": 0,
                "source_score": 0,
                "temperature_score": 0
            }
            
            # Apply demographic scoring
            demo_score = self._calculate_demographic_score(lead)
            score_breakdown["demographic_score"] = demo_score["total"]
            score_breakdown["scoring_details"].extend(demo_score["details"])
            
            # Apply engagement scoring
            engagement_score = await self._calculate_engagement_score(lead)
            score_breakdown["engagement_score"] = engagement_score["total"]
            score_breakdown["scoring_details"].extend(engagement_score["details"])
            
            # Apply behavioral scoring
            behavioral_score = await self._calculate_behavioral_score(lead)
            score_breakdown["behavioral_score"] = behavioral_score["total"]
            score_breakdown["scoring_details"].extend(behavioral_score["details"])
            
            # Apply source-based scoring
            source_score = self._calculate_source_score(lead)
            score_breakdown["source_score"] = source_score["total"]
            score_breakdown["scoring_details"].extend(source_score["details"])
            
            # Apply temperature scoring
            temp_score = self._calculate_temperature_score(lead)
            score_breakdown["temperature_score"] = temp_score["total"]
            score_breakdown["scoring_details"].extend(temp_score["details"])
            
            # Apply organization-specific rules
            org_score = await self._apply_organization_rules(lead, org_rules)
            score_breakdown["applied_rules"] = org_score["applied_rules"]
            
            # Calculate total score
            total_score = (
                demo_score["total"] + 
                engagement_score["total"] + 
                behavioral_score["total"] + 
                source_score["total"] + 
                temp_score["total"] + 
                org_score["total"]
            )
            
            # Cap the score at 100
            final_score = min(total_score, 100)
            score_breakdown["calculated_score"] = final_score
            score_breakdown["score_change"] = final_score - lead.score
            
            return score_breakdown
            
        except Exception as e:
            logger.error(f"Failed to calculate score for lead {lead_id}: {e}")
            raise
    
    async def update_lead_score(self, lead_id: int, reason: str = "Automated scoring") -> Dict[str, Any]:
        """
        Calculate and update a lead's score, tracking the change in history.
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Calculate new score
            score_result = await self.calculate_lead_score(lead_id)
            
            previous_score = lead.score
            new_score = score_result["calculated_score"]
            score_change = new_score - previous_score
            
            # Update lead score
            lead.score = new_score
            lead.updated_at = datetime.utcnow()
            
            # Create score history entry
            score_history = LeadScoreHistory(
                lead_id=lead_id,
                previous_score=previous_score,
                new_score=new_score,
                score_change=score_change,
                reason=reason,
                created_at=datetime.utcnow()
            )
            
            self.db.add(score_history)
            self.db.commit()
            
            # Log the activity
            activity_log = ActivityLog(
                lead_id=lead_id,
                activity_type="score_updated",
                description=f"Lead score updated from {previous_score} to {new_score} ({score_change:+d})",
                activity_metadata={
                    "previous_score": previous_score,
                    "new_score": new_score,
                    "score_change": score_change,
                    "reason": reason,
                    "score_breakdown": score_result["scoring_details"]
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(activity_log)
            self.db.commit()
            
            # Update lead temperature based on score
            await self._update_lead_temperature_from_score(lead_id, new_score)
            
            logger.info(f"Updated score for lead {lead_id}: {previous_score} -> {new_score} ({score_change:+d})")
            
            return {
                "lead_id": lead_id,
                "previous_score": previous_score,
                "new_score": new_score,
                "score_change": score_change,
                "score_breakdown": score_result,
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update score for lead {lead_id}: {e}")
            raise
    
    async def bulk_update_scores(self, organization_id: int, lead_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Update scores for multiple leads in an organization.
        """
        try:
            if lead_ids:
                leads = self.db.query(Lead).filter(
                    and_(
                        Lead.organization_id == organization_id,
                        Lead.id.in_(lead_ids)
                    )
                ).all()
            else:
                leads = self.db.query(Lead).filter(
                    Lead.organization_id == organization_id
                ).all()
            
            results = {
                "organization_id": organization_id,
                "total_leads": len(leads),
                "updated_leads": [],
                "failed_leads": [],
                "summary": {
                    "successful_updates": 0,
                    "failed_updates": 0,
                    "total_score_changes": 0
                }
            }
            
            for lead in leads:
                try:
                    update_result = await self.update_lead_score(
                        lead.id, 
                        reason="Bulk score update"
                    )
                    results["updated_leads"].append(update_result)
                    results["summary"]["successful_updates"] += 1
                    results["summary"]["total_score_changes"] += abs(update_result["score_change"])
                    
                except Exception as e:
                    results["failed_leads"].append({
                        "lead_id": lead.id,
                        "error": str(e)
                    })
                    results["summary"]["failed_updates"] += 1
                    logger.error(f"Failed to update score for lead {lead.id} in bulk update: {e}")
            
            logger.info(f"Bulk score update completed for organization {organization_id}: "
                       f"{results['summary']['successful_updates']} successful, "
                       f"{results['summary']['failed_updates']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed bulk score update for organization {organization_id}: {e}")
            raise
    
    def _calculate_demographic_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on demographic information."""
        score = 0
        details = []
        
        if lead.company:
            points = self.default_scoring_rules["has_company"]["points"]
            score += points
            details.append({
                "rule": "has_company",
                "points": points,
                "description": self.default_scoring_rules["has_company"]["description"]
            })
        
        if lead.job_title:
            points = self.default_scoring_rules["has_job_title"]["points"]
            score += points
            details.append({
                "rule": "has_job_title",
                "points": points,
                "description": self.default_scoring_rules["has_job_title"]["description"]
            })
        
        if lead.phone:
            points = self.default_scoring_rules["has_phone"]["points"]
            score += points
            details.append({
                "rule": "has_phone",
                "points": points,
                "description": self.default_scoring_rules["has_phone"]["description"]
            })
        
        if lead.linkedin_url:
            points = self.default_scoring_rules["has_linkedin"]["points"]
            score += points
            details.append({
                "rule": "has_linkedin",
                "points": points,
                "description": self.default_scoring_rules["has_linkedin"]["description"]
            })
        
        return {"total": score, "details": details}
    
    async def _calculate_engagement_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on engagement activities."""
        score = 0
        details = []
        
        # Get recent communications
        recent_comms = self.db.query(Communication).filter(
            and_(
                Communication.lead_id == lead.id,
                Communication.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        # Count different types of engagement
        email_opens = len([c for c in recent_comms if c.communication_type.value == 'email' and 
                          c.comm_metadata.get('opened', False)])
        email_clicks = len([c for c in recent_comms if c.communication_type.value == 'email' and 
                           c.comm_metadata.get('clicked', False)])
        
        # Score email engagement
        if email_opens > 0:
            points = min(email_opens * self.default_scoring_rules["email_opened"]["points"], 10)
            score += points
            details.append({
                "rule": "email_opened",
                "points": points,
                "description": f"Opened {email_opens} emails",
                "count": email_opens
            })
        
        if email_clicks > 0:
            points = min(email_clicks * self.default_scoring_rules["email_clicked"]["points"], 15)
            score += points
            details.append({
                "rule": "email_clicked",
                "points": points,
                "description": f"Clicked {email_clicks} email links",
                "count": email_clicks
            })
        
        return {"total": score, "details": details}
    
    async def _calculate_behavioral_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on behavioral patterns."""
        score = 0
        details = []
        
        # Check recent activity
        recent_activity = self.db.query(ActivityLog).filter(
            and_(
                ActivityLog.lead_id == lead.id,
                ActivityLog.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).count()
        
        if recent_activity > 0:
            points = self.default_scoring_rules["recent_activity"]["points"]
            score += points
            details.append({
                "rule": "recent_activity",
                "points": points,
                "description": f"Active in last 7 days ({recent_activity} activities)"
            })
        
        # Check for multiple interactions
        total_communications = self.db.query(Communication).filter(
            Communication.lead_id == lead.id
        ).count()
        
        if total_communications >= 3:
            points = self.default_scoring_rules["multiple_interactions"]["points"]
            score += points
            details.append({
                "rule": "multiple_interactions",
                "points": points,
                "description": f"Multiple interactions ({total_communications} total)"
            })
        
        # Check for inbound contact
        inbound_comms = self.db.query(Communication).filter(
            and_(
                Communication.lead_id == lead.id,
                Communication.direction.has_value('inbound')
            )
        ).count()
        
        if inbound_comms > 0:
            points = self.default_scoring_rules["inbound_contact"]["points"]
            score += points
            details.append({
                "rule": "inbound_contact",
                "points": points,
                "description": f"Initiated contact ({inbound_comms} inbound communications)"
            })
        
        return {"total": score, "details": details}
    
    def _calculate_source_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on lead source."""
        score = 0
        details = []
        
        if lead.source == LeadSource.REFERRAL:
            points = self.default_scoring_rules["referral_source"]["points"]
            score += points
            details.append({
                "rule": "referral_source",
                "points": points,
                "description": self.default_scoring_rules["referral_source"]["description"]
            })
        elif lead.source == LeadSource.SOCIAL_MEDIA:
            points = self.default_scoring_rules["social_media_source"]["points"]
            score += points
            details.append({
                "rule": "social_media_source",
                "points": points,
                "description": self.default_scoring_rules["social_media_source"]["description"]
            })
        elif lead.source == LeadSource.ADVERTISING:
            points = self.default_scoring_rules["paid_advertising"]["points"]
            score += points
            details.append({
                "rule": "paid_advertising",
                "points": points,
                "description": self.default_scoring_rules["paid_advertising"]["description"]
            })
        
        return {"total": score, "details": details}
    
    def _calculate_temperature_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on lead temperature."""
        score = 0
        details = []
        
        if lead.lead_temperature == LeadTemperature.HOT:
            points = self.default_scoring_rules["hot_temperature"]["points"]
            score += points
            details.append({
                "rule": "hot_temperature",
                "points": points,
                "description": self.default_scoring_rules["hot_temperature"]["description"]
            })
        elif lead.lead_temperature == LeadTemperature.WARM:
            points = self.default_scoring_rules["warm_temperature"]["points"]
            score += points
            details.append({
                "rule": "warm_temperature",
                "points": points,
                "description": self.default_scoring_rules["warm_temperature"]["description"]
            })
        
        return {"total": score, "details": details}
    
    async def _apply_organization_rules(self, lead: Lead, rules: List[LeadScoringRule]) -> Dict[str, Any]:
        """Apply organization-specific scoring rules."""
        total_score = 0
        applied_rules = []
        
        for rule in rules:
            try:
                if self._evaluate_rule_criteria(lead, rule.criteria):
                    total_score += rule.score_points
                    applied_rules.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type,
                        "points": rule.score_points,
                        "description": rule.description
                    })
                    
                    logger.debug(f"Applied rule {rule.name} (+{rule.score_points}) to lead {lead.id}")
                    
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id} for lead {lead.id}: {e}")
                continue
        
        return {"total": total_score, "applied_rules": applied_rules}
    
    def _evaluate_rule_criteria(self, lead: Lead, criteria: Dict[str, Any]) -> bool:
        """Evaluate if a lead matches the rule criteria."""
        # This is a simplified implementation - you can extend this
        # to support complex criteria evaluation
        
        for field, condition in criteria.items():
            if field == "company":
                if condition.get("required") and not lead.company:
                    return False
                if condition.get("contains") and lead.company:
                    if condition["contains"].lower() not in lead.company.lower():
                        return False
            
            elif field == "job_title":
                if condition.get("required") and not lead.job_title:
                    return False
                if condition.get("contains") and lead.job_title:
                    if condition["contains"].lower() not in lead.job_title.lower():
                        return False
            
            elif field == "source":
                if condition.get("equals") and lead.source.value != condition["equals"]:
                    return False
            
            elif field == "status":
                if condition.get("equals") and lead.status.value != condition["equals"]:
                    return False
        
        return True
    
    async def _update_lead_temperature_from_score(self, lead_id: int, score: int) -> None:
        """Update lead temperature based on score thresholds."""
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return
            
            old_temperature = lead.lead_temperature
            new_temperature = None
            
            # Define temperature thresholds
            if score >= 70:
                new_temperature = LeadTemperature.HOT
            elif score >= 40:
                new_temperature = LeadTemperature.WARM
            else:
                new_temperature = LeadTemperature.COLD
            
            if new_temperature != old_temperature:
                lead.lead_temperature = new_temperature
                self.db.commit()
                
                # Log the temperature change
                activity_log = ActivityLog(
                    lead_id=lead_id,
                    activity_type="temperature_updated",
                    description=f"Lead temperature changed from {old_temperature.value if old_temperature else 'none'} to {new_temperature.value} based on score {score}",
                    activity_metadata={
                        "old_temperature": old_temperature.value if old_temperature else None,
                        "new_temperature": new_temperature.value,
                        "score": score,
                        "trigger": "automatic_scoring"
                    },
                    created_at=datetime.utcnow()
                )
                
                self.db.add(activity_log)
                self.db.commit()
                
                logger.info(f"Updated temperature for lead {lead_id}: {old_temperature} -> {new_temperature} (score: {score})")
                
        except Exception as e:
            logger.error(f"Failed to update temperature for lead {lead_id}: {e}")
    
    async def get_lead_score_history(self, lead_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the score history for a lead."""
        try:
            history = self.db.query(LeadScoreHistory).filter(
                LeadScoreHistory.lead_id == lead_id
            ).order_by(desc(LeadScoreHistory.created_at)).limit(limit).all()
            
            return [
                {
                    "id": h.id,
                    "previous_score": h.previous_score,
                    "new_score": h.new_score,
                    "score_change": h.score_change,
                    "reason": h.reason,
                    "rule_id": h.rule_id,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]
            
        except Exception as e:
            logger.error(f"Failed to get score history for lead {lead_id}: {e}")
            raise
    
    async def get_scoring_analytics(self, organization_id: int, days_back: int = 30) -> Dict[str, Any]:
        """Get scoring analytics for an organization."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get leads with scores
            leads = self.db.query(Lead).filter(
                Lead.organization_id == organization_id
            ).all()
            
            if not leads:
                return {
                    "organization_id": organization_id,
                    "total_leads": 0,
                    "analytics": {}
                }
            
            scores = [lead.score for lead in leads]
            
            # Calculate score distribution
            score_ranges = {
                "hot_leads": len([s for s in scores if s >= 70]),
                "warm_leads": len([s for s in scores if 40 <= s < 70]),
                "cold_leads": len([s for s in scores if s < 40])
            }
            
            # Get recent score changes
            recent_changes = self.db.query(LeadScoreHistory).join(Lead).filter(
                and_(
                    Lead.organization_id == organization_id,
                    LeadScoreHistory.created_at >= start_date
                )
            ).all()
            
            return {
                "organization_id": organization_id,
                "total_leads": len(leads),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "score_distribution": score_ranges,
                "recent_score_changes": len(recent_changes),
                "analytics_period_days": days_back,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get scoring analytics for organization {organization_id}: {e}")
            raise 