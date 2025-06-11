"""
Google Maps Lead Generation Workflow Router

This router handles the Google Maps lead generation workflow endpoints.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import User
from schemas import (
    GoogleMapsWorkflowRequest, GoogleMapsWorkflowResponse, 
    GoogleMapsWorkflowStatusResponse, GoogleMapsLeadResponse,
    APIResponse
)
from services.google_maps_lead_service import GoogleMapsLeadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows/google-maps", tags=["Google Maps Workflow"])


# Dependency to get Google Maps service
def get_google_maps_service(db: Session = Depends(get_db)) -> GoogleMapsLeadService:
    """Get Google Maps lead generation service."""
    try:
        # Note: OpenAI API key will be provided by the user via credentials
        return GoogleMapsLeadService(db)
    except Exception as e:
        logger.error(f"Failed to initialize GoogleMapsLeadService: {e}")
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")


@router.post("/start", response_model=APIResponse)
async def start_google_maps_workflow(
    request: GoogleMapsWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a Google Maps lead generation workflow.
    
    This endpoint initiates the workflow that:
    1. Scrapes Google Maps for businesses in the specified location and industry
    2. Extracts website URLs from the search results
    3. Scrapes each website for contact information
    4. Optionally enriches the data using OpenAI
    5. Stores the results in the database
    """
    try:
        logger.info(f"Starting Google Maps workflow for user {current_user.username}")
        logger.info(f"Request data: {request.dict()}")
        
        # Initialize service with OpenAI key from request
        service = GoogleMapsLeadService(db, request.openai_api_key)
        logger.info("Service initialized successfully")
        
        # Create workflow execution record (but don't start workflow yet)
        from models import WorkflowExecution, GoogleMapsSearchExecution
        from datetime import datetime
        
        # Create workflow execution record
        workflow_execution = WorkflowExecution(
            user_id=current_user.id,
            workflow_type="google_maps_lead_generation",
            status="pending",
            input_data={
                "location": request.location,
                "industry": request.industry,
                "max_results": request.max_results,
                "include_ai_enrichment": request.include_ai_enrichment
            },
            started_at=datetime.utcnow()
        )
        db.add(workflow_execution)
        db.commit()
        db.refresh(workflow_execution)
        
        # Create search execution record
        search_query = f"{request.location}+{request.industry.replace(' ', '+')}"
        search_execution = GoogleMapsSearchExecution(
            workflow_execution_id=workflow_execution.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            location=request.location,
            industry=request.industry,
            search_query=search_query,
            status="pending"
        )
        db.add(search_execution)
        db.commit()
        db.refresh(search_execution)
        
        # Start the workflow in background using FastAPI's BackgroundTasks
        background_tasks.add_task(
            service._run_workflow,
            workflow_execution.id,
            search_execution.id,
            request
        )
        
        logger.info(f"Workflow started: execution_id={workflow_execution.id}, search_execution_id={search_execution.id}")
        
        # Create search query for response
        search_query_display = f"{request.location} {request.industry}"
        
        response_data = GoogleMapsWorkflowResponse(
            execution_id=workflow_execution.id,
            search_execution_id=search_execution.id,
            status="pending",
            message="Google Maps lead generation workflow started successfully",
            search_query=search_query_display,
            estimated_completion_time="5-10 minutes"
        )
        
        return APIResponse(
            success=True,
            data=response_data.dict(),
            message="Workflow started successfully"
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error starting Google Maps workflow: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error starting workflow: {str(e)}")


@router.get("/status/{execution_id}", response_model=APIResponse)
async def get_workflow_status(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    service: GoogleMapsLeadService = Depends(get_google_maps_service)
):
    """
    Get the status of a Google Maps workflow execution.
    
    Returns detailed progress information including:
    - Current step and progress percentage
    - Number of URLs found and websites scraped
    - Number of emails found and leads enriched
    - List of generated leads
    """
    try:
        status_data = service.get_workflow_status(execution_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Workflow execution not found")
        
        # Convert to response schema
        response_data = GoogleMapsWorkflowStatusResponse(**status_data)
        
        return APIResponse(
            success=True,
            data=response_data.dict(),
            message="Workflow status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/{execution_id}", response_model=APIResponse)
async def get_workflow_leads(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    service: GoogleMapsLeadService = Depends(get_google_maps_service)
):
    """
    Get all leads generated by a specific Google Maps workflow execution.
    """
    try:
        leads = service.get_leads_by_execution(execution_id)
        
        # Convert to response schemas
        lead_responses = [
            GoogleMapsLeadResponse(
                id=lead.id,
                execution_id=lead.execution_id,
                organization_id=lead.organization_id,
                user_id=lead.user_id,
                business_name=lead.business_name,
                google_maps_url=lead.google_maps_url,
                website_url=lead.website_url,
                location=lead.location,
                industry=lead.industry,
                email=lead.email,
                phone=lead.phone,
                address=lead.address,
                ai_enriched_data=lead.ai_enriched_data,
                confidence_score=lead.confidence_score,
                enrichment_status=lead.enrichment_status,
                conversion_status=lead.conversion_status,
                converted_to_lead_id=lead.converted_to_lead_id,
                scraped_at=lead.scraped_at,
                enriched_at=lead.enriched_at,
                converted_at=lead.converted_at,
                created_at=lead.created_at,
                updated_at=lead.updated_at
            )
            for lead in leads
        ]
        
        return APIResponse(
            success=True,
            data={
                "leads": [lead.dict() for lead in lead_responses],
                "total": len(lead_responses)
            },
            message=f"Retrieved {len(lead_responses)} leads"
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/convert", response_model=APIResponse)
async def convert_lead_to_crm(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Convert a Google Maps lead to a regular CRM lead.
    
    This creates a new Lead record from the Google Maps lead data.
    """
    try:
        from models import GoogleMapsLead, Lead, LeadSource
        
        # Get the Google Maps lead
        google_maps_lead = db.query(GoogleMapsLead).filter(
            GoogleMapsLead.id == lead_id
        ).first()
        
        if not google_maps_lead:
            raise HTTPException(status_code=404, detail="Google Maps lead not found")
        
        # Check if already converted
        if google_maps_lead.converted_to_lead_id:
            raise HTTPException(status_code=400, detail="Lead already converted")
        
        # Extract name from business name (simple approach)
        business_name = google_maps_lead.business_name
        first_name = "Unknown"
        last_name = "Contact"
        
        # Try to extract a contact name from AI enriched data
        if google_maps_lead.ai_enriched_data and google_maps_lead.ai_enriched_data.get('contact_name'):
            name_parts = google_maps_lead.ai_enriched_data['contact_name'].split(' ')
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
        
        # Create new CRM lead
        new_lead = Lead(
            email=google_maps_lead.email or f"contact@{google_maps_lead.website_url.split('/')[2] if google_maps_lead.website_url else 'unknown.com'}",
            first_name=first_name,
            last_name=last_name,
            company=google_maps_lead.business_name,
            phone=google_maps_lead.phone,
            website=google_maps_lead.website_url,
            source=LeadSource.OTHER,  # Could be enhanced with LeadSource.GOOGLE_MAPS
            organization_id=current_user.organization_id,
            assigned_to_id=current_user.id,
            notes=f"Generated from Google Maps search: {google_maps_lead.location} {google_maps_lead.industry}",
            custom_fields={
                "google_maps_lead_id": google_maps_lead.id,
                "ai_enriched_data": google_maps_lead.ai_enriched_data,
                "confidence_score": google_maps_lead.confidence_score
            }
        )
        
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        
        # Update the Google Maps lead to mark as converted
        google_maps_lead.converted_to_lead_id = new_lead.id
        google_maps_lead.conversion_status = "converted"
        google_maps_lead.converted_at = new_lead.created_at
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "lead_id": new_lead.id,
                "google_maps_lead_id": google_maps_lead.id,
                "business_name": google_maps_lead.business_name
            },
            message="Lead converted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template", response_model=APIResponse)
async def get_workflow_template():
    """
    Get the Google Maps workflow template configuration.
    
    This provides information about the workflow including:
    - Required inputs (location, industry)
    - Optional parameters (max_results, include_ai_enrichment)
    - Expected outputs
    """
    template = {
        "name": "Google Maps Lead Generation",
        "description": "Scrape Google Maps for businesses and generate leads with AI enrichment",
        "version": "1.0.0",
        "inputs": [
            {
                "name": "location",
                "type": "string",
                "required": True,
                "description": "Geographic location to search (e.g., 'Calgary', 'New York City')",
                "example": "Calgary"
            },
            {
                "name": "industry",
                "type": "string",
                "required": True,
                "description": "Industry or business type to search for (e.g., 'dentists', 'restaurants')",
                "example": "dentists"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "default": 20,
                "min": 1,
                "max": 100,
                "description": "Maximum number of leads to generate"
            },
            {
                "name": "include_ai_enrichment",
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Whether to use OpenAI for lead enrichment"
            }
        ],
        "outputs": [
            "Business names and contact information",
            "Website URLs and email addresses",
            "Phone numbers and addresses",
            "AI-enriched business intelligence",
            "Lead quality scores and recommendations"
        ],
        "estimated_duration": "5-10 minutes",
        "requirements": [
            "OpenAI API key (for AI enrichment)",
            "Stable internet connection"
        ]
    }
    
    return APIResponse(
        success=True,
        data=template,
        message="Workflow template retrieved successfully"
    ) 