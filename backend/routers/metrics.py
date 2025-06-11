"""
SaaS Metrics API endpoints for dashboard analytics.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case, distinct

from database import get_db
from models import (
    Lead, User, Organization, Communication, Campaign, CampaignLead,
    LeadStatus, LeadSource, CommunicationType, CommunicationDirection,
    CampaignStatus, ActivityLog, LeadScoreHistory
)
from schemas import APIResponse
from routers.auth import get_current_active_user, get_dev_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


# Development endpoints - no auth required
@router.get("/dev/dashboard", response_model=APIResponse)
async def get_dashboard_metrics_dev(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back for metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get comprehensive dashboard metrics for development."""
    # Duplicate the logic from get_dashboard_metrics since we can't call it directly
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not assigned to any organization"
        )
    
    # Base query for leads in the organization
    leads_query = db.query(Lead).filter(Lead.organization_id == org_id)
    
    # Total leads
    total_leads = leads_query.count()
    
    # New leads in period
    new_leads = leads_query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).count()
    
    # Leads by status
    leads_by_status = db.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.organization_id == org_id
    ).group_by(Lead.status).all()
    
    # Conversion metrics
    qualified_leads = leads_query.filter(
        Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.PROPOSAL, LeadStatus.NEGOTIATION, LeadStatus.CLOSED_WON])
    ).count()
    
    won_leads = leads_query.filter(Lead.status == LeadStatus.CLOSED_WON).count()
    lost_leads = leads_query.filter(Lead.status == LeadStatus.CLOSED_LOST).count()
    
    # Calculate conversion rates
    qualification_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
    win_rate = (won_leads / (won_leads + lost_leads) * 100) if (won_leads + lost_leads) > 0 else 0
    
    return APIResponse(
        success=True,
        data={
            "overview": {
                "total_leads": total_leads,
                "new_leads": new_leads,
                "qualified_leads": qualified_leads,
                "won_leads": won_leads,
                "lost_leads": lost_leads,
                "qualification_rate": round(qualification_rate, 2),
                "win_rate": round(win_rate, 2),
                "total_revenue": 0,
                "avg_deal_size": 0,
                "deals_count": 0,
                "total_activities": 0,
                "period_days": days_back
            },
            "lead_distribution": {
                "by_status": [{"status": item.status.value, "count": item.count} for item in leads_by_status],
                "by_source": [
                    {"source": "Website", "count": max(1, int(total_leads * 0.4))},
                    {"source": "Email", "count": max(1, int(total_leads * 0.25))},
                    {"source": "Phone", "count": max(1, int(total_leads * 0.25))},
                    {"source": "Social", "count": max(1, total_leads - max(1, int(total_leads * 0.4)) - max(1, int(total_leads * 0.25)) - max(1, int(total_leads * 0.25)))}
                ]
            },
            "time_series": {
                "daily_leads": [
                    {"date": "2024-01-01", "count": max(1, int(total_leads * 0.15))},
                    {"date": "2024-01-02", "count": max(1, int(total_leads * 0.25))},
                    {"date": "2024-01-03", "count": max(1, int(total_leads * 0.1))},
                    {"date": "2024-01-04", "count": max(1, int(total_leads * 0.3))},
                    {"date": "2024-01-05", "count": max(1, total_leads - max(1, int(total_leads * 0.15)) - max(1, int(total_leads * 0.25)) - max(1, int(total_leads * 0.1)) - max(1, int(total_leads * 0.3)))}
                ],
                "score_trend": [
                    {"date": "2024-01-01", "avg_score": 65.2},
                    {"date": "2024-01-02", "avg_score": 68.5},
                    {"date": "2024-01-03", "avg_score": 72.1},
                    {"date": "2024-01-04", "avg_score": 69.8},
                    {"date": "2024-01-05", "avg_score": 74.3}
                ]
            },
            "score_analytics": {
                "avg_score": 69.8,
                "max_score": 95.5,
                "min_score": 45.2
            },
            "communication_metrics": {
                "total_communications": 156,
                "outbound_count": 89,
                "inbound_count": 67
            },
            "team_performance": [
                {"user_id": 1, "name": "John Doe", "leads_assigned": 15, "leads_won": 8, "revenue_generated": 24000, "win_rate": 53.3},
                {"user_id": 2, "name": "Jane Smith", "leads_assigned": 12, "leads_won": 5, "revenue_generated": 18000, "win_rate": 41.7}
            ],
            "campaign_performance": [
                {"campaign_id": 1, "name": "Q1 Email Campaign", "status": "active", "total_leads": 45, "converted_leads": 12, "conversion_rate": 26.7, "budget_allocated": 5000, "budget_spent": 3200, "budget_utilization": 64.0}
            ]
        }
    )


@router.get("/dev/revenue", response_model=APIResponse)
async def get_revenue_metrics_dev(
    days_back: int = Query(90, ge=1, le=365, description="Number of days to look back"),
    group_by: str = Query("month", regex="^(day|week|month)$", description="Grouping period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get revenue metrics for development."""
    return APIResponse(
        success=True,
        data={
            "revenue_trend": [
                {"period": "2024-01", "revenue": 15000, "deals_count": 5, "avg_deal_size": 3000},
                {"period": "2024-02", "revenue": 22000, "deals_count": 8, "avg_deal_size": 2750},
                {"period": "2024-03", "revenue": 18000, "deals_count": 6, "avg_deal_size": 3000},
                {"period": "2024-04", "revenue": 28000, "deals_count": 10, "avg_deal_size": 2800},
                {"period": "2024-05", "revenue": 35000, "deals_count": 12, "avg_deal_size": 2917}
            ],
            "revenue_by_source": [
                {"source": "Website", "revenue": 45000, "deals_count": 15},
                {"source": "Email", "revenue": 28000, "deals_count": 8},
                {"source": "Phone", "revenue": 52000, "deals_count": 18},
                {"source": "Social", "revenue": 12000, "deals_count": 4}
            ],
            "growth_rate": 15.7,
            "total_revenue": 137000,
            "group_by": group_by,
            "period_days": days_back
        }
    )


@router.get("/dev/funnel", response_model=APIResponse)
async def get_funnel_metrics_dev(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Get funnel metrics for development."""
    # Use realistic test data that matches the overview (14 leads)
    total_leads = 14  # Consistent with dashboard overview
    
    # Calculate funnel stages based on realistic proportions  
    qualified_count = max(1, int(total_leads * 0.45))  # 45% qualification rate = 6 leads
    proposal_count = max(1, int(qualified_count * 0.5))  # 50% of qualified move to proposal = 3 leads  
    closed_won_count = max(1, int(proposal_count * 0.67))  # 67% of proposals close-win = 2 leads
    
    return APIResponse(
        success=True,
        data={
            "funnel_stages": [
                { "stage": "Leads", "count": total_leads, "conversion_rate": 100.0, "stage_conversion": 100.0 },
                { "stage": "Qualified", "count": qualified_count, "conversion_rate": round((qualified_count / total_leads) * 100, 1), "stage_conversion": 45.0 },
                { "stage": "Proposal", "count": proposal_count, "conversion_rate": round((proposal_count / total_leads) * 100, 1), "stage_conversion": round((proposal_count / qualified_count) * 100, 1) },
                { "stage": "Closed Won", "count": closed_won_count, "conversion_rate": round((closed_won_count / total_leads) * 100, 1), "stage_conversion": round((closed_won_count / proposal_count) * 100, 1) }
            ],
            "total_leads": total_leads,
            "period_days": days_back
        }
    )


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard_metrics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back for metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard metrics for the organization."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not assigned to any organization"
        )
    
    # Base query for leads in the organization
    leads_query = db.query(Lead).filter(Lead.organization_id == org_id)
    
    # Total leads
    total_leads = leads_query.count()
    
    # New leads in period
    new_leads = leads_query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).count()
    
    # Leads by status
    leads_by_status = db.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.organization_id == org_id
    ).group_by(Lead.status).all()
    
    # Leads by source
    leads_by_source = db.query(
        Lead.source,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.organization_id == org_id
    ).group_by(Lead.source).all()
    
    # Conversion metrics
    qualified_leads = leads_query.filter(
        Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.PROPOSAL, LeadStatus.NEGOTIATION, LeadStatus.CLOSED_WON])
    ).count()
    
    won_leads = leads_query.filter(Lead.status == LeadStatus.CLOSED_WON).count()
    lost_leads = leads_query.filter(Lead.status == LeadStatus.CLOSED_LOST).count()
    
    # Calculate conversion rates
    qualification_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
    win_rate = (won_leads / (won_leads + lost_leads) * 100) if (won_leads + lost_leads) > 0 else 0
    
    # Revenue metrics (using lead value field)
    revenue_data = db.query(
        func.sum(Lead.value).label('total_revenue'),
        func.avg(Lead.value).label('avg_deal_size'),
        func.count(Lead.id).label('deals_count')
    ).filter(
        Lead.organization_id == org_id,
        Lead.status == LeadStatus.CLOSED_WON,
        Lead.value.isnot(None)
    ).first()
    
    total_revenue = (revenue_data.total_revenue or 0) / 100  # Convert from cents to dollars
    avg_deal_size = (revenue_data.avg_deal_size or 0) / 100
    deals_count = revenue_data.deals_count or 0
    
    # Lead score analytics
    score_analytics = db.query(
        func.avg(Lead.score).label('avg_score'),
        func.max(Lead.score).label('max_score'),
        func.min(Lead.score).label('min_score')
    ).filter(Lead.organization_id == org_id).first()
    
    # Activity metrics
    total_activities = db.query(ActivityLog).filter(
        ActivityLog.created_at >= start_date,
        ActivityLog.created_at <= end_date
    ).join(Lead).filter(Lead.organization_id == org_id).count()
    
    # Communication metrics
    communications_data = db.query(
        func.count(Communication.id).label('total_communications'),
        func.count(case((Communication.direction == CommunicationDirection.OUTBOUND, 1))).label('outbound_count'),
        func.count(case((Communication.direction == CommunicationDirection.INBOUND, 1))).label('inbound_count')
    ).filter(
        Communication.created_at >= start_date,
        Communication.created_at <= end_date
    ).join(Lead).filter(Lead.organization_id == org_id).first()
    
    # Time-series data for charts (daily data for the period)
    daily_leads = db.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.organization_id == org_id,
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(func.date(Lead.created_at)).order_by(func.date(Lead.created_at)).all()
    
    # Lead score trend
    score_trend = db.query(
        func.date(LeadScoreHistory.created_at).label('date'),
        func.avg(LeadScoreHistory.new_score).label('avg_score')
    ).filter(
        LeadScoreHistory.created_at >= start_date,
        LeadScoreHistory.created_at <= end_date
    ).join(Lead).filter(Lead.organization_id == org_id).group_by(
        func.date(LeadScoreHistory.created_at)
    ).order_by(func.date(LeadScoreHistory.created_at)).all()
    
    # Team performance metrics
    team_performance = db.query(
        User.id,
        User.first_name,
        User.last_name,
        func.count(Lead.id).label('leads_assigned'),
        func.count(case((Lead.status == LeadStatus.CLOSED_WON, 1))).label('leads_won'),
        func.sum(case((Lead.status == LeadStatus.CLOSED_WON, Lead.value), else_=0)).label('revenue_generated')
    ).outerjoin(Lead, User.id == Lead.assigned_to_id).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).group_by(User.id, User.first_name, User.last_name).all()
    
    # Campaign performance
    campaign_performance = db.query(
        Campaign.id,
        Campaign.name,
        Campaign.status,
        func.count(CampaignLead.id).label('total_leads'),
        func.count(case((CampaignLead.status == 'converted', 1))).label('converted_leads'),
        Campaign.budget_allocated,
        Campaign.budget_spent
    ).outerjoin(CampaignLead, Campaign.id == CampaignLead.campaign_id).filter(
        Campaign.organization_id == org_id
    ).group_by(
        Campaign.id, Campaign.name, Campaign.status, 
        Campaign.budget_allocated, Campaign.budget_spent
    ).all()
    
    return APIResponse(
        success=True,
        data={
            "overview": {
                "total_leads": total_leads,
                "new_leads": new_leads,
                "qualified_leads": qualified_leads,
                "won_leads": won_leads,
                "lost_leads": lost_leads,
                "qualification_rate": round(qualification_rate, 2),
                "win_rate": round(win_rate, 2),
                "total_revenue": round(total_revenue, 2),
                "avg_deal_size": round(avg_deal_size, 2),
                "deals_count": deals_count,
                "total_activities": total_activities,
                "period_days": days_back
            },
            "lead_distribution": {
                "by_status": [{"status": item.status.value, "count": item.count} for item in leads_by_status],
                "by_source": [{"source": item.source.value, "count": item.count} for item in leads_by_source]
            },
            "score_analytics": {
                "avg_score": round(score_analytics.avg_score or 0, 2),
                "max_score": score_analytics.max_score or 0,
                "min_score": score_analytics.min_score or 0
            },
            "communication_metrics": {
                "total_communications": communications_data.total_communications or 0,
                "outbound_count": communications_data.outbound_count or 0,
                "inbound_count": communications_data.inbound_count or 0
            },
            "time_series": {
                "daily_leads": [
                    {"date": item.date.isoformat(), "count": item.count} 
                    for item in daily_leads
                ],
                "score_trend": [
                    {"date": item.date.isoformat(), "avg_score": round(item.avg_score, 2)} 
                    for item in score_trend
                ]
            },
            "team_performance": [
                {
                    "user_id": item.id,
                    "name": f"{item.first_name} {item.last_name}",
                    "leads_assigned": item.leads_assigned,
                    "leads_won": item.leads_won,
                    "revenue_generated": round((item.revenue_generated or 0) / 100, 2),
                    "win_rate": round((item.leads_won / item.leads_assigned * 100) if item.leads_assigned > 0 else 0, 2)
                }
                for item in team_performance
            ],
            "campaign_performance": [
                {
                    "campaign_id": item.id,
                    "name": item.name,
                    "status": item.status.value,
                    "total_leads": item.total_leads,
                    "converted_leads": item.converted_leads,
                    "conversion_rate": round((item.converted_leads / item.total_leads * 100) if item.total_leads > 0 else 0, 2),
                    "budget_allocated": round((item.budget_allocated or 0) / 100, 2),
                    "budget_spent": round((item.budget_spent or 0) / 100, 2),
                    "budget_utilization": round((item.budget_spent / item.budget_allocated * 100) if item.budget_allocated and item.budget_allocated > 0 else 0, 2)
                }
                for item in campaign_performance
            ]
        },
        message="Dashboard metrics retrieved successfully"
    )


@router.get("/revenue", response_model=APIResponse)
async def get_revenue_metrics(
    days_back: int = Query(90, ge=1, le=365, description="Number of days to look back"),
    group_by: str = Query("month", regex="^(day|week|month)$", description="Grouping period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed revenue metrics and trends."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not assigned to any organization"
        )
    
    # Determine grouping function based on group_by parameter
    if group_by == "day":
        date_trunc = func.date(Lead.updated_at)
    elif group_by == "week":
        date_trunc = func.date_trunc('week', Lead.updated_at)
    else:  # month
        date_trunc = func.date_trunc('month', Lead.updated_at)
    
    # Revenue over time
    revenue_trend = db.query(
        date_trunc.label('period'),
        func.sum(Lead.value).label('revenue'),
        func.count(Lead.id).label('deals_count'),
        func.avg(Lead.value).label('avg_deal_size')
    ).filter(
        Lead.organization_id == org_id,
        Lead.status == LeadStatus.CLOSED_WON,
        Lead.updated_at >= start_date,
        Lead.updated_at <= end_date,
        Lead.value.isnot(None)
    ).group_by(date_trunc).order_by(date_trunc).all()
    
    # Revenue by source
    revenue_by_source = db.query(
        Lead.source,
        func.sum(Lead.value).label('revenue'),
        func.count(Lead.id).label('deals_count')
    ).filter(
        Lead.organization_id == org_id,
        Lead.status == LeadStatus.CLOSED_WON,
        Lead.value.isnot(None)
    ).group_by(Lead.source).all()
    
    return APIResponse(
        success=True,
        data={
            "revenue_trend": [
                {
                    "period": item.period.isoformat() if hasattr(item.period, 'isoformat') else str(item.period),
                    "revenue": round((item.revenue or 0) / 100, 2),
                    "deals_count": item.deals_count,
                    "avg_deal_size": round((item.avg_deal_size or 0) / 100, 2)
                }
                for item in revenue_trend
            ],
            "revenue_by_source": [
                {
                    "source": item.source.value,
                    "revenue": round((item.revenue or 0) / 100, 2),
                    "deals_count": item.deals_count
                }
                for item in revenue_by_source
            ],
            "group_by": group_by,
            "period_days": days_back
        },
        message="Revenue metrics retrieved successfully"
    )


@router.get("/funnel", response_model=APIResponse)
async def get_funnel_metrics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales funnel metrics and conversion rates."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not assigned to any organization"
        )
    
    # Funnel stages with counts
    funnel_data = db.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.organization_id == org_id,
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(Lead.status).all()
    
    # Create ordered funnel stages
    funnel_order = [
        LeadStatus.NEW,
        LeadStatus.CONTACTED,
        LeadStatus.QUALIFIED,
        LeadStatus.PROPOSAL,
        LeadStatus.NEGOTIATION,
        LeadStatus.CLOSED_WON,
        LeadStatus.CLOSED_LOST
    ]
    
    funnel_counts = {item.status: item.count for item in funnel_data}
    
    # Calculate conversion rates between stages
    funnel_stages = []
    total_leads = sum(funnel_counts.values())
    
    for i, stage in enumerate(funnel_order):
        count = funnel_counts.get(stage, 0)
        conversion_rate = (count / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate stage-to-stage conversion
        if i > 0:
            prev_stage_count = funnel_counts.get(funnel_order[i-1], 0)
            stage_conversion = (count / prev_stage_count * 100) if prev_stage_count > 0 else 0
        else:
            stage_conversion = 100.0
        
        funnel_stages.append({
            "stage": stage.value,
            "count": count,
            "conversion_rate": round(conversion_rate, 2),
            "stage_conversion": round(stage_conversion, 2)
        })
    
    return APIResponse(
        success=True,
        data={
            "funnel_stages": funnel_stages,
            "total_leads": total_leads,
            "period_days": days_back
        },
        message="Funnel metrics retrieved successfully"
    ) 