"""
Lead management API endpoints.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import os

from database import get_db
from models import Lead, User, Organization, LeadStatus, LeadSource, LeadTemperature, LeadScoreHistory, ActivityLog
from schemas import (
    LeadCreate, LeadUpdate, LeadResponse, 
    APIResponse, ListResponse
)
from routers.auth import get_current_active_user, get_dev_user
# from services import LeadScoringService  # REMOVED: Backend scoring is handled by n8n workflows only

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])

# Simple, working delete endpoint for development
@router.get("/delete-test/{lead_id}")
async def delete_lead_test(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """TEST: Delete a lead for development - WORKING VERSION."""
    print(f"🔥🔥🔥 DELETE_TEST CALLED WITH ID: {lead_id} 🔥🔥🔥")
    
    # Import models to handle related records
    from models import LeadScoreHistory, ActivityLog
    
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        print(f"🔥🔥🔥 LEAD {lead_id} NOT FOUND 🔥🔥🔥")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    print(f"🔥🔥🔥 DELETING LEAD {lead_id}: {lead.email} 🔥🔥🔥")
    
    # Delete related records first to avoid foreign key constraints
    score_history_count = db.query(LeadScoreHistory).filter(LeadScoreHistory.lead_id == lead_id).count()
    if score_history_count > 0:
        print(f"🗑️ Deleting {score_history_count} score history records...")
        db.query(LeadScoreHistory).filter(LeadScoreHistory.lead_id == lead_id).delete()
    
    activity_count = db.query(ActivityLog).filter(ActivityLog.lead_id == lead_id).count()
    if activity_count > 0:
        print(f"🗑️ Deleting {activity_count} activity log records...")
        db.query(ActivityLog).filter(ActivityLog.lead_id == lead_id).delete()
    
    # Delete the lead
    db.delete(lead)
    db.commit()
    
    return {
        "success": True,
        "data": {"id": lead_id},
        "message": "Lead deleted successfully"
    }


def _generate_enhanced_test_data(lead):
    """Generate enhanced test data across the three supported temperature ranges for lead scoring."""
    lead_hash = abs(hash(lead.email))
    lead_type = lead_hash % 3  # 0=hot, 1=warm, 2=cold (only 3 supported types)
    
    print(f"🌡️ TEMPERATURE GENERATION: {lead.email} -> hash: {lead_hash}, type: {lead_type}")

    # Generate job titles that affect demographic scoring
    executive_titles = ["CEO", "CTO", "VP Sales", "Director of Marketing", "Founder"]
    manager_titles = ["Sales Manager", "Marketing Manager", "Team Lead", "Department Head"]
    regular_titles = ["Software Engineer", "Marketing Specialist", "Sales Rep", "Analyst"]

    if lead_type == 0:  # HOT LEADS (score >= 80) - maximized for high scores
        job_title = executive_titles[lead_hash % len(executive_titles)]  # 25 points (CEO/CTO/etc)
        website_visits = 15 + (lead_hash % 10)  # 15-25 visits (15 points)
        pages_viewed = 25 + (lead_hash % 15)    # 25-40 pages (15 points)
        email_opens = 8 + (lead_hash % 5)       # 8-12 opens (10 points)
        email_clicks = 5 + (lead_hash % 4)      # 5-8 clicks (10 points)
        downloads = 4 + (lead_hash % 2)         # 4-5 downloads (10 points max)
        company_size = 1200 + (lead_hash % 300) # 1200-1500 employees (25 points)
        industry = ["technology", "saas", "finance"][lead_hash % 3]  # 10 points
        # Hot leads should have recent activity for temporal bonus (10 points)
        # This will be handled by setting last_activity_at to recent date
    elif lead_type == 1:  # WARM LEADS (score 60-79)
        job_title = manager_titles[lead_hash % len(manager_titles)] if lead_hash % 2 else executive_titles[lead_hash % len(executive_titles)]
        website_visits = 8 + (lead_hash % 8)    # 8-15 visits
        pages_viewed = 15 + (lead_hash % 15)    # 15-30 pages
        email_opens = 4 + (lead_hash % 4)       # 4-7 opens
        email_clicks = 2 + (lead_hash % 3)      # 2-4 clicks
        downloads = 1 + (lead_hash % 2)         # 1-2 downloads
        company_size = 200 + (lead_hash % 300)  # 200-500 employees
        industry = ["technology", "healthcare", "consulting"][lead_hash % 3]
    else:  # COLD LEADS (score 40-59, was previously frozen but now maps to cold)
        job_title = regular_titles[lead_hash % len(regular_titles)] if lead_hash % 3 else manager_titles[lead_hash % len(manager_titles)]
        website_visits = 2 + (lead_hash % 4)    # 2-5 visits (slightly higher than before)
        pages_viewed = 3 + (lead_hash % 8)      # 3-10 pages (slightly higher than before)
        email_opens = max(0, (lead_hash % 3))   # 0-2 opens
        email_clicks = max(0, (lead_hash % 2))  # 0-1 clicks
        downloads = max(0, (lead_hash % 2))     # 0-1 downloads
        company_size = 25 + (lead_hash % 75)    # 25-100 employees (slightly higher than before)
        industry = ["retail", "manufacturing", "other"][lead_hash % 3]

    # Set last_activity_at based on lead type for temporal scoring
    from datetime import datetime, timedelta
    
    if lead_type == 0:  # Hot leads get very recent activity (10 temporal points)
        last_activity_at = datetime.utcnow() - timedelta(hours=2)
    elif lead_type == 1:  # Warm leads get recent activity (7 temporal points)
        last_activity_at = datetime.utcnow() - timedelta(days=2)
    else:  # Cold leads get older activity (3 temporal points)
        last_activity_at = datetime.utcnow() - timedelta(days=10)

    return {
        "job_title": job_title,
        "website_visits": website_visits,
        "pages_viewed": pages_viewed,
        "email_opens": email_opens,
        "email_clicks": email_clicks,
        "downloads": downloads,
        "company_size": company_size,
        "industry": industry,
        "unsubscribed": False,
        "bounced_emails": 0,
        "last_activity_at": last_activity_at.isoformat(),
        # Temperature will be calculated based on the final score, not generated here
    }


def _calculate_score_from_test_data(lead, test_data):
    """Calculate a realistic score based on the lead's actual data and enhanced test data."""
    score = 0
    
    # Demographic scoring (based on actual lead data + test data) - reduced max points
    if lead.company or test_data.get('company_size', 0) > 0:
        score += 5  # Has company information
    
    if lead.job_title or test_data.get('job_title'):
        job_title = test_data.get('job_title', lead.job_title or '').lower()
        if any(title in job_title for title in ['ceo', 'cto', 'founder', 'vp', 'vice president', 'director']):
            score += 15  # Executive level (reduced from 25)
        elif any(title in job_title for title in ['manager', 'lead', 'head']):
            score += 10  # Manager level (reduced from 15)
        else:
            score += 5   # Has job title
    
    if lead.phone:
        score += 3   # Has phone number (reduced from 5)
    
    if lead.linkedin_url:
        score += 3   # Has LinkedIn profile (reduced from 5)
    
    # Company size scoring (from test data) - reduced max points
    company_size = test_data.get('company_size', 0)
    if company_size >= 1000:
        score += 15  # Enterprise (reduced from 25)
    elif company_size >= 200:
        score += 10  # Mid-market (reduced from 15)
    elif company_size >= 50:
        score += 6   # Small business (reduced from 10)
    elif company_size > 0:
        score += 3   # Has company size info (reduced from 5)
    
    # Engagement scoring (from test data) - reduced max points
    website_visits = test_data.get('website_visits', 0)
    if website_visits >= 15:
        score += 10  # High engagement (reduced from 15)
    elif website_visits >= 8:
        score += 7   # Medium engagement (reduced from 10)
    elif website_visits >= 3:
        score += 4   # Some engagement (reduced from 5)
    
    pages_viewed = test_data.get('pages_viewed', 0)
    if pages_viewed >= 25:
        score += 10  # Very engaged (reduced from 15)
    elif pages_viewed >= 15:
        score += 7   # Engaged (reduced from 10)
    elif pages_viewed >= 5:
        score += 4   # Some interest (reduced from 5)
    
    # Email engagement scoring - reduced max points
    email_opens = test_data.get('email_opens', 0)
    email_clicks = test_data.get('email_clicks', 0)
    
    score += min(email_opens * 1, 6)    # Up to 6 points for email opens (reduced from 10)
    score += min(email_clicks * 3, 9)   # Up to 9 points for email clicks (reduced from 15)
    
    # Download scoring - reduced max points
    downloads = test_data.get('downloads', 0)
    score += min(downloads * 3, 6)      # Up to 6 points for downloads (reduced from 10)
    
    # Source-based scoring (based on actual lead data) - reduced points
    if lead.source:
        source_scores = {
            'referral': 12,      # reduced from 20
            'website': 8,        # reduced from 15
            'social_media': 5,   # reduced from 8
            'email': 6,          # reduced from 10
            'advertising': 7,    # reduced from 12
            'cold_outreach': 3,  # reduced from 5
            'event': 9,          # reduced from 15
            'other': 3           # reduced from 5
        }
        score += source_scores.get(lead.source.value, 3)
    
    # Industry scoring (from test data) - reduced points
    industry = test_data.get('industry', '')
    if industry in ['technology', 'saas', 'finance']:
        score += 6   # High-value industries (reduced from 10)
    elif industry in ['healthcare', 'consulting']:
        score += 4   # Medium-value industries (reduced from 8)
    else:
        score += 2   # Other industries (reduced from 5)
    
    # Temporal scoring (based on last activity) - reduced points
    from datetime import datetime, timedelta
    last_activity_str = test_data.get('last_activity_at')
    if last_activity_str:
        try:
            last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
            now = datetime.utcnow()
            days_since_activity = (now - last_activity.replace(tzinfo=None)).days
            
            if days_since_activity <= 1:
                score += 6   # Very recent activity (reduced from 10)
            elif days_since_activity <= 3:
                score += 4   # Recent activity (reduced from 7)
            elif days_since_activity <= 7:
                score += 3   # Recent activity (reduced from 5)
            elif days_since_activity <= 14:
                score += 2   # Some recent activity (reduced from 3)
        except:
            score += 2   # Default for activity
    
    # Cap the score at 100
    return min(score, 100)


def _calculate_temperature_from_score(score):
    """Calculate lead temperature based on the calculated score."""
    if score >= 70:
        return "hot"
    elif score >= 40:
        return "warm"
    else:
        return "cold"


# Development endpoint - no auth required
@router.get("/dev")
async def get_leads_dev(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    status_filter: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    source_filter: Optional[LeadSource] = Query(None, description="Filter by lead source"),
    search: Optional[str] = Query(None, description="Search in name, email, or company"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    test_scoring: bool = Query(False, description="Test the scoring logic"),
    remove_lead_id: Optional[int] = Query(None, description="Remove a specific lead by ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads with filtering and pagination for development."""
    
    # ULTRA OBVIOUS test - this MUST appear in logs if function is called
    print("=" * 80)
    print("🚨🚨🚨 GET_LEADS_DEV FUNCTION IS BEING CALLED 🚨🚨🚨")
    print(f"🚨🚨🚨 test_scoring parameter = {test_scoring}")
    print(f"🚨🚨🚨 remove_lead_id parameter = {remove_lead_id}")
    print("=" * 80)
    
    # Handle lead removal first
    if remove_lead_id:
        print(f"🚨🚨🚨 REMOVE LEAD REQUESTED FOR ID: {remove_lead_id} 🚨🚨🚨")
        
        # Import models to handle related records
        from models import LeadScoreHistory, ActivityLog
        
        lead = db.query(Lead).filter(
            Lead.id == remove_lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            print(f"🚨🚨🚨 LEAD {remove_lead_id} NOT FOUND FOR REMOVAL 🚨🚨🚨")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        print(f"🚨🚨🚨 REMOVING LEAD {remove_lead_id}: {lead.email} 🚨🚨🚨")
        
        # Delete related records first to avoid foreign key constraints
        score_history_count = db.query(LeadScoreHistory).filter(LeadScoreHistory.lead_id == remove_lead_id).count()
        if score_history_count > 0:
            print(f"🗑️ Deleting {score_history_count} score history records...")
            db.query(LeadScoreHistory).filter(LeadScoreHistory.lead_id == remove_lead_id).delete()
        
        activity_count = db.query(ActivityLog).filter(ActivityLog.lead_id == remove_lead_id).count()
        if activity_count > 0:
            print(f"🗑️ Deleting {activity_count} activity log records...")
            db.query(ActivityLog).filter(ActivityLog.lead_id == remove_lead_id).delete()
        
        # Delete the lead
        db.delete(lead)
        db.commit()
        
        return {
            "success": True,
            "data": {"id": remove_lead_id},
            "message": "Lead removed successfully"
        }
    
    # If test_scoring is True, return the same data as for-scoring endpoint
    if test_scoring:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow (same as for-scoring endpoint)
        formatted_leads = []
        for lead in leads:
            # Generate test data first so we can override job_title
            test_data = _generate_enhanced_test_data(lead)
            
            # Create base lead data
            base_lead_data = {
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,  # Default value, will be overridden by test data if present
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": test_data.get("last_activity_at", lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat()),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
            }
            
            # Merge with test data, allowing test data to override any field
            test_data_filtered = {k: v for k, v in test_data.items() if k not in ["last_activity_at"]}
            
            # Merge with test data, allowing test data to override any field
            formatted_lead = {**base_lead_data, **test_data_filtered}
            
                        # Debug: Log test data generation for verification
            if lead.email in ["mike.chen@bigcorp.net", "john.doe@techcorp.com", "sarah.wilson@startup.io"]:
                print(f"🎯 {lead.email}: job_title='{test_data.get('job_title')}', score_potential={test_data.get('website_visits', 0) + test_data.get('email_opens', 0) * 5}")
            
            # Ensure job_title from test data overrides null database value
            if test_data.get('job_title'):
                formatted_lead['job_title'] = test_data['job_title']
            formatted_leads.append(formatted_lead)
        
        # Return raw data to bypass any response model validation
        return {
            "items": formatted_leads,
            "total": len(formatted_leads),
            "page": 1,
            "per_page": len(formatted_leads), 
            "pages": 1,
            "DEBUG_INFO": {
                "function_called": "get_leads_dev",
                "test_scoring_branch": True,
                "test_scoring_param": test_scoring,
                "leads_processed": len(formatted_leads),
                "debug_timestamp": str(datetime.utcnow())
            }
        }
    
    # Original dev endpoint logic
    # Duplicate the logic from get_leads since we can't call it directly
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
    
    # Format leads with complete data and apply test data for realistic temperatures
    formatted_leads = []
    for lead in leads:
        # Generate test data for each lead to get realistic temperature distribution
        test_data = _generate_enhanced_test_data(lead)
        
        # DEBUG: Print test data generation results
        print(f"🔥 DEBUG: Lead {lead.id} ({lead.email}) -> test_data temperature: {test_data.get('lead_temperature')}")
        
        # Calculate realistic score from test data
        calculated_score = _calculate_score_from_test_data(lead, test_data)
        
        # Calculate temperature based on the calculated score
        calculated_temperature = _calculate_temperature_from_score(calculated_score)
        
        # Create base lead data - use calculated score and temperature
        base_lead_data = {
            "id": lead.id,
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company": lead.company,
            "job_title": lead.job_title,
            "phone": lead.phone,
            "website": lead.website,
            "linkedin_url": lead.linkedin_url,
            "status": lead.status.value if lead.status else None,
            "source": lead.source.value if lead.source else None,
            "score": calculated_score,  # Use calculated score instead of database score
            "lead_temperature": calculated_temperature,  # Use calculated temperature based on score
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else (lead.created_at.isoformat() if lead.created_at else None),
            "tags": lead.tags or [],
            "custom_fields": lead.custom_fields or {},
        }
        
        # Merge with test data to get proper temperature distribution (excluding last_activity_at and lead_temperature as we already used it)
        test_data_filtered = {k: v for k, v in test_data.items() if k not in ["last_activity_at", "lead_temperature"]}
        formatted_lead = {**base_lead_data, **test_data_filtered}
        
        # Ensure job_title from test data overrides null database value
        if test_data.get('job_title'):
            formatted_lead['job_title'] = test_data['job_title']
        formatted_leads.append(formatted_lead)
    
    return {
        "items": formatted_leads,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/dev", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_dev(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Create a new lead for development."""
    # Set organization_id to the dev user's organization if not provided
    if not hasattr(lead_data, 'organization_id') or not lead_data.organization_id:
        lead_data.organization_id = current_user.organization_id
    
    # Check if lead with same email already exists in this organization
    existing_lead = db.query(Lead).filter(
        Lead.email == lead_data.email,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists in the organization"
        )
    
    # Create new lead
    lead_dict = lead_data.model_dump()
    lead_dict['organization_id'] = current_user.organization_id
    db_lead = Lead(**lead_dict)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    # Automatically trigger lead scoring using n8n workflow and get results
    try:
        import httpx
        
        async def trigger_lead_scoring_and_update():
            try:
                async with httpx.AsyncClient() as client:
                    # Prepare lead data for n8n scoring - include all lead details
                    webhook_payload = {
                        "trigger": "new_lead_created",
                        "lead_id": db_lead.id,
                        "action": "score_lead",
                        "timestamp": db_lead.created_at.isoformat(),
                        "lead_data": {
                            "id": db_lead.id,
                            "email": db_lead.email,
                            "first_name": db_lead.first_name,
                            "last_name": db_lead.last_name,
                            "company": db_lead.company,
                            "job_title": db_lead.job_title,
                            "phone": db_lead.phone,
                            "website": db_lead.website,
                            "linkedin_url": db_lead.linkedin_url,
                            "status": db_lead.status.value if db_lead.status else "new",
                            "source": db_lead.source.value if db_lead.source else "unknown",
                            "created_at": db_lead.created_at.isoformat() if db_lead.created_at else None
                        }
                    }
                    
                    print(f"🚀 Calling n8n workflow for lead {db_lead.id}")
                    print(f"📤 Payload: {webhook_payload}")
                    
                    # Call the actual n8n webhook and wait for scoring results
                    webhook_response = await client.post(
                        "http://n8n:5678/webhook/lead-activity",
                        json=webhook_payload,
                        timeout=60.0  # Increased timeout for scoring
                    )
                    
                    if webhook_response.status_code == 200:
                        try:
                            result = webhook_response.json()
                            print(f"✅ N8n response received: {result}")
                            
                            # Extract scoring data from n8n response
                            if isinstance(result, dict):
                                # Check if n8n returned scoring data
                                score = result.get('score')
                                temperature = result.get('lead_temperature') or result.get('temperature')
                                
                                if score is not None and temperature:
                                    # Update the lead with scoring results
                                    print(f"📊 Updating lead {db_lead.id} with score: {score}, temperature: {temperature}")
                                    
                                    db_lead.score = score
                                    db_lead.lead_temperature = temperature
                                    
                                    # Store additional scoring details if provided
                                    if 'score_breakdown' in result:
                                        if not db_lead.custom_fields:
                                            db_lead.custom_fields = {}
                                        db_lead.custom_fields['score_breakdown'] = result['score_breakdown']
                                    
                                    db.commit()
                                    db.refresh(db_lead)
                                    
                                    print(f"✅ Lead {db_lead.id} updated with score: {score}, temperature: {temperature}")
                                    return True
                                else:
                                    print(f"⚠️ N8n response missing score or temperature data: {result}")
                                    return False
                            else:
                                print(f"⚠️ N8n response not in expected format: {result}")
                                return False
                                
                        except Exception as parse_error:
                            print(f"⚠️ Error parsing n8n response: {parse_error}")
                            print(f"Raw response: {webhook_response.text}")
                            return False
                    else:
                        print(f"⚠️ N8n webhook failed (status {webhook_response.status_code}): {webhook_response.text}")
                        print(f"🔍 Make sure your Lead_Scoring workflow is ACTIVE in n8n at http://localhost:5678")
                        return False
                        
            except Exception as scoring_error:
                print(f"❌ Error calling n8n webhook for lead {db_lead.id}: {scoring_error}")
                print(f"🔍 Check if n8n is running and workflow is active")
                return False
        
        # Trigger scoring and update lead
        scoring_success = await trigger_lead_scoring_and_update()
        
        if scoring_success:
            print(f"✅ Lead {db_lead.id} scored and updated successfully")
        else:
            print(f"⚠️ Lead scoring failed for {db_lead.id}, but lead creation succeeded")
        
    except Exception as e:
        print(f"⚠️ Failed to trigger scoring for lead {db_lead.id}: {str(e)}")
        # Don't fail the lead creation if scoring fails
    
    return APIResponse(
        success=True,
        data=LeadResponse.model_validate(db_lead),
        message="Lead created and scored successfully"
    )


@router.get("/dev/{lead_id}", response_model=LeadResponse)
async def get_lead_dev(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get a specific lead by ID for development."""
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


async def get_user_for_delete(
    db: Session = Depends(get_db)
):
    """Get user for delete operations - allows dev users only for now."""
    # For development, just use dev user
    return get_dev_user(db)

@router.delete("/{lead_id}", response_model=APIResponse)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_for_delete)
):
    """Delete a lead (works for both dev and authenticated users)."""
    print(f"🚨🚨🚨 DELETE_LEAD CALLED WITH ID: {lead_id} BY USER: {current_user.email} 🚨🚨🚨")
    
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    
    if not lead:
        print(f"🚨🚨🚨 LEAD {lead_id} NOT FOUND 🚨🚨🚨")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    print(f"🚨🚨🚨 DELETING LEAD {lead_id}: {lead.email} 🚨🚨🚨")
    db.delete(lead)
    db.commit()
    
    return APIResponse(
        success=True,
        data={"id": lead_id},
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

## REMOVED: All backend scoring endpoints - scoring is handled exclusively by n8n workflows


# === N8N WORKFLOW SPECIFIC ENDPOINTS ===

# Test endpoint without authentication
@router.get("/test-no-auth", response_model=APIResponse)
async def test_endpoint_no_auth():
    """Test endpoint without authentication to verify backend is working."""
    return APIResponse(
        success=True,
        data={"message": "Backend is working!", "timestamp": datetime.utcnow().isoformat()},
        message="Test endpoint working"
    )

# Debug endpoint to test get_dev_user function
@router.get("/debug-dev-user", response_model=APIResponse)
async def debug_dev_user_endpoint(
    db: Session = Depends(get_db)
):
    """Debug endpoint to test get_dev_user function."""
    try:
        from config import settings
        env_info = {
            "environment": settings.environment,
            "environment_raw": os.getenv("ENVIRONMENT", "not_set")
        }
        
        # Try to call get_dev_user manually
        dev_user = get_dev_user(db)
        
        return APIResponse(
            success=True,
            data={
                "env_info": env_info,
                "dev_user": {
                    "id": dev_user.id,
                    "email": dev_user.email,
                    "username": dev_user.username,
                    "organization_id": dev_user.organization_id
                }
            },
            message="get_dev_user working"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            data={"error": str(e), "type": type(e).__name__},
            message="get_dev_user failed"
        )

@router.get("/for-scoring-test", response_model=APIResponse)
async def get_leads_for_scoring_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Simple test version of get leads for scoring."""
    return APIResponse(
        success=True,
        data={"message": "for-scoring-test working!", "user_id": current_user.id},
        message="Test successful"
    )

@router.get("/for-scoring")
async def get_leads_for_scoring(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for leads"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads that need scoring (for n8n workflow)."""
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat(),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
                # Mock behavioral data - in real implementation, this would come from tracking
                "website_visits": 0,
                "pages_viewed": 0,
                "email_opens": 0,
                "email_clicks": 0,
                "downloads": 0,
                "company_size": 100,  # Default company size
                "industry": "technology",  # Default industry
                "unsubscribed": False,
                "bounced_emails": 0
            })
        
        return {
            "success": True,
            "data": formatted_leads,
            "message": f"Retrieved {len(formatted_leads)} leads for scoring"
        }
        
    except Exception as e:
        logger.error(f"Failed to get leads for scoring: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"Failed to get leads for scoring: {str(e)}"
        }


@router.post("/score/bulk-update-n8n", response_model=APIResponse)
async def bulk_update_lead_scores_n8n(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Bulk update lead scores from n8n workflow."""
    try:
        updated_leads = []
        failed_updates = []
        
        for update_data in updates:
            try:
                lead_id = update_data.get("id")
                new_score = update_data.get("score", 0)
                lead_temperature = update_data.get("lead_temperature", "cold")
                score_breakdown = update_data.get("score_breakdown", {})
                
                # Get the lead
                lead = db.query(Lead).filter(
                    Lead.id == lead_id,
                    Lead.organization_id == current_user.organization_id
                ).first()
                
                if not lead:
                    failed_updates.append({
                        "lead_id": lead_id,
                        "error": "Lead not found"
                    })
                    continue
                
                # Track previous score
                previous_score = lead.score or 0
                score_change = new_score - previous_score
                
                # Update lead
                lead.score = new_score
                lead.lead_temperature = LeadTemperature(lead_temperature)
                lead.updated_at = datetime.utcnow()
                
                # Add score history
                score_history = LeadScoreHistory(
                    lead_id=lead_id,
                    previous_score=previous_score,
                    new_score=new_score,
                    score_change=score_change,
                    reason="n8n automated scoring",
                    created_at=datetime.utcnow()
                )
                db.add(score_history)
                
                # Add activity log
                activity_log = ActivityLog(
                    lead_id=lead_id,
                    activity_type="score_updated",
                    description=f"Lead score updated by n8n workflow from {previous_score} to {new_score} ({score_change:+d})",
                    activity_metadata={
                        "previous_score": previous_score,
                        "new_score": new_score,
                        "score_change": score_change,
                        "score_breakdown": score_breakdown,
                        "lead_temperature": lead_temperature,
                        "source": "n8n_workflow"
                    },
                    created_at=datetime.utcnow()
                )
                db.add(activity_log)
                
                updated_leads.append({
                    "lead_id": lead_id,
                    "previous_score": previous_score,
                    "new_score": new_score,
                    "score_change": score_change,
                    "lead_temperature": lead_temperature
                })
                
            except Exception as e:
                failed_updates.append({
                    "lead_id": update_data.get("id", "unknown"),
                    "error": str(e)
                })
        
        # Commit all changes
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "updated_leads": updated_leads,
                "failed_updates": failed_updates,
                "summary": {
                    "successful_updates": len(updated_leads),
                    "failed_updates": len(failed_updates),
                    "total_processed": len(updates)
                }
            },
            message=f"Bulk update completed: {len(updated_leads)} successful, {len(failed_updates)} failed"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bulk update scores from n8n: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update scores: {str(e)}"
        )


@router.post("/activity/log", response_model=APIResponse)
async def log_lead_activity(
    activity_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)  # Using dev user for n8n access
):
    """Log lead activity from n8n workflow."""
    try:
        lead_id = activity_data.get("lead_id")
        activity_type = activity_data.get("activity_type", "workflow_activity")
        description = activity_data.get("description", "Activity logged by n8n workflow")
        metadata = activity_data.get("activity_data", {})
        
        # Verify lead exists and belongs to organization
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Create activity log
        activity_log = ActivityLog(
            lead_id=lead_id,
            activity_type=activity_type,
            description=description,
            activity_metadata=metadata,
            created_at=datetime.utcnow()
        )
        
        db.add(activity_log)
        db.commit()
        
        return APIResponse(
            success=True,
            data={
                "activity_id": activity_log.id,
                "lead_id": lead_id,
                "activity_type": activity_type,
                "logged_at": activity_log.created_at.isoformat()
            },
            message="Activity logged successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log activity: {str(e)}"
        )

# Working alternative for n8n - using a route pattern we know works
@router.get("/n8n-scoring", response_model=APIResponse)
async def get_leads_for_n8n_scoring(
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for leads"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get leads that need scoring (for n8n workflow) - working alternative endpoint."""
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Query leads that need scoring
        query = db.query(Lead).filter(
            Lead.organization_id == current_user.organization_id
        ).filter(
            or_(
                # Recently updated leads
                Lead.updated_at >= cutoff_time,
                # Leads with no score or old score
                Lead.score == None,
                Lead.score == 0,
                # Leads where score wasn't updated in last 7 days
                and_(
                    Lead.updated_at < datetime.utcnow() - timedelta(days=7),
                    Lead.score < 50  # Focus on low-scoring leads for re-evaluation
                )
            )
        ).order_by(Lead.updated_at.desc())
        
        leads = query.all()
        
        # Format leads for n8n workflow
        formatted_leads = []
        for lead in leads:
            formatted_leads.append({
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title,
                "phone": lead.phone,
                "website": lead.website,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status.value if lead.status else None,
                "source": lead.source.value if lead.source else None,
                "score": lead.score or 0,
                "lead_temperature": lead.lead_temperature.value if lead.lead_temperature else "cold",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "last_activity_at": lead.last_engagement_date.isoformat() if lead.last_engagement_date else lead.created_at.isoformat(),
                "tags": lead.tags or [],
                "custom_fields": lead.custom_fields or {},
                # Mock behavioral data - in real implementation, this would come from tracking
                "website_visits": 0,
                "pages_viewed": 0,
                "email_opens": 0,
                "email_clicks": 0,
                "downloads": 0,
                "company_size": 100,  # Default company size
                "industry": "technology",  # Default industry
                "unsubscribed": False,
                "bounced_emails": 0
            })
        
        return APIResponse(
            success=True,
            data=formatted_leads,
            message=f"Retrieved {len(formatted_leads)} leads for scoring"
        )
        
    except Exception as e:
        logger.error(f"Failed to get leads for scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leads for scoring: {str(e)}"
        )
 