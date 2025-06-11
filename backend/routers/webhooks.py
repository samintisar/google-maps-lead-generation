"""
Webhook Router

FastAPI router for handling webhook endpoints, real-time data updates,
and automation triggers. Provides secure webhook management with 
signature verification and event processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import hashlib
import hmac
import json
import secrets
import asyncio

from ..database import get_db
from ..auth import get_current_user, get_optional_user
from ..models import User
from ..automation import AutomationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Webhook registry for active webhooks
webhook_registry = {}
webhook_secrets = {}

class WebhookEvent:
    """Webhook event data structure"""
    def __init__(self, webhook_id: str, event_type: str, data: Dict[str, Any], source: str = None):
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.data = data
        self.source = source or "unknown"
        self.timestamp = datetime.utcnow()
        self.processed = False

class WebhookProcessor:
    """Process webhook events and trigger automation"""
    
    def __init__(self, automation_engine: AutomationEngine = None):
        self.automation_engine = automation_engine
        self.event_handlers = {}
        self.event_queue = []
        
    def register_handler(self, event_type: str, handler_script: str):
        """Register an automation script to handle specific webhook events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler_script)
        logger.info(f"Registered handler '{handler_script}' for event type '{event_type}'")
    
    async def process_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process a webhook event and trigger associated automations"""
        try:
            from ..automation.metrics import metrics_collector
            
            # Record webhook processing start
            metrics_collector.record_webhook_processing_start(
                event_type=event.event_type,
                webhook_id=event.webhook_id,
                source=event.source
            )
            
            logger.info(f"Processing webhook event: {event.event_type} from {event.source}")
            
            # Check if we have handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])
            if not handlers:
                logger.warning(f"No handlers registered for event type: {event.event_type}")
                metrics_collector.record_webhook_processing_end(
                    event_type=event.event_type,
                    webhook_id=event.webhook_id,
                    status="no_handlers"
                )
                return {"status": "no_handlers", "event_id": event.webhook_id}
            
            results = []
            
            # Execute all registered handlers
            for handler_script in handlers:
                try:
                    if self.automation_engine:
                        # Prepare context with webhook data
                        context = {
                            "webhook_event": {
                                "id": event.webhook_id,
                                "type": event.event_type,
                                "data": event.data,
                                "source": event.source,
                                "timestamp": event.timestamp.isoformat()
                            }
                        }
                        
                        # Execute the handler script
                        result = await self.automation_engine.execute_script(
                            script_name=handler_script,
                            context=context,
                            execution_id=f"webhook_{event.webhook_id}_{handler_script}"
                        )
                        
                        results.append({
                            "handler": handler_script,
                            "status": result.status.value,
                            "execution_id": result.execution_id,
                            "error": result.error_message
                        })
                        
                    else:
                        logger.warning("No automation engine available for handler execution")
                        
                except Exception as e:
                    logger.error(f"Error executing webhook handler {handler_script}: {e}")
                    results.append({
                        "handler": handler_script,
                        "status": "failed",
                        "error": str(e)
                    })
            
            event.processed = True
            
            # Record successful processing
            metrics_collector.record_webhook_processing_end(
                event_type=event.event_type,
                webhook_id=event.webhook_id,
                status="processed"
            )
            
            return {
                "status": "processed",
                "event_id": event.webhook_id,
                "handlers_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook event {event.webhook_id}: {e}")
            
            # Record failed processing
            try:
                from ..automation.metrics import metrics_collector
                metrics_collector.record_webhook_processing_end(
                    event_type=event.event_type,
                    webhook_id=event.webhook_id,
                    status="failed",
                    error_type=type(e).__name__
                )
            except:
                pass  # Don't let metrics failure break webhook processing
            
            return {
                "status": "error",
                "event_id": event.webhook_id,
                "error": str(e)
            }

# Global webhook processor instance
webhook_processor = None

def get_webhook_processor() -> WebhookProcessor:
    """Get webhook processor instance"""
    global webhook_processor
    if webhook_processor is None:
        raise HTTPException(status_code=500, detail="Webhook processor not initialized")
    return webhook_processor

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    if not secret or not signature:
        return False
    
    # Support different signature formats
    if signature.startswith('sha256='):
        signature = signature[7:]
    elif signature.startswith('sha1='):
        signature = signature[5:]
    
    # Calculate expected signature
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

@router.post("/register")
async def register_webhook(
    webhook_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new webhook endpoint"""
    try:
        webhook_id = webhook_config.get('id') or f"webhook_{secrets.token_hex(8)}"
        event_types = webhook_config.get('event_types', [])
        auto_scripts = webhook_config.get('automation_scripts', [])
        description = webhook_config.get('description', '')
        
        # Generate webhook secret
        webhook_secret = secrets.token_urlsafe(32)
        
        # Store webhook configuration
        webhook_registry[webhook_id] = {
            'id': webhook_id,
            'user_id': current_user.id,
            'event_types': event_types,
            'automation_scripts': auto_scripts,
            'description': description,
            'created_at': datetime.utcnow(),
            'active': True
        }
        
        webhook_secrets[webhook_id] = webhook_secret
        
        # Register automation handlers
        processor = get_webhook_processor()
        for event_type in event_types:
            for script in auto_scripts:
                processor.register_handler(event_type, script)
        
        logger.info(f"Registered webhook {webhook_id} for user {current_user.id}")
        
        return {
            "webhook_id": webhook_id,
            "secret": webhook_secret,
            "endpoint_url": f"/api/webhooks/{webhook_id}",
            "event_types": event_types,
            "automation_scripts": auto_scripts
        }
        
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to register webhook")

@router.get("/list")
async def list_webhooks(
    current_user: User = Depends(get_current_user)
):
    """List user's registered webhooks"""
    user_webhooks = [
        {
            "id": webhook['id'],
            "event_types": webhook['event_types'],
            "automation_scripts": webhook['automation_scripts'],
            "description": webhook['description'],
            "created_at": webhook['created_at'],
            "active": webhook['active']
        }
        for webhook in webhook_registry.values()
        if webhook['user_id'] == current_user.id
    ]
    
    return {"webhooks": user_webhooks, "count": len(user_webhooks)}

@router.post("/{webhook_id}")
async def receive_webhook(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_event_type: Optional[str] = Header(None, alias="X-Event-Type"),
    processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Receive and process webhook data"""
    try:
        # Check if webhook exists
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        webhook_config = webhook_registry[webhook_id]
        if not webhook_config['active']:
            raise HTTPException(status_code=410, detail="Webhook is inactive")
        
        # Get request body
        body = await request.body()
        
        # Verify signature if secret exists
        webhook_secret = webhook_secrets.get(webhook_id)
        if webhook_secret and x_signature:
            if not verify_webhook_signature(body, x_signature, webhook_secret):
                logger.warning(f"Invalid signature for webhook {webhook_id}")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON payload
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw_data": body.decode('utf-8', errors='ignore')}
        
        # Determine event type
        event_type = x_event_type or payload.get('event_type', 'generic')
        
        # Create webhook event
        event = WebhookEvent(
            webhook_id=f"{webhook_id}_{datetime.utcnow().timestamp()}",
            event_type=event_type,
            data=payload,
            source=f"webhook_{webhook_id}"
        )
        
        # Process event in background
        background_tasks.add_task(processor.process_event, event)
        
        logger.info(f"Received webhook {webhook_id} with event type {event_type}")
        
        return {
            "status": "received",
            "webhook_id": webhook_id,
            "event_type": event_type,
            "timestamp": event.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook"""
    if webhook_id not in webhook_registry:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = webhook_registry[webhook_id]
    if webhook['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this webhook")
    
    # Remove webhook
    del webhook_registry[webhook_id]
    if webhook_id in webhook_secrets:
        del webhook_secrets[webhook_id]
    
    logger.info(f"Deleted webhook {webhook_id}")
    
    return {"message": "Webhook deleted", "webhook_id": webhook_id}

@router.post("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle webhook active status"""
    if webhook_id not in webhook_registry:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = webhook_registry[webhook_id]
    if webhook['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this webhook")
    
    webhook['active'] = not webhook['active']
    
    return {
        "webhook_id": webhook_id,
        "active": webhook['active'],
        "status": "activated" if webhook['active'] else "deactivated"
    }

@router.get("/{webhook_id}/events")
async def get_webhook_events(
    webhook_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Get recent events for a webhook"""
    if webhook_id not in webhook_registry:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = webhook_registry[webhook_id]
    if webhook['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this webhook")
    
    # Filter events for this webhook
    webhook_events = [
        {
            "event_id": event.webhook_id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp,
            "processed": event.processed,
            "data_size": len(json.dumps(event.data)) if event.data else 0
        }
        for event in processor.event_queue[-limit:]
        if event.source == f"webhook_{webhook_id}"
    ]
    
    return {"events": webhook_events, "count": len(webhook_events)}

async def init_webhook_system(automation_engine: AutomationEngine = None):
    """Initialize the webhook system"""
    global webhook_processor
    webhook_processor = WebhookProcessor(automation_engine)
    logger.info("Webhook system initialized")
    
    # Register webhook automation scripts with the automation engine
    if automation_engine:
        from ..automation.webhook_scripts import register_webhook_scripts
        register_webhook_scripts(automation_engine)
    
    # Register some default event handlers
    default_handlers = {
        "lead_created": ["lead_scoring", "lead_enrichment"],
        "lead_updated": ["lead_scoring"],
        "user_registered": ["send_welcome_email"],
        "form_submitted": ["lead_creation", "notification_send"]
    }
    
    for event_type, handlers in default_handlers.items():
        for handler in handlers:
            try:
                webhook_processor.register_handler(event_type, handler)
            except Exception as e:
                logger.warning(f"Could not register default handler {handler} for {event_type}: {e}")

# Test webhook endpoint for development
@router.post("/test")
async def test_webhook(
    test_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    processor: WebhookProcessor = Depends(get_webhook_processor)
):
    """Test webhook endpoint for development and testing"""
    event = WebhookEvent(
        webhook_id=f"test_{datetime.utcnow().timestamp()}",
        event_type=test_data.get('event_type', 'test'),
        data=test_data,
        source="test_endpoint"
    )
    
    # Process immediately for testing
    result = await processor.process_event(event)
    
    return {
        "test_result": result,
        "test_data": test_data,
        "timestamp": event.timestamp
    } 