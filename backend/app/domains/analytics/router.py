"""
Analytics Domain Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.database import get_db
from .schemas import (
    Integration, IntegrationCreate, IntegrationUpdate,
    AnalyticsReport, AnalyticsReportCreate,
    LeadAnalytics, CampaignAnalytics, WorkflowAnalytics, DashboardAnalytics
)
from .services import IntegrationService, AnalyticsService

router = APIRouter()

# Integration endpoints
@router.get("/integrations/", response_model=List[Integration])
def get_integrations(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    integration_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all integrations with optional filtering."""
    service = IntegrationService(db)
    return service.get_integrations(
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        integration_type=integration_type,
        is_active=is_active
    )


@router.get("/integrations/{integration_id}", response_model=Integration)
def get_integration(integration_id: int, db: Session = Depends(get_db)):
    """Get a specific integration by ID."""
    service = IntegrationService(db)
    integration = service.get_integration(integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    return integration


@router.post("/integrations/", response_model=Integration, status_code=status.HTTP_201_CREATED)
def create_integration(integration: IntegrationCreate, db: Session = Depends(get_db)):
    """Create a new integration."""
    service = IntegrationService(db)
    return service.create_integration(integration)


@router.put("/integrations/{integration_id}", response_model=Integration)
def update_integration(
    integration_id: int,
    integration_update: IntegrationUpdate,
    db: Session = Depends(get_db)
):
    """Update an integration."""
    service = IntegrationService(db)
    integration = service.update_integration(integration_id, integration_update)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    return integration


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(integration_id: int, db: Session = Depends(get_db)):
    """Delete an integration."""
    service = IntegrationService(db)
    if not service.delete_integration(integration_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )


# Analytics endpoints
@router.get("/dashboard/{organization_id}", response_model=DashboardAnalytics)
def get_dashboard_analytics(
    organization_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard analytics for an organization."""
    service = AnalyticsService(db)
    return service.get_dashboard_analytics(organization_id, days)


@router.get("/leads/{organization_id}", response_model=LeadAnalytics)
def get_lead_analytics(
    organization_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get lead analytics for an organization."""
    service = AnalyticsService(db)
    return service.get_lead_analytics(organization_id, days)


@router.get("/campaigns/{organization_id}", response_model=CampaignAnalytics)
def get_campaign_analytics(
    organization_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get campaign analytics for an organization."""
    service = AnalyticsService(db)
    return service.get_campaign_analytics(organization_id, days)


@router.get("/workflows/{organization_id}", response_model=WorkflowAnalytics)
def get_workflow_analytics(
    organization_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get workflow analytics for an organization."""
    service = AnalyticsService(db)
    return service.get_workflow_analytics(organization_id, days)


# Reports endpoints
@router.get("/reports/", response_model=List[AnalyticsReport])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get analytics reports with optional filtering."""
    service = AnalyticsService(db)
    return service.get_reports(
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        report_type=report_type
    )


@router.post("/reports/", response_model=AnalyticsReport, status_code=status.HTTP_201_CREATED)
def create_report(report: AnalyticsReportCreate, db: Session = Depends(get_db)):
    """Create a new analytics report."""
    service = AnalyticsService(db)
    return service.create_report(report)