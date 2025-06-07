"""
Sales management API endpoints for alerts, notifications, and workflow triggers.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Lead, User, ActivityLog
from schemas import APIResponse
from routers.auth import get_dev_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sales-alerts", tags=["sales-alerts"])


@router.post("/hot-lead", response_model=APIResponse)
async def notify_hot_lead(
    alert_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """
    Notify sales team about hot lead from n8n workflow.
    """
    try:
        lead_id = alert_data.get("lead_id")
        lead_name = alert_data.get("name", "Unknown Lead")
        lead_email = alert_data.get("email", "")
        company = alert_data.get("company", "")
        score = alert_data.get("score", 0)
        temperature = alert_data.get("temperature", "hot")
        score_breakdown = alert_data.get("score_breakdown", {})
        priority = alert_data.get("priority", "high")
        
        # Verify lead exists
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Log the hot lead alert activity
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type="hot_lead_alert",
            description=f"Hot lead alert triggered for {lead_name} (Score: {score})",
            activity_metadata={
                "alert_type": "hot_lead",
                "score": score,
                "temperature": temperature,
                "score_breakdown": score_breakdown,
                "priority": priority,
                "company": company,
                "email": lead_email,
                "triggered_by": "n8n_workflow",
                "alert_timestamp": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        # In a real implementation, you would:
        # 1. Send email notifications to sales team
        # 2. Create Slack/Teams notifications
        # 3. Update CRM systems
        # 4. Trigger additional workflows
        
        # For now, just log the alert
        logger.info(
            f"Hot lead alert processed: {lead_name} ({lead_email}) from {company} "
            f"with score {score} - Lead ID: {lead_id}"
        )
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "alert_type": "hot_lead",
                "score": score,
                "temperature": temperature,
                "processed_at": datetime.utcnow().isoformat(),
                "activity_log_id": activity_log.id
            },
            message=f"Hot lead alert processed for {lead_name}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process hot lead alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process hot lead alert: {str(e)}"
        )


@router.post("/warm-lead", response_model=APIResponse)
async def notify_warm_lead(
    alert_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """
    Notify sales team about warm lead from n8n workflow.
    """
    try:
        lead_id = alert_data.get("lead_id")
        lead_name = alert_data.get("name", "Unknown Lead")
        lead_email = alert_data.get("email", "")
        company = alert_data.get("company", "")
        score = alert_data.get("score", 0)
        temperature = alert_data.get("temperature", "warm")
        recommended_action = alert_data.get("recommended_action", "personalized_follow_up")
        
        # Verify lead exists
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Log the warm lead alert activity
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type="warm_lead_alert",
            description=f"Warm lead alert triggered for {lead_name} (Score: {score})",
            activity_metadata={
                "alert_type": "warm_lead",
                "score": score,
                "temperature": temperature,
                "recommended_action": recommended_action,
                "company": company,
                "email": lead_email,
                "triggered_by": "n8n_workflow",
                "alert_timestamp": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        logger.info(
            f"Warm lead alert processed: {lead_name} ({lead_email}) from {company} "
            f"with score {score} - Recommended action: {recommended_action}"
        )
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "alert_type": "warm_lead",
                "score": score,
                "temperature": temperature,
                "recommended_action": recommended_action,
                "processed_at": datetime.utcnow().isoformat(),
                "activity_log_id": activity_log.id
            },
            message=f"Warm lead alert processed for {lead_name}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process warm lead alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process warm lead alert: {str(e)}"
        )


@router.post("/score-change", response_model=APIResponse)
async def notify_score_change(
    alert_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """
    Notify about significant lead score changes from n8n workflow.
    """
    try:
        lead_id = alert_data.get("lead_id")
        lead_name = alert_data.get("name", "Unknown Lead")
        previous_score = alert_data.get("previous_score", 0)
        new_score = alert_data.get("new_score", 0)
        score_change = alert_data.get("score_change", 0)
        temperature = alert_data.get("temperature", "cold")
        
        # Verify lead exists
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Log the score change alert
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type="score_change_alert",
            description=f"Significant score change for {lead_name}: {previous_score} → {new_score} ({score_change:+d})",
            activity_metadata={
                "alert_type": "score_change",
                "previous_score": previous_score,
                "new_score": new_score,
                "score_change": score_change,
                "temperature": temperature,
                "triggered_by": "n8n_workflow",
                "alert_timestamp": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        logger.info(
            f"Score change alert processed: {lead_name} score changed from "
            f"{previous_score} to {new_score} ({score_change:+d})"
        )
        
        return APIResponse(
            success=True,
            data={
                "lead_id": lead_id,
                "alert_type": "score_change",
                "previous_score": previous_score,
                "new_score": new_score,
                "score_change": score_change,
                "temperature": temperature,
                "processed_at": datetime.utcnow().isoformat(),
                "activity_log_id": activity_log.id
            },
            message=f"Score change alert processed for {lead_name}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process score change alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process score change alert: {str(e)}"
        ) 