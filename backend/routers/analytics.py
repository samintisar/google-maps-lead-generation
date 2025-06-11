"""
Advanced Analytics API endpoints for complex calculations and data science operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models import User, Lead
from routers.auth import get_current_active_user, get_dev_user
from schemas import APIResponse
from services.analytics.analytics_service import AdvancedAnalyticsService
from automation.engine import AutomationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["advanced-analytics"])

# Pydantic models for request/response
class StatisticalAnalysisRequest(BaseModel):
    analysis_type: str = Field(default="comprehensive", description="Type of analysis: comprehensive, correlation, trend, or descriptive")
    custom_datasets: Optional[Dict[str, List[float]]] = Field(default=None, description="Custom datasets for analysis")

class ConversionPredictionRequest(BaseModel):
    lead_ids: List[int] = Field(description="List of lead IDs to analyze")
    model_type: str = Field(default="random_forest", description="ML model type: random_forest or logistic_regression")

class LifecycleAnalysisRequest(BaseModel):
    cohort_period: str = Field(default="month", description="Cohort period: week, month, or quarter")
    include_predictions: bool = Field(default=True, description="Include predictive analytics")

class AdvancedMetricsRequest(BaseModel):
    metric_types: Optional[List[str]] = Field(
        default=None, 
        description="Metric types to calculate: conversion_funnel, engagement_analytics, performance_metrics, predictive_scores"
    )

# Development endpoints (no auth required)
@router.post("/dev/comprehensive-report", response_model=APIResponse)
async def generate_comprehensive_report_dev(
    days_back: int = Query(90, ge=1, le=365, description="Days of historical data to analyze"),
    lead_ids: Optional[List[int]] = Body(default=None, description="Specific lead IDs to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Generate a comprehensive analytics report with all available analyses."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        # Initialize analytics service
        analytics_service = AdvancedAnalyticsService(db)
        
        # Generate comprehensive report
        report = await analytics_service.generate_comprehensive_analytics_report(
            organization_id=org_id,
            lead_ids=lead_ids,
            days_back=days_back
        )
        
        return APIResponse(
            success=True,
            data={
                "report": report,
                "execution_time": "Generated successfully",
                "organization_id": org_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics report: {str(e)}"
        )

@router.post("/dev/statistical-analysis", response_model=APIResponse)
async def perform_statistical_analysis_dev(
    request: StatisticalAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Perform comprehensive statistical analysis on organizational data."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        results = await analytics_service.perform_statistical_analysis(
            organization_id=org_id,
            analysis_type=request.analysis_type,
            custom_datasets=request.custom_datasets
        )
        
        return APIResponse(
            success=True,
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error performing statistical analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistical analysis failed: {str(e)}"
        )

@router.post("/dev/conversion-predictions", response_model=APIResponse)
async def predict_lead_conversions_dev(
    request: ConversionPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Predict conversion probabilities for specified leads using machine learning."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        # Validate lead IDs belong to the organization
        valid_leads = db.query(Lead.id).filter(
            Lead.id.in_(request.lead_ids),
            Lead.organization_id == org_id
        ).all()
        
        valid_lead_ids = [lead.id for lead in valid_leads]
        
        if not valid_lead_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid leads found for the provided IDs"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        predictions = await analytics_service.analyze_lead_conversion_probability(
            lead_ids=valid_lead_ids,
            model_type=request.model_type
        )
        
        return APIResponse(
            success=True,
            data={
                "predictions": predictions,
                "model_type": request.model_type,
                "total_leads_analyzed": len(predictions),
                "requested_leads": len(request.lead_ids),
                "valid_leads": len(valid_lead_ids)
            }
        )
        
    except Exception as e:
        logger.error(f"Error predicting lead conversions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion prediction failed: {str(e)}"
        )

@router.post("/dev/lifecycle-analysis", response_model=APIResponse)
async def analyze_customer_lifecycle_dev(
    request: LifecycleAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Comprehensive customer lifecycle analysis including cohorts and behavioral segments."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        analysis = await analytics_service.analyze_customer_lifecycle(
            organization_id=org_id,
            cohort_period=request.cohort_period,
            include_predictions=request.include_predictions
        )
        
        return APIResponse(
            success=True,
            data=analysis
        )
        
    except Exception as e:
        logger.error(f"Error analyzing customer lifecycle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lifecycle analysis failed: {str(e)}"
        )

@router.post("/dev/advanced-metrics", response_model=APIResponse)
async def calculate_advanced_metrics_dev(
    request: AdvancedMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Calculate advanced metrics using complex mathematical operations."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        metrics = await analytics_service.calculate_advanced_metrics(
            organization_id=org_id,
            metric_types=request.metric_types
        )
        
        return APIResponse(
            success=True,
            data={
                "metrics": metrics,
                "organization_id": org_id,
                "calculated_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating advanced metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced metrics calculation failed: {str(e)}"
        )

@router.get("/dev/correlation-analysis", response_model=APIResponse)
async def analyze_correlations_dev(
    variables: List[str] = Query(
        default=["lead_scores", "communication_counts", "days_in_pipeline"],
        description="Variables to analyze for correlations"
    ),
    method: str = Query(default="pearson", description="Correlation method: pearson or spearman"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Analyze correlations between specified variables."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        # Perform correlation analysis
        analysis_result = await analytics_service.perform_statistical_analysis(
            organization_id=org_id,
            analysis_type="correlation"
        )
        
        # Extract correlation results
        correlations = analysis_result.get("results", {}).get("correlations", {})
        
        # Filter by requested variables if specified
        filtered_correlations = {}
        for corr_name, corr_data in correlations.items():
            # Check if correlation involves requested variables
            if any(var in corr_name for var in variables):
                filtered_correlations[corr_name] = corr_data
        
        return APIResponse(
            success=True,
            data={
                "correlations": filtered_correlations,
                "method": method,
                "variables_analyzed": variables,
                "total_correlations_found": len(filtered_correlations)
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing correlations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Correlation analysis failed: {str(e)}"
        )

@router.get("/dev/trend-analysis", response_model=APIResponse)
async def analyze_trends_dev(
    trend_type: str = Query(
        default="lead_scores",
        description="Type of trend to analyze: lead_scores, lead_creation, conversions"
    ),
    days_back: int = Query(90, ge=7, le=365, description="Days of historical data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_dev_user)
):
    """Analyze trends in organizational data over time."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        # Perform trend analysis
        analysis_result = await analytics_service.perform_statistical_analysis(
            organization_id=org_id,
            analysis_type="trend"
        )
        
        trends = analysis_result.get("results", {}).get("trends", {})
        
        # Filter by requested trend type
        filtered_trends = {}
        if trend_type == "lead_scores" and "lead_score_trend" in trends:
            filtered_trends["lead_score_trend"] = trends["lead_score_trend"]
        elif trend_type == "lead_creation" and "lead_creation_trend" in trends:
            filtered_trends["lead_creation_trend"] = trends["lead_creation_trend"]
        else:
            filtered_trends = trends  # Return all trends
        
        return APIResponse(
            success=True,
            data={
                "trends": filtered_trends,
                "trend_type": trend_type,
                "days_analyzed": days_back,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )

# Production endpoints (require authentication)
@router.post("/comprehensive-report", response_model=APIResponse)
async def generate_comprehensive_report(
    days_back: int = Query(90, ge=1, le=365, description="Days of historical data to analyze"),
    lead_ids: Optional[List[int]] = Body(default=None, description="Specific lead IDs to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a comprehensive analytics report with all available analyses."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        # Initialize analytics service with automation engine if available
        try:
            automation_engine = AutomationEngine()
            analytics_service = AdvancedAnalyticsService(db, automation_engine)
        except Exception:
            # Fallback without automation engine
            analytics_service = AdvancedAnalyticsService(db)
        
        # Generate comprehensive report
        report = await analytics_service.generate_comprehensive_analytics_report(
            organization_id=org_id,
            lead_ids=lead_ids,
            days_back=days_back
        )
        
        return APIResponse(
            success=True,
            data={
                "report": report,
                "execution_time": "Generated successfully",
                "organization_id": org_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics report: {str(e)}"
        )

@router.post("/statistical-analysis", response_model=APIResponse)
async def perform_statistical_analysis(
    request: StatisticalAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform comprehensive statistical analysis on organizational data."""
    try:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to any organization"
            )
        
        analytics_service = AdvancedAnalyticsService(db)
        
        results = await analytics_service.perform_statistical_analysis(
            organization_id=org_id,
            analysis_type=request.analysis_type,
            custom_datasets=request.custom_datasets
        )
        
        return APIResponse(
            success=True,
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error performing statistical analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistical analysis failed: {str(e)}"
        ) 