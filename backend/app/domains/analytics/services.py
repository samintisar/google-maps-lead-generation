"""
Analytics Domain Services.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import Integration, AnalyticsReport
from .schemas import (
    IntegrationCreate, IntegrationUpdate, AnalyticsReportCreate,
    LeadAnalytics, CampaignAnalytics, WorkflowAnalytics, DashboardAnalytics
)


class IntegrationService:
    """Service for integration management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_integrations(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        integration_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Integration]:
        """Get integrations with optional filtering."""
        query = self.db.query(Integration)
        
        if organization_id:
            query = query.filter(Integration.organization_id == organization_id)
        
        if integration_type:
            query = query.filter(Integration.type == integration_type)
        
        if is_active is not None:
            query = query.filter(Integration.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_integration(self, integration_id: int) -> Optional[Integration]:
        """Get a specific integration by ID."""
        return self.db.query(Integration).filter(Integration.id == integration_id).first()
    
    def create_integration(self, integration_data: IntegrationCreate) -> Integration:
        """Create a new integration."""
        db_integration = Integration(**integration_data.dict())
        self.db.add(db_integration)
        self.db.commit()
        self.db.refresh(db_integration)
        return db_integration
    
    def update_integration(self, integration_id: int, integration_data: IntegrationUpdate) -> Optional[Integration]:
        """Update an integration."""
        integration = self.get_integration(integration_id)
        if not integration:
            return None
        
        update_data = integration_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(integration, field, value)
        
        self.db.commit()
        self.db.refresh(integration)
        return integration
    
    def delete_integration(self, integration_id: int) -> bool:
        """Delete an integration."""
        integration = self.get_integration(integration_id)
        if not integration:
            return False
        
        self.db.delete(integration)
        self.db.commit()
        return True


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_lead_analytics(self, organization_id: int, days: int = 30) -> LeadAnalytics:
        """Get lead analytics for the specified period."""
        # Import here to avoid circular imports
        from app.domains.lead_management.models import Lead, Activity
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total leads
        total_leads = self.db.query(func.count(Lead.id)).filter(
            Lead.organization_id == organization_id
        ).scalar()
        
        # New leads in period
        new_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.created_at >= start_date
            )
        ).scalar()
        
        # Qualified leads (assuming status 'qualified')
        qualified_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == 'qualified'
            )
        ).scalar()
        
        # Converted leads (assuming status 'converted')
        converted_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == 'converted'
            )
        ).scalar()
        
        # Conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
        
        # Average score
        avg_score = self.db.query(func.avg(Lead.score)).filter(
            Lead.organization_id == organization_id
        ).scalar() or 0.0
        
        # Leads by source
        leads_by_source = {}
        source_results = self.db.query(Lead.source, func.count(Lead.id)).filter(
            Lead.organization_id == organization_id
        ).group_by(Lead.source).all()
        
        for source, count in source_results:
            leads_by_source[source or 'Unknown'] = count
        
        # Leads by status
        leads_by_status = {}
        status_results = self.db.query(Lead.status, func.count(Lead.id)).filter(
            Lead.organization_id == organization_id
        ).group_by(Lead.status).all()
        
        for status, count in status_results:
            leads_by_status[status] = count
        
        return LeadAnalytics(
            total_leads=total_leads,
            new_leads=new_leads,
            qualified_leads=qualified_leads,
            converted_leads=converted_leads,
            conversion_rate=conversion_rate,
            average_score=avg_score,
            leads_by_source=leads_by_source,
            leads_by_status=leads_by_status
        )
    
    def get_campaign_analytics(self, organization_id: int, days: int = 30) -> CampaignAnalytics:
        """Get campaign analytics for the specified period."""
        # Import here to avoid circular imports
        from app.domains.campaign_management.models import Campaign
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total campaigns
        total_campaigns = self.db.query(func.count(Campaign.id)).filter(
            Campaign.organization_id == organization_id
        ).scalar()
        
        # Active campaigns
        active_campaigns = self.db.query(func.count(Campaign.id)).filter(
            and_(
                Campaign.organization_id == organization_id,
                Campaign.status == 'active'
            )
        ).scalar()
        
        # Completed campaigns
        completed_campaigns = self.db.query(func.count(Campaign.id)).filter(
            and_(
                Campaign.organization_id == organization_id,
                Campaign.status == 'completed'
            )
        ).scalar()
        
        # Budget analytics
        total_budget = self.db.query(func.sum(Campaign.budget)).filter(
            Campaign.organization_id == organization_id
        ).scalar() or 0.0
        
        # For now, assume total spent = total budget (placeholder)
        total_spent = total_budget
        
        # Average ROI (placeholder calculation)
        average_roi = 15.5  # Placeholder
        
        # Campaigns by status
        campaigns_by_status = {}
        status_results = self.db.query(Campaign.status, func.count(Campaign.id)).filter(
            Campaign.organization_id == organization_id
        ).group_by(Campaign.status).all()
        
        for status, count in status_results:
            campaigns_by_status[status] = count
        
        return CampaignAnalytics(
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            completed_campaigns=completed_campaigns,
            total_budget=total_budget,
            total_spent=total_spent,
            average_roi=average_roi,
            campaigns_by_status=campaigns_by_status
        )
    
    def get_workflow_analytics(self, organization_id: int, days: int = 30) -> WorkflowAnalytics:
        """Get workflow analytics for the specified period."""
        # Import here to avoid circular imports
        from app.domains.workflow_execution.models import WorkflowExecution
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total executions
        total_executions = self.db.query(func.count(WorkflowExecution.id)).filter(
            and_(
                WorkflowExecution.organization_id == organization_id,
                WorkflowExecution.started_at >= start_date
            )
        ).scalar()
        
        # Successful executions
        successful_executions = self.db.query(func.count(WorkflowExecution.id)).filter(
            and_(
                WorkflowExecution.organization_id == organization_id,
                WorkflowExecution.status == 'completed',
                WorkflowExecution.started_at >= start_date
            )
        ).scalar()
        
        # Failed executions
        failed_executions = self.db.query(func.count(WorkflowExecution.id)).filter(
            and_(
                WorkflowExecution.organization_id == organization_id,
                WorkflowExecution.status == 'failed',
                WorkflowExecution.started_at >= start_date
            )
        ).scalar()
        
        # Success rate
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
        
        # Average execution time (placeholder)
        average_execution_time = 120.5  # seconds
        
        # Executions by type (placeholder - would need workflow type field)
        executions_by_type = {
            "google-maps": total_executions // 2,
            "email-campaign": total_executions // 3,
            "lead-scoring": total_executions // 6
        }
        
        # Executions by status
        executions_by_status = {}
        status_results = self.db.query(WorkflowExecution.status, func.count(WorkflowExecution.id)).filter(
            and_(
                WorkflowExecution.organization_id == organization_id,
                WorkflowExecution.started_at >= start_date
            )
        ).group_by(WorkflowExecution.status).all()
        
        for status, count in status_results:
            executions_by_status[status] = count
        
        return WorkflowAnalytics(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            executions_by_type=executions_by_type,
            executions_by_status=executions_by_status
        )
    
    def get_dashboard_analytics(self, organization_id: int, days: int = 30) -> DashboardAnalytics:
        """Get comprehensive dashboard analytics."""
        lead_analytics = self.get_lead_analytics(organization_id, days)
        campaign_analytics = self.get_campaign_analytics(organization_id, days)
        workflow_analytics = self.get_workflow_analytics(organization_id, days)
        
        # Recent activities (placeholder)
        recent_activities = [
            {
                "type": "lead_created",
                "description": "New lead added: John Doe",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "type": "workflow_completed",
                "description": "Google Maps workflow completed successfully",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return DashboardAnalytics(
            lead_analytics=lead_analytics,
            campaign_analytics=campaign_analytics,
            workflow_analytics=workflow_analytics,
            recent_activities=recent_activities
        )
    
    def create_report(self, report_data: AnalyticsReportCreate) -> AnalyticsReport:
        """Create a new analytics report."""
        db_report = AnalyticsReport(**report_data.dict())
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return db_report
    
    def get_reports(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[int] = None,
        report_type: Optional[str] = None
    ) -> List[AnalyticsReport]:
        """Get analytics reports with optional filtering."""
        query = self.db.query(AnalyticsReport)
        
        if organization_id:
            query = query.filter(AnalyticsReport.organization_id == organization_id)
        
        if report_type:
            query = query.filter(AnalyticsReport.report_type == report_type)
        
        return query.offset(skip).limit(limit).all()