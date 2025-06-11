"""
Cohort Analysis Module

Provides cohort analysis capabilities for lead lifecycle tracking,
customer retention analysis, and behavioral segmentation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract

from models import (
    Lead, Communication, LeadScoreHistory, ActivityLog, Campaign,
    CampaignLead, LeadStatus, LeadSource, Organization
)

logger = logging.getLogger(__name__)

@dataclass
class CohortMetrics:
    """Cohort analysis metrics"""
    cohort_period: str
    cohort_size: int
    retention_rates: Dict[int, float]
    conversion_rates: Dict[int, float]
    revenue_per_cohort: Dict[int, float]
    avg_time_to_conversion: float
    cohort_characteristics: Dict[str, Any]

@dataclass
class LeadLifecycleStage:
    """Lead lifecycle stage analysis"""
    stage_name: str
    avg_duration_days: float
    conversion_rate: float
    typical_activities: List[str]
    success_factors: List[str]

class CohortAnalysis:
    """
    Advanced cohort analysis for lead lifecycle and customer behavior.
    """
    
    def __init__(self, db: Session):
        """Initialize the cohort analysis engine."""
        self.db = db
    
    async def analyze_lead_cohorts(
        self,
        organization_id: int,
        cohort_period: str = "month",
        analysis_periods: int = 12
    ) -> List[CohortMetrics]:
        """
        Analyze lead cohorts based on their acquisition period.
        
        Args:
            organization_id: Organization to analyze
            cohort_period: "week", "month", or "quarter"
            analysis_periods: Number of periods to analyze
        """
        try:
            # Get all leads for the organization
            leads = self.db.query(Lead).filter(
                Lead.organization_id == organization_id
            ).order_by(Lead.created_at).all()
            
            if not leads:
                return []
            
            # Group leads into cohorts
            cohorts = self._group_leads_into_cohorts(leads, cohort_period, analysis_periods)
            
            cohort_metrics = []
            
            for cohort_key, cohort_leads in cohorts.items():
                if not cohort_leads:
                    continue
                
                # Calculate retention rates
                retention_rates = await self._calculate_retention_rates(
                    cohort_leads, cohort_period
                )
                
                # Calculate conversion rates
                conversion_rates = await self._calculate_conversion_rates(
                    cohort_leads, cohort_period
                )
                
                # Calculate revenue per cohort
                revenue_per_period = await self._calculate_cohort_revenue(
                    cohort_leads, cohort_period
                )
                
                # Calculate average time to conversion
                avg_conversion_time = self._calculate_avg_conversion_time(cohort_leads)
                
                # Analyze cohort characteristics
                characteristics = self._analyze_cohort_characteristics(cohort_leads)
                
                cohort_metrics.append(CohortMetrics(
                    cohort_period=cohort_key,
                    cohort_size=len(cohort_leads),
                    retention_rates=retention_rates,
                    conversion_rates=conversion_rates,
                    revenue_per_cohort=revenue_per_period,
                    avg_time_to_conversion=avg_conversion_time,
                    cohort_characteristics=characteristics
                ))
            
            return sorted(cohort_metrics, key=lambda x: x.cohort_period)
            
        except Exception as e:
            logger.error(f"Error analyzing lead cohorts: {e}")
            raise
    
    async def analyze_lead_lifecycle_stages(
        self,
        organization_id: int,
        minimum_leads: int = 20
    ) -> List[LeadLifecycleStage]:
        """
        Analyze typical lead lifecycle stages and their characteristics.
        """
        try:
            # Get leads with sufficient history
            leads = self.db.query(Lead).filter(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.created_at <= datetime.utcnow() - timedelta(days=7)  # At least 1 week old
                )
            ).all()
            
            if len(leads) < minimum_leads:
                raise ValueError(f"Need at least {minimum_leads} leads for lifecycle analysis")
            
            # Define lifecycle stages based on lead status progression
            stages = [
                ("New Lead", [LeadStatus.NEW]),
                ("Contacted", [LeadStatus.CONTACTED]),
                ("Qualified", [LeadStatus.QUALIFIED]),
                ("Proposal", [LeadStatus.PROPOSAL]),
                ("Negotiation", [LeadStatus.NEGOTIATION]),
                ("Closed Won", [LeadStatus.CLOSED_WON]),
                ("Closed Lost", [LeadStatus.CLOSED_LOST])
            ]
            
            stage_analysis = []
            
            for stage_name, statuses in stages:
                stage_leads = [lead for lead in leads if lead.status in statuses]
                
                if not stage_leads:
                    continue
                
                # Calculate average duration in stage
                avg_duration = await self._calculate_stage_duration(stage_leads, statuses[0])
                
                # Calculate conversion rate from this stage
                conversion_rate = await self._calculate_stage_conversion_rate(
                    organization_id, statuses[0]
                )
                
                # Identify typical activities in this stage
                typical_activities = await self._identify_stage_activities(stage_leads)
                
                # Identify success factors
                success_factors = await self._identify_success_factors(
                    stage_leads, statuses[0]
                )
                
                stage_analysis.append(LeadLifecycleStage(
                    stage_name=stage_name,
                    avg_duration_days=avg_duration,
                    conversion_rate=conversion_rate,
                    typical_activities=typical_activities,
                    success_factors=success_factors
                ))
            
            return stage_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing lead lifecycle stages: {e}")
            raise
    
    async def calculate_customer_retention_rate(
        self,
        organization_id: int,
        period_days: int = 30,
        periods_to_analyze: int = 6
    ) -> Dict[str, Any]:
        """
        Calculate customer retention rate over specified periods.
        """
        try:
            # Get customers (converted leads)
            customers = self.db.query(Lead).filter(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.status == LeadStatus.CLOSED_WON
                )
            ).order_by(Lead.updated_at).all()
            
            if len(customers) < 10:
                raise ValueError("Need at least 10 customers for retention analysis")
            
            # Group customers by conversion period
            customer_cohorts = {}
            base_date = min(customer.updated_at for customer in customers)
            
            for customer in customers:
                period_index = (customer.updated_at - base_date).days // period_days
                if period_index not in customer_cohorts:
                    customer_cohorts[period_index] = []
                customer_cohorts[period_index].append(customer)
            
            # Calculate retention rates
            retention_data = []
            
            for period_index, cohort_customers in customer_cohorts.items():
                if period_index + periods_to_analyze > max(customer_cohorts.keys()):
                    continue  # Not enough future data
                
                cohort_retention = {}
                cohort_size = len(cohort_customers)
                
                for future_period in range(1, periods_to_analyze + 1):
                    # Count how many customers had activity in future period
                    future_start = base_date + timedelta(days=(period_index + future_period) * period_days)
                    future_end = future_start + timedelta(days=period_days)
                    
                    active_customers = 0
                    for customer in cohort_customers:
                        # Check for activity (communications, score updates, etc.)
                        activity_count = self.db.query(Communication).filter(
                            and_(
                                Communication.lead_id == customer.id,
                                Communication.created_at >= future_start,
                                Communication.created_at < future_end
                            )
                        ).count()
                        
                        if activity_count > 0:
                            active_customers += 1
                    
                    retention_rate = (active_customers / cohort_size) * 100 if cohort_size > 0 else 0
                    cohort_retention[future_period] = retention_rate
                
                retention_data.append({
                    "cohort_period": period_index,
                    "cohort_size": cohort_size,
                    "retention_rates": cohort_retention
                })
            
            # Calculate overall retention metrics
            overall_retention = {}
            for period in range(1, periods_to_analyze + 1):
                period_rates = [data["retention_rates"].get(period, 0) for data in retention_data]
                overall_retention[period] = sum(period_rates) / len(period_rates) if period_rates else 0
            
            return {
                "overall_retention_rates": overall_retention,
                "cohort_data": retention_data,
                "period_days": period_days,
                "total_customers": len(customers),
                "analyzed_cohorts": len(retention_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating customer retention rate: {e}")
            raise
    
    async def segment_leads_by_behavior(
        self,
        organization_id: int,
        segmentation_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Segment leads based on behavioral patterns.
        """
        try:
            # Get all leads with their activity data
            leads = self.db.query(Lead).filter(
                Lead.organization_id == organization_id
            ).all()
            
            segments = {
                "highly_engaged": [],
                "moderately_engaged": [],
                "low_engagement": [],
                "inactive": [],
                "fast_converters": [],
                "slow_nurturers": []
            }
            
            for lead in leads:
                # Get lead activity metrics
                communications = self.db.query(Communication).filter(
                    Communication.lead_id == lead.id
                ).all()
                
                score_history = self.db.query(LeadScoreHistory).filter(
                    LeadScoreHistory.lead_id == lead.id
                ).all()
                
                # Calculate engagement metrics
                engagement_score = self._calculate_engagement_score(lead, communications)
                conversion_speed = self._calculate_conversion_speed(lead)
                
                # Segment based on engagement
                if engagement_score >= 80:
                    segments["highly_engaged"].append(self._create_lead_summary(lead, engagement_score))
                elif engagement_score >= 50:
                    segments["moderately_engaged"].append(self._create_lead_summary(lead, engagement_score))
                elif engagement_score >= 20:
                    segments["low_engagement"].append(self._create_lead_summary(lead, engagement_score))
                else:
                    segments["inactive"].append(self._create_lead_summary(lead, engagement_score))
                
                # Segment based on conversion speed
                if conversion_speed is not None:
                    if conversion_speed <= 14:  # Fast: <= 2 weeks
                        segments["fast_converters"].append(self._create_lead_summary(lead, engagement_score))
                    elif conversion_speed >= 90:  # Slow: >= 3 months
                        segments["slow_nurturers"].append(self._create_lead_summary(lead, engagement_score))
            
            # Add segment statistics
            for segment_name, segment_leads in segments.items():
                if segment_leads:
                    avg_score = sum(lead["lead_score"] for lead in segment_leads) / len(segment_leads)
                    conversion_rate = (
                        sum(1 for lead in segment_leads if lead["status"] == "closed_won") 
                        / len(segment_leads) * 100
                    )
                    
                    segments[segment_name] = {
                        "leads": segment_leads,
                        "count": len(segment_leads),
                        "avg_score": round(avg_score, 2),
                        "conversion_rate": round(conversion_rate, 2)
                    }
                else:
                    segments[segment_name] = {
                        "leads": [],
                        "count": 0,
                        "avg_score": 0,
                        "conversion_rate": 0
                    }
            
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting leads by behavior: {e}")
            raise
    
    def _group_leads_into_cohorts(
        self,
        leads: List[Lead],
        period: str,
        num_periods: int
    ) -> Dict[str, List[Lead]]:
        """Group leads into cohorts based on creation period."""
        cohorts = {}
        
        # Find the earliest lead creation date
        min_date = min(lead.created_at for lead in leads)
        
        for lead in leads:
            if period == "week":
                period_start = lead.created_at - timedelta(days=lead.created_at.weekday())
                cohort_key = period_start.strftime("%Y-W%U")
            elif period == "month":
                cohort_key = lead.created_at.strftime("%Y-%m")
            elif period == "quarter":
                quarter = (lead.created_at.month - 1) // 3 + 1
                cohort_key = f"{lead.created_at.year}-Q{quarter}"
            else:
                raise ValueError("Period must be 'week', 'month', or 'quarter'")
            
            if cohort_key not in cohorts:
                cohorts[cohort_key] = []
            cohorts[cohort_key].append(lead)
        
        # Return only the most recent cohorts
        sorted_cohorts = sorted(cohorts.items(), key=lambda x: x[0])[-num_periods:]
        return dict(sorted_cohorts)
    
    async def _calculate_retention_rates(
        self,
        cohort_leads: List[Lead],
        period: str
    ) -> Dict[int, float]:
        """Calculate retention rates for a cohort."""
        retention_rates = {}
        
        # Get cohort creation date
        cohort_start = min(lead.created_at for lead in cohort_leads)
        
        # Calculate period length in days
        if period == "week":
            period_days = 7
        elif period == "month":
            period_days = 30
        elif period == "quarter":
            period_days = 90
        else:
            period_days = 30
        
        # Check retention for up to 6 periods
        for period_num in range(1, 7):
            period_start = cohort_start + timedelta(days=period_num * period_days)
            period_end = period_start + timedelta(days=period_days)
            
            # Count leads with activity in this period
            active_leads = 0
            for lead in cohort_leads:
                activity_count = self.db.query(Communication).filter(
                    and_(
                        Communication.lead_id == lead.id,
                        Communication.created_at >= period_start,
                        Communication.created_at < period_end
                    )
                ).count()
                
                if activity_count > 0:
                    active_leads += 1
            
            retention_rate = (active_leads / len(cohort_leads)) * 100 if cohort_leads else 0
            retention_rates[period_num] = retention_rate
        
        return retention_rates
    
    async def _calculate_conversion_rates(
        self,
        cohort_leads: List[Lead],
        period: str
    ) -> Dict[int, float]:
        """Calculate conversion rates for a cohort over time."""
        conversion_rates = {}
        
        # Get cohort creation date
        cohort_start = min(lead.created_at for lead in cohort_leads)
        
        # Period length in days
        if period == "week":
            period_days = 7
        elif period == "month":
            period_days = 30
        elif period == "quarter":
            period_days = 90
        else:
            period_days = 30
        
        # Calculate cumulative conversion rates
        for period_num in range(1, 7):
            period_end = cohort_start + timedelta(days=period_num * period_days)
            
            # Count conversions by this period
            conversions = sum(
                1 for lead in cohort_leads
                if lead.status == LeadStatus.CLOSED_WON and lead.updated_at <= period_end
            )
            
            conversion_rate = (conversions / len(cohort_leads)) * 100 if cohort_leads else 0
            conversion_rates[period_num] = conversion_rate
        
        return conversion_rates
    
    async def _calculate_cohort_revenue(
        self,
        cohort_leads: List[Lead],
        period: str
    ) -> Dict[int, float]:
        """Calculate revenue generated by cohort over time."""
        revenue_per_period = {}
        
        cohort_start = min(lead.created_at for lead in cohort_leads)
        
        if period == "week":
            period_days = 7
        elif period == "month":
            period_days = 30
        elif period == "quarter":
            period_days = 90
        else:
            period_days = 30
        
        for period_num in range(1, 7):
            period_end = cohort_start + timedelta(days=period_num * period_days)
            
            # Sum revenue from converted leads by this period
            revenue = sum(
                lead.value or 0 for lead in cohort_leads
                if lead.status == LeadStatus.CLOSED_WON and lead.updated_at <= period_end
            )
            
            revenue_per_period[period_num] = revenue
        
        return revenue_per_period
    
    def _calculate_avg_conversion_time(self, cohort_leads: List[Lead]) -> float:
        """Calculate average time to conversion for cohort."""
        conversion_times = []
        
        for lead in cohort_leads:
            if lead.status == LeadStatus.CLOSED_WON:
                conversion_time = (lead.updated_at - lead.created_at).days
                conversion_times.append(conversion_time)
        
        return sum(conversion_times) / len(conversion_times) if conversion_times else 0
    
    def _analyze_cohort_characteristics(self, cohort_leads: List[Lead]) -> Dict[str, Any]:
        """Analyze characteristics of a cohort."""
        if not cohort_leads:
            return {}
        
        # Source distribution
        source_counts = {}
        for lead in cohort_leads:
            source = lead.source.value if lead.source else "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Temperature distribution
        temp_counts = {}
        for lead in cohort_leads:
            temp = lead.lead_temperature.value if lead.lead_temperature else "unknown"
            temp_counts[temp] = temp_counts.get(temp, 0) + 1
        
        # Score statistics
        scores = [lead.score for lead in cohort_leads if lead.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "avg_score": round(avg_score, 2),
            "source_distribution": source_counts,
            "temperature_distribution": temp_counts,
            "has_company_percentage": (
                sum(1 for lead in cohort_leads if lead.company) / len(cohort_leads) * 100
            ),
            "has_phone_percentage": (
                sum(1 for lead in cohort_leads if lead.phone) / len(cohort_leads) * 100
            )
        }
    
    async def _calculate_stage_duration(self, stage_leads: List[Lead], status: LeadStatus) -> float:
        """Calculate average duration leads spend in a specific stage."""
        durations = []
        
        for lead in stage_leads:
            # Get status change history from activity logs
            status_changes = self.db.query(ActivityLog).filter(
                and_(
                    ActivityLog.lead_id == lead.id,
                    ActivityLog.activity_type == "status_change"
                )
            ).order_by(ActivityLog.created_at).all()
            
            # Simple duration calculation (time in current status)
            if status_changes:
                last_change = status_changes[-1].created_at
                duration = (datetime.utcnow() - last_change).days
                durations.append(max(duration, 1))  # Minimum 1 day
            else:
                # Use time since creation
                duration = (datetime.utcnow() - lead.created_at).days
                durations.append(max(duration, 1))
        
        return sum(durations) / len(durations) if durations else 0
    
    async def _calculate_stage_conversion_rate(self, organization_id: int, status: LeadStatus) -> float:
        """Calculate conversion rate from a specific stage."""
        # Get all leads that were in this status
        stage_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == status
            )
        ).count()
        
        # Count how many eventually converted
        converted_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CLOSED_WON
            )
        ).count()
        
        # Simplified conversion rate calculation
        return (converted_leads / stage_leads * 100) if stage_leads > 0 else 0
    
    async def _identify_stage_activities(self, stage_leads: List[Lead]) -> List[str]:
        """Identify typical activities in a stage."""
        activity_counts = {}
        
        for lead in stage_leads:
            communications = self.db.query(Communication).filter(
                Communication.lead_id == lead.id
            ).all()
            
            for comm in communications:
                activity_type = comm.communication_type.value
                activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        # Return top 3 activities
        sorted_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
        return [activity[0] for activity in sorted_activities[:3]]
    
    async def _identify_success_factors(self, stage_leads: List[Lead], status: LeadStatus) -> List[str]:
        """Identify factors that lead to success in this stage."""
        success_factors = []
        
        # Analyze successful leads (those that converted)
        successful_leads = [lead for lead in stage_leads if lead.status == LeadStatus.CLOSED_WON]
        
        if successful_leads:
            # Common characteristics of successful leads
            avg_score = sum(lead.score for lead in successful_leads) / len(successful_leads)
            if avg_score > 70:
                success_factors.append("High lead score (>70)")
            
            company_percentage = sum(1 for lead in successful_leads if lead.company) / len(successful_leads)
            if company_percentage > 0.8:
                success_factors.append("Complete company information")
            
            # Check for multiple communications
            for lead in successful_leads:
                comm_count = self.db.query(Communication).filter(
                    Communication.lead_id == lead.id
                ).count()
                if comm_count > 3:
                    success_factors.append("Multiple touchpoints")
                    break
        
        return success_factors[:3]  # Top 3 factors
    
    def _calculate_engagement_score(self, lead: Lead, communications: List[Communication]) -> float:
        """Calculate engagement score for lead segmentation."""
        score = 0
        
        # Communication frequency
        score += min(len(communications) * 10, 40)  # Max 40 points
        
        # Inbound communications (shows interest)
        inbound_count = sum(1 for comm in communications if comm.direction.value == "inbound")
        score += min(inbound_count * 15, 30)  # Max 30 points
        
        # Lead score contribution
        score += min((lead.score or 0) * 0.3, 30)  # Max 30 points from lead score
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_conversion_speed(self, lead: Lead) -> Optional[float]:
        """Calculate days to conversion (None if not converted)."""
        if lead.status == LeadStatus.CLOSED_WON:
            return (lead.updated_at - lead.created_at).days
        return None
    
    def _create_lead_summary(self, lead: Lead, engagement_score: float) -> Dict[str, Any]:
        """Create a summary of lead for segmentation."""
        return {
            "lead_id": lead.id,
            "name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company,
            "status": lead.status.value,
            "lead_score": lead.score or 0,
            "engagement_score": round(engagement_score, 1),
            "source": lead.source.value if lead.source else "unknown",
            "created_at": lead.created_at.isoformat(),
            "days_in_pipeline": (datetime.utcnow() - lead.created_at).days
        } 