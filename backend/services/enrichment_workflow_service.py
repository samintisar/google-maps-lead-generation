"""
Lead Enrichment Workflow Service

This service implements the lead enrichment workflow based on the N8N template.
It handles HubSpot integration, AI-powered data enrichment, and result validation.
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from cryptography.fernet import Fernet
import openai
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models import (
    WorkflowCredentials, WorkflowExecution, WorkflowLog, 
    EnrichedLeadData, Lead, User
)
from schemas import (
    WorkflowExecutionCreate, WorkflowLogCreate, EnrichedLeadDataCreate,
    WorkflowServiceCredentials, WorkflowRunRequest
)
from database import get_db
from config import settings

logger = logging.getLogger(__name__)

class EnrichmentWorkflowService:
    def __init__(self, db: Session):
        self.db = db
        # Generate a key for encryption if not in settings
        encryption_key = getattr(settings, 'encryption_key', None)
        if not encryption_key:
            encryption_key = Fernet.generate_key()
        self.cipher = Fernet(encryption_key if isinstance(encryption_key, bytes) else encryption_key.encode())
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt credentials for secure storage."""
        credentials_json = json.dumps(credentials)
        encrypted = self.cipher.encrypt(credentials_json.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_credentials: str) -> dict:
        """Decrypt stored credentials."""
        try:
            decrypted = self.cipher.decrypt(encrypted_credentials.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return {}
    
    async def save_credentials(self, user_id: int, service_name: str, credentials: dict) -> WorkflowCredentials:
        """Save encrypted credentials for a user and service."""
        # Check if credentials already exist
        existing = self.db.query(WorkflowCredentials).filter(
            and_(
                WorkflowCredentials.user_id == user_id,
                WorkflowCredentials.service_name == service_name
            )
        ).first()
        
        encrypted_creds = self.encrypt_credentials(credentials)
        
        if existing:
            existing.encrypted_credentials = encrypted_creds
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            new_creds = WorkflowCredentials(
                user_id=user_id,
                service_name=service_name,
                encrypted_credentials=encrypted_creds
            )
            self.db.add(new_creds)
            self.db.commit()
            return new_creds
    
    def get_credentials(self, user_id: int, service_name: str) -> Optional[dict]:
        """Get decrypted credentials for a user and service."""
        creds = self.db.query(WorkflowCredentials).filter(
            and_(
                WorkflowCredentials.user_id == user_id,
                WorkflowCredentials.service_name == service_name,
                WorkflowCredentials.is_active == True
            )
        ).first()
        
        if creds:
            return self.decrypt_credentials(creds.encrypted_credentials)
        return None
    
    async def create_execution(self, user_id: int, workflow_request: WorkflowRunRequest) -> WorkflowExecution:
        """Create a new workflow execution record."""
        execution = WorkflowExecution(
            user_id=user_id,
            workflow_type=workflow_request.workflow_type,
            status="pending",
            input_data=workflow_request.dict(),
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    async def log_workflow_step(self, execution_id: int, step_name: str, step_type: str, 
                              status: str, input_data: dict = None, output_data: dict = None, 
                              error_message: str = None, duration_ms: int = None) -> WorkflowLog:
        """Log a workflow step."""
        log_entry = WorkflowLog(
            execution_id=execution_id,
            step_name=step_name,
            step_type=step_type,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            duration_ms=duration_ms
        )
        self.db.add(log_entry)
        self.db.commit()
        return log_entry
    
    async def update_execution_status(self, execution_id: int, status: str, 
                                    output_data: dict = None, error_message: str = None,
                                    leads_processed: int = None, leads_enriched: int = None,
                                    confidence_score: float = None):
        """Update execution status and metrics."""
        execution = self.db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
        if execution:
            execution.status = status
            if output_data:
                execution.output_data = output_data
            if error_message:
                execution.error_message = error_message
            if leads_processed is not None:
                execution.leads_processed = leads_processed
            if leads_enriched is not None:
                execution.leads_enriched = leads_enriched
            if confidence_score is not None:
                execution.confidence_score = confidence_score
            if status in ["completed", "failed", "cancelled"]:
                execution.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def fetch_hubspot_leads(self, credentials: dict, filters: dict = None) -> List[dict]:
        """Fetch leads from HubSpot API."""
        try:
            api_key = credentials.get('hubspot_api_key')
            access_token = credentials.get('hubspot_access_token')
            
            if not api_key and not access_token:
                raise ValueError("HubSpot API key or access token required")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
            
            # Build API URL
            url = "https://api.hubapi.com/crm/v3/objects/contacts"
            if api_key:
                url += f"?hapikey={api_key}"
            
            # Add properties to fetch
            properties = [
                'firstname', 'lastname', 'email', 'phone', 'company', 
                'jobtitle', 'website', 'city', 'state', 'country',
                'lifecyclestage', 'hubspot_owner_id'
            ]
            
            params = {
                'properties': ','.join(properties),
                'limit': 100
            }
            
            if not api_key:  # Using access token
                params['archived'] = 'false'
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Failed to fetch HubSpot leads: {e}")
            raise
    
    async def enrich_lead_with_ai(self, lead_data: dict, openai_credentials: dict) -> Tuple[dict, float]:
        """Use OpenAI to enrich lead data with additional information."""
        try:
            api_key = openai_credentials.get('openai_api_key')
            if not api_key:
                raise ValueError("OpenAI API key required")
            
            # Use the new OpenAI client
            client = openai.OpenAI(api_key=api_key)
            
            # Prepare prompt for lead enrichment
            prompt = f"""
            Enrich the following lead data with additional professional information:
            
            Lead Data:
            {json.dumps(lead_data, indent=2)}
            
            Please provide enrichment in the following JSON format:
            {{
                "first_name": "extracted or improved first name",
                "last_name": "extracted or improved last name", 
                "email": "validated email",
                "phone": "formatted phone number",
                "company": "full company name",
                "job_title": "standardized job title",
                "department": "likely department",
                "linkedin_url": "LinkedIn profile URL if determinable",
                "industry": "company industry",
                "company_size": "estimated company size category",
                "seniority_level": "junior/mid/senior/executive",
                "confidence_score": "confidence level 0-1 for the enrichment"
            }}
            
            Rules:
            1. Only return the JSON object, no additional text
            2. Use null for unknown fields
            3. Provide confidence score based on data quality
            4. Standardize job titles and company names
            5. Validate email format
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional data enrichment specialist. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            try:
                enriched_data = json.loads(result_text)
                confidence_score = enriched_data.pop('confidence_score', 0.5)
                return enriched_data, float(confidence_score)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {result_text}")
                return {}, 0.0
                
        except Exception as e:
            logger.error(f"AI enrichment failed: {e}")
            return {}, 0.0
    
    async def validate_enriched_data(self, original_data: dict, enriched_data: dict) -> Tuple[bool, float, str]:
        """Validate enriched data against original data."""
        try:
            score = 0.0
            total_checks = 0
            issues = []
            
            # Check email consistency
            if original_data.get('email') and enriched_data.get('email'):
                total_checks += 1
                if original_data['email'].lower() == enriched_data['email'].lower():
                    score += 1.0
                else:
                    issues.append("Email mismatch")
            
            # Check name consistency
            if original_data.get('firstname') and enriched_data.get('first_name'):
                total_checks += 1
                if original_data['firstname'].lower() in enriched_data['first_name'].lower():
                    score += 1.0
                else:
                    issues.append("First name inconsistency")
            
            if original_data.get('lastname') and enriched_data.get('last_name'):
                total_checks += 1
                if original_data['lastname'].lower() in enriched_data['last_name'].lower():
                    score += 1.0
                else:
                    issues.append("Last name inconsistency")
            
            # Check company consistency
            if original_data.get('company') and enriched_data.get('company'):
                total_checks += 1
                if original_data['company'].lower() in enriched_data['company'].lower():
                    score += 1.0
                else:
                    issues.append("Company name inconsistency")
            
            # Calculate confidence score
            confidence = score / max(total_checks, 1)
            is_valid = confidence >= 0.8  # 80% threshold
            
            remarks = f"Validation score: {confidence:.2f}. " + "; ".join(issues) if issues else "Data validated successfully"
            
            return is_valid, confidence, remarks
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False, 0.0, f"Validation error: {str(e)}"
    
    async def update_hubspot_contact(self, credentials: dict, contact_id: str, enriched_data: dict) -> bool:
        """Update HubSpot contact with enriched data."""
        try:
            api_key = credentials.get('hubspot_api_key')
            access_token = credentials.get('hubspot_access_token')
            
            if not api_key and not access_token:
                raise ValueError("HubSpot API key or access token required")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
            
            # Map enriched data to HubSpot properties
            hubspot_properties = {}
            if enriched_data.get('first_name'):
                hubspot_properties['firstname'] = enriched_data['first_name']
            if enriched_data.get('last_name'):
                hubspot_properties['lastname'] = enriched_data['last_name']
            if enriched_data.get('company'):
                hubspot_properties['company'] = enriched_data['company']
            if enriched_data.get('job_title'):
                hubspot_properties['jobtitle'] = enriched_data['job_title']
            if enriched_data.get('industry'):
                hubspot_properties['industry'] = enriched_data['industry']
            if enriched_data.get('linkedin_url'):
                hubspot_properties['linkedin_url'] = enriched_data['linkedin_url']
            
            if not hubspot_properties:
                return True  # Nothing to update
            
            url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            if api_key:
                url += f"?hapikey={api_key}"
            
            payload = {
                'properties': hubspot_properties
            }
            
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update HubSpot contact {contact_id}: {e}")
            return False
    
    async def run_lead_enrichment_workflow(self, user_id: int, workflow_request: WorkflowRunRequest) -> WorkflowExecution:
        """Execute the complete lead enrichment workflow."""
        execution = await self.create_execution(user_id, workflow_request)
        
        try:
            # Update execution status to running
            await self.update_execution_status(execution.id, "running")
            await self.log_workflow_step(execution.id, "workflow_start", "trigger", "running")
            
            # Step 1: Fetch leads from HubSpot
            await self.log_workflow_step(execution.id, "fetch_hubspot_leads", "trigger", "running")
            hubspot_leads = await self.fetch_hubspot_leads(
                workflow_request.credentials.dict(),
                workflow_request.lead_filters
            )
            await self.log_workflow_step(
                execution.id, "fetch_hubspot_leads", "trigger", "completed",
                output_data={"leads_count": len(hubspot_leads)}
            )
            
            enriched_count = 0
            total_confidence = 0.0
            
            # Step 2: Process each lead
            for i, lead in enumerate(hubspot_leads):
                lead_id = lead.get('id')
                properties = lead.get('properties', {})
                
                await self.log_workflow_step(
                    execution.id, f"process_lead_{i+1}", "enrichment", "running",
                    input_data={"lead_id": lead_id, "properties": properties}
                )
                
                try:
                    # Step 3: AI Enrichment
                    enriched_data, confidence = await self.enrich_lead_with_ai(
                        properties, workflow_request.credentials.dict()
                    )
                    
                    if confidence > 0:
                        # Step 4: Validate enriched data
                        is_valid, validation_score, remarks = await self.validate_enriched_data(
                            properties, enriched_data
                        )
                        
                        # Save enriched data to database
                        # Find corresponding lead in our database
                        db_lead = self.db.query(Lead).filter(Lead.email == properties.get('email')).first()
                        if db_lead:
                            enriched_record = EnrichedLeadData(
                                lead_id=db_lead.id,
                                execution_id=execution.id,
                                original_data=properties,
                                enriched_data=enriched_data,
                                confidence_score=validation_score,
                                data_sources={"ai_model": "gpt-4", "hubspot": True},
                                validation_status="validated" if is_valid else "rejected"
                            )
                            self.db.add(enriched_record)
                        
                        # Step 5: Update HubSpot if validation passed
                        if is_valid and validation_score >= 0.85:
                            update_success = await self.update_hubspot_contact(
                                workflow_request.credentials.dict(), lead_id, enriched_data
                            )
                            if update_success:
                                enriched_count += 1
                                total_confidence += validation_score
                        
                        await self.log_workflow_step(
                            execution.id, f"process_lead_{i+1}", "enrichment", "completed",
                            output_data={
                                "enriched": is_valid,
                                "confidence": validation_score,
                                "remarks": remarks
                            }
                        )
                    else:
                        await self.log_workflow_step(
                            execution.id, f"process_lead_{i+1}", "enrichment", "failed",
                            error_message="AI enrichment returned no results"
                        )
                
                except Exception as e:
                    await self.log_workflow_step(
                        execution.id, f"process_lead_{i+1}", "enrichment", "failed",
                        error_message=str(e)
                    )
            
            # Calculate final metrics
            avg_confidence = total_confidence / max(enriched_count, 1)
            
            # Update final execution status
            await self.update_execution_status(
                execution.id, "completed",
                output_data={
                    "total_leads": len(hubspot_leads),
                    "enriched_leads": enriched_count,
                    "average_confidence": avg_confidence
                },
                leads_processed=len(hubspot_leads),
                leads_enriched=enriched_count,
                confidence_score=avg_confidence
            )
            
            await self.log_workflow_step(execution.id, "workflow_complete", "completion", "completed")
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            await self.update_execution_status(
                execution.id, "failed", 
                error_message=str(e)
            )
            await self.log_workflow_step(
                execution.id, "workflow_error", "error", "failed",
                error_message=str(e)
            )
            self.db.commit()
        
        return execution
    
    def get_execution_status(self, execution_id: int, user_id: int) -> Optional[WorkflowExecution]:
        """Get execution status and logs."""
        return self.db.query(WorkflowExecution).filter(
            and_(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.user_id == user_id
            )
        ).first()
    
    def get_user_executions(self, user_id: int, limit: int = 50) -> List[WorkflowExecution]:
        """Get user's workflow executions."""
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.user_id == user_id
        ).order_by(desc(WorkflowExecution.created_at)).limit(limit).all() 