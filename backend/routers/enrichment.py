"""
Lead Enrichment API Router - RESTful endpoints for lead data enrichment.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db
from auth import get_current_user
from models import User, Lead
from services.lead_enrichment_service import LeadEnrichmentService
from schemas import LeadEnrichmentRequest, LeadEnrichmentResponse, BulkEnrichmentRequest, BulkEnrichmentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enrichment", tags=["Lead Enrichment"])

@router.post("/leads/{lead_id}/enrich", response_model=LeadEnrichmentResponse)
async def enrich_lead(
    lead_id: int,
    enrichment_types: Optional[List[str]] = Query(None, description="Types of enrichment to perform"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enrich a specific lead with data cleaning, validation, and augmentation.
    
    Available enrichment types:
    - email: Email validation and domain analysis
    - phone: Phone number validation and formatting
    - company: Company information enrichment
    - social: Social media profile discovery
    - normalize: Data normalization and cleaning
    - dedup: Duplicate detection
    """
    try:
        # Verify lead exists and user has access
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Initialize enrichment service
        enrichment_service = LeadEnrichmentService(db)
        
        # Perform enrichment
        result = await enrichment_service.enrich_lead(lead_id, enrichment_types)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Lead {lead_id} enriched successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Lead enrichment failed for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")

@router.post("/leads/bulk-enrich", response_model=BulkEnrichmentResponse)
async def bulk_enrich_leads(
    background_tasks: BackgroundTasks,
    lead_ids: Optional[List[int]] = Query(None, description="Specific lead IDs to enrich"),
    enrichment_types: Optional[List[str]] = Query(None, description="Types of enrichment to perform"),
    batch_size: int = Query(10, description="Batch size for processing"),
    async_mode: bool = Query(False, description="Process in background"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk enrich multiple leads for the current organization.
    
    Can be run synchronously or asynchronously (background task).
    """
    try:
        # Initialize enrichment service
        enrichment_service = LeadEnrichmentService(db)
        
        if async_mode:
            # Add to background tasks
            background_tasks.add_task(
                enrichment_service.bulk_enrich_leads,
                current_user.organization_id,
                lead_ids,
                enrichment_types,
                batch_size
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": "Bulk enrichment started in background",
                    "data": {
                        "status": "processing",
                        "organization_id": current_user.organization_id,
                        "lead_ids": lead_ids,
                        "enrichment_types": enrichment_types,
                        "batch_size": batch_size
                    }
                }
            )
        else:
            # Process synchronously
            result = await enrichment_service.bulk_enrich_leads(
                current_user.organization_id,
                lead_ids,
                enrichment_types,
                batch_size
            )
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"Bulk enrichment completed: {result['enriched_leads']}/{result['total_leads']} leads processed",
                    "data": result
                }
            )
        
    except Exception as e:
        logger.error(f"Bulk enrichment failed for organization {current_user.organization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk enrichment failed: {str(e)}")

@router.get("/leads/{lead_id}/enrichment-status")
async def get_lead_enrichment_status(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the enrichment status and metadata for a specific lead.
    """
    try:
        # Verify lead exists and user has access
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Extract enrichment metadata from custom fields
        custom_fields = lead.custom_fields or {}
        enrichment_data = custom_fields.get("enrichment", {})
        validation_data = custom_fields.get("validation", {})
        duplicate_data = custom_fields.get("duplicate_check", {})
        
        enrichment_status = {
            "lead_id": lead_id,
            "has_been_enriched": bool(enrichment_data),
            "last_enriched": enrichment_data.get("last_enriched"),
            "enrichment_types": enrichment_data.get("enrichment_types", []),
            "data_sources": enrichment_data.get("data_sources", []),
            "validation_results": validation_data,
            "duplicate_check": duplicate_data,
            "enriched_fields": {
                "email": {
                    "original": lead.email,
                    "is_valid": validation_data.get("email", {}).get("is_valid", False)
                },
                "phone": {
                    "original": lead.phone,
                    "is_valid": validation_data.get("phone", {}).get("is_valid", False)
                },
                "company": {
                    "original": lead.company,
                    "industry": custom_fields.get("industry"),
                    "size": custom_fields.get("company_size")
                }
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": enrichment_status
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get enrichment status for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get enrichment status: {str(e)}")

@router.post("/leads/{lead_id}/validate")
async def validate_lead_data(
    lead_id: int,
    validation_types: Optional[List[str]] = Query(None, description="Types of validation to perform"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform data validation on a lead without full enrichment.
    
    Available validation types:
    - email: Email format and deliverability
    - phone: Phone number format validation
    - duplicates: Check for potential duplicates
    """
    try:
        # Verify lead exists and user has access
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Initialize enrichment service
        enrichment_service = LeadEnrichmentService(db)
        
        validation_results = {}
        
        # Default validation types
        if validation_types is None:
            validation_types = ['email', 'phone', 'duplicates']
        
        # Perform email validation
        if 'email' in validation_types:
            email_result = await enrichment_service._enrich_email(lead)
            validation_results['email'] = email_result['validation']
        
        # Perform phone validation
        if 'phone' in validation_types:
            phone_result = await enrichment_service._enrich_phone(lead)
            validation_results['phone'] = phone_result['validation']
        
        # Check for duplicates
        if 'duplicates' in validation_types:
            duplicate_result = await enrichment_service._check_duplicates(lead)
            validation_results['duplicates'] = {
                "potential_duplicates_count": len(duplicate_result['potential_duplicates']),
                "duplicate_score": duplicate_result['duplicate_score'],
                "matching_criteria": duplicate_result['matching_criteria']
            }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Lead validation completed",
                "data": {
                    "lead_id": lead_id,
                    "validation_types": validation_types,
                    "validation_results": validation_results,
                    "validated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Lead validation failed for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/leads/{lead_id}/duplicates")
async def find_lead_duplicates(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Find potential duplicate leads for a specific lead.
    """
    try:
        # Verify lead exists and user has access
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Initialize enrichment service
        enrichment_service = LeadEnrichmentService(db)
        
        # Check for duplicates
        duplicate_result = await enrichment_service._check_duplicates(lead)
        
        # Get detailed information about potential duplicates
        duplicate_leads = []
        for dup in duplicate_result['potential_duplicates']:
            dup_lead = db.query(Lead).filter(Lead.id == dup['lead_id']).first()
            if dup_lead:
                duplicate_leads.append({
                    "lead_id": dup_lead.id,
                    "first_name": dup_lead.first_name,
                    "last_name": dup_lead.last_name,
                    "email": dup_lead.email,
                    "company": dup_lead.company,
                    "phone": dup_lead.phone,
                    "match_type": dup['match_type'],
                    "match_score": dup['score'],
                    "matched_field": dup['matched_field'],
                    "matched_value": dup['matched_value']
                })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "lead_id": lead_id,
                    "duplicate_score": duplicate_result['duplicate_score'],
                    "potential_duplicates_count": len(duplicate_leads),
                    "potential_duplicates": duplicate_leads,
                    "matching_criteria": duplicate_result['matching_criteria']
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Duplicate search failed for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Duplicate search failed: {str(e)}")

@router.get("/enrichment-types")
async def get_available_enrichment_types():
    """
    Get a list of available enrichment types and their descriptions.
    """
    enrichment_types = {
        "email": {
            "name": "Email Validation",
            "description": "Validate email format, check domain, and normalize email addresses",
            "data_sources": ["email-validator", "domain_lookup"]
        },
        "phone": {
            "name": "Phone Number Validation",
            "description": "Validate and format phone numbers to standard formats",
            "data_sources": ["regex_validation", "format_standardization"]
        },
        "company": {
            "name": "Company Enrichment",
            "description": "Enrich company information including industry classification and size estimation",
            "data_sources": ["domain_analysis", "industry_keywords", "job_title_analysis"]
        },
        "social": {
            "name": "Social Profile Discovery",
            "description": "Discover and validate social media profiles",
            "data_sources": ["linkedin_validation", "social_discovery"]
        },
        "normalize": {
            "name": "Data Normalization",
            "description": "Clean and normalize names, company names, and job titles",
            "data_sources": ["text_processing", "capitalization_rules", "abbreviation_handling"]
        },
        "dedup": {
            "name": "Duplicate Detection",
            "description": "Identify potential duplicate leads in the database",
            "data_sources": ["database_comparison", "similarity_matching"]
        }
    }
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "enrichment_types": enrichment_types,
                "default_types": ["email", "phone", "company", "normalize", "dedup"],
                "total_types": len(enrichment_types)
            }
        }
    ) 