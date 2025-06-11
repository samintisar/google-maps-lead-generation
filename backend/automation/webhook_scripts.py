"""
Webhook Automation Scripts

Sample automation scripts that are triggered by webhook events.
These scripts demonstrate how to process webhook data and integrate
with the automation system.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

async def lead_scoring_webhook(db_session, redis, context, execution_id, logger, **kwargs):
    """
    Webhook handler for lead scoring when leads are created or updated
    """
    try:
        webhook_event = context.get('webhook_event', {})
        event_data = webhook_event.get('data', {})
        
        logger.info(f"Processing lead scoring webhook: {execution_id}")
        
        # Extract lead data from webhook
        lead_id = event_data.get('lead_id')
        lead_data = event_data.get('lead_data', {})
        
        if not lead_id:
            return {"error": "No lead_id provided in webhook data"}
        
        # Calculate lead score based on webhook data
        score = 0
        
        # Score based on company size
        company_size = lead_data.get('company_size', '').lower()
        if 'enterprise' in company_size or 'large' in company_size:
            score += 40
        elif 'medium' in company_size or 'mid' in company_size:
            score += 25
        elif 'small' in company_size:
            score += 10
        
        # Score based on industry
        industry = lead_data.get('industry', '').lower()
        high_value_industries = ['technology', 'finance', 'healthcare', 'saas']
        if any(ind in industry for ind in high_value_industries):
            score += 30
        
        # Score based on email domain
        email = lead_data.get('email', '')
        if email:
            domain = email.split('@')[-1].lower()
            corporate_indicators = ['.com', '.org', '.gov', '.edu']
            if any(domain.endswith(ind) for ind in corporate_indicators) and 'gmail' not in domain and 'yahoo' not in domain:
                score += 20
        
        # Score based on website
        if lead_data.get('website'):
            score += 15
        
        # Score based on phone number
        if lead_data.get('phone'):
            score += 10
        
        # Update lead score in database
        from ..models import Lead
        lead = db_session.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.score = min(score, 100)  # Cap at 100
            lead.last_activity = datetime.utcnow()
            db_session.commit()
            
            logger.info(f"Updated lead {lead_id} score to {score}")
            
            return {
                "lead_id": lead_id,
                "new_score": score,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"error": f"Lead {lead_id} not found in database"}
            
    except Exception as e:
        logger.error(f"Error in lead scoring webhook: {e}")
        return {"error": str(e), "status": "failed"}

async def lead_enrichment_webhook(db_session, redis, context, execution_id, logger, **kwargs):
    """
    Webhook handler for lead enrichment
    """
    try:
        webhook_event = context.get('webhook_event', {})
        event_data = webhook_event.get('data', {})
        
        logger.info(f"Processing lead enrichment webhook: {execution_id}")
        
        lead_id = event_data.get('lead_id')
        lead_data = event_data.get('lead_data', {})
        
        if not lead_id:
            return {"error": "No lead_id provided in webhook data"}
        
        # Enrich lead data
        enriched_data = {}
        
        # Extract company domain from email
        email = lead_data.get('email', '')
        if email and '@' in email:
            domain = email.split('@')[-1]
            enriched_data['company_domain'] = domain
        
        # Normalize phone number
        phone = lead_data.get('phone', '')
        if phone:
            # Remove non-numeric characters
            normalized_phone = ''.join(filter(str.isdigit, phone))
            if len(normalized_phone) == 10:
                normalized_phone = f"({normalized_phone[:3]}) {normalized_phone[3:6]}-{normalized_phone[6:]}"
            enriched_data['normalized_phone'] = normalized_phone
        
        # Determine timezone based on phone area code (US only)
        if phone and len(phone) >= 3:
            area_code = ''.join(filter(str.isdigit, phone))[:3]
            timezone_map = {
                '212': 'Eastern', '646': 'Eastern', '718': 'Eastern',  # NYC
                '415': 'Pacific', '510': 'Pacific', '650': 'Pacific',  # SF Bay Area
                '310': 'Pacific', '213': 'Pacific', '424': 'Pacific',  # LA
                '312': 'Central', '773': 'Central', '872': 'Central',  # Chicago
            }
            if area_code in timezone_map:
                enriched_data['timezone'] = timezone_map[area_code]
        
        # Update lead with enriched data
        from ..models import Lead
        lead = db_session.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            # Update lead fields with enriched data
            for key, value in enriched_data.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            
            lead.last_activity = datetime.utcnow()
            db_session.commit()
            
            logger.info(f"Enriched lead {lead_id} with data: {enriched_data}")
            
            return {
                "lead_id": lead_id,
                "enriched_data": enriched_data,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"error": f"Lead {lead_id} not found in database"}
            
    except Exception as e:
        logger.error(f"Error in lead enrichment webhook: {e}")
        return {"error": str(e), "status": "failed"}

async def send_welcome_email_webhook(db_session, redis, context, execution_id, logger, **kwargs):
    """
    Webhook handler for sending welcome emails to new users
    """
    try:
        webhook_event = context.get('webhook_event', {})
        event_data = webhook_event.get('data', {})
        
        logger.info(f"Processing welcome email webhook: {execution_id}")
        
        user_id = event_data.get('user_id')
        user_data = event_data.get('user_data', {})
        
        if not user_id:
            return {"error": "No user_id provided in webhook data"}
        
        # Simulate sending welcome email
        email = user_data.get('email')
        first_name = user_data.get('first_name', 'there')
        
        if not email:
            return {"error": "No email provided for user"}
        
        # In a real implementation, this would integrate with an email service
        email_content = {
            "to": email,
            "subject": f"Welcome to LMA Platform, {first_name}!",
            "body": f"""
            Hi {first_name},
            
            Welcome to the Lead Management Automation Platform! 
            We're excited to have you on board.
            
            Your account has been successfully created and you can 
            start managing your leads right away.
            
            Best regards,
            The LMA Team
            """,
            "template": "welcome_email",
            "user_id": user_id
        }
        
        # Store email in Redis for processing queue (if Redis is available)
        if redis:
            email_key = f"email_queue:{execution_id}"
            redis.setex(email_key, 3600, json.dumps(email_content))  # Store for 1 hour
        
        logger.info(f"Queued welcome email for user {user_id} ({email})")
        
        return {
            "user_id": user_id,
            "email": email,
            "email_queued": True,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in welcome email webhook: {e}")
        return {"error": str(e), "status": "failed"}

async def lead_creation_webhook(db_session, redis, context, execution_id, logger, **kwargs):
    """
    Webhook handler for creating leads from form submissions
    """
    try:
        webhook_event = context.get('webhook_event', {})
        event_data = webhook_event.get('data', {})
        
        logger.info(f"Processing lead creation webhook: {execution_id}")
        
        # Extract form data
        form_data = event_data.get('form_data', {})
        source = event_data.get('source', 'webhook')
        
        required_fields = ['email']
        if not all(field in form_data for field in required_fields):
            return {"error": f"Missing required fields: {required_fields}"}
        
        # Create new lead
        from ..models import Lead
        
        new_lead = Lead(
            email=form_data.get('email'),
            first_name=form_data.get('first_name', ''),
            last_name=form_data.get('last_name', ''),
            company=form_data.get('company', ''),
            phone=form_data.get('phone', ''),
            source=source,
            status='new',
            score=0,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        db_session.add(new_lead)
        db_session.commit()
        db_session.refresh(new_lead)
        
        logger.info(f"Created new lead {new_lead.id} from webhook")
        
        return {
            "lead_id": new_lead.id,
            "email": new_lead.email,
            "source": source,
            "status": "created",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in lead creation webhook: {e}")
        db_session.rollback()
        return {"error": str(e), "status": "failed"}

async def notification_send_webhook(db_session, redis, context, execution_id, logger, **kwargs):
    """
    Webhook handler for sending notifications
    """
    try:
        webhook_event = context.get('webhook_event', {})
        event_data = webhook_event.get('data', {})
        
        logger.info(f"Processing notification webhook: {execution_id}")
        
        notification_type = event_data.get('type', 'general')
        message = event_data.get('message', '')
        recipients = event_data.get('recipients', [])
        
        if not message:
            return {"error": "No message provided for notification"}
        
        if not recipients:
            return {"error": "No recipients provided for notification"}
        
        # Process notifications
        notifications_sent = []
        
        for recipient in recipients:
            notification = {
                "recipient": recipient,
                "type": notification_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_id": execution_id
            }
            
            # Store notification (in a real system, this would go to a notification service)
            if redis:
                notification_key = f"notification:{recipient}:{execution_id}"
                redis.setex(notification_key, 86400, json.dumps(notification))  # Store for 24 hours
            
            notifications_sent.append(notification)
        
        logger.info(f"Sent {len(notifications_sent)} notifications via webhook")
        
        return {
            "notifications_sent": len(notifications_sent),
            "recipients": recipients,
            "type": notification_type,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in notification webhook: {e}")
        return {"error": str(e), "status": "failed"}

# Register these scripts with the automation engine
def register_webhook_scripts(automation_engine):
    """Register webhook automation scripts with the automation engine"""
    scripts = {
        "lead_scoring": lead_scoring_webhook,
        "lead_enrichment": lead_enrichment_webhook,
        "send_welcome_email": send_welcome_email_webhook,
        "lead_creation": lead_creation_webhook,
        "notification_send": notification_send_webhook,
    }
    
    for script_name, script_func in scripts.items():
        automation_engine.register_script(
            name=script_name,
            script_func=script_func,
            metadata={
                "category": "webhook",
                "description": f"Webhook automation script for {script_name.replace('_', ' ')}",
                "trigger": "webhook_event",
                "created_by": "webhook_system"
            }
        )
    
    logger.info(f"Registered {len(scripts)} webhook automation scripts") 