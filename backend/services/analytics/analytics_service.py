"""
Comprehensive Analytics Service

Main service that orchestrates statistical analysis, predictive analytics,
and cohort analysis for the LMA platform. Integrates with AutomationEngine
for optimized calculations.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import asdict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from .statistical_engine import StatisticalEngine, TrendDirection, CorrelationType
from .predictive_analytics import PredictiveAnalytics, ConversionProbability
from .cohort_analysis import CohortAnalysis
from models import Lead, Communication, LeadScoreHistory, Organization, LeadStatus
from automation.engine import AutomationEngine

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """
    Comprehensive analytics service providing statistical analysis,
    predictive modeling, and cohort analysis capabilities.
    """
    
    def __init__(self, db: Session, automation_engine: Optional[AutomationEngine] = None):
        """Initialize the advanced analytics service."""
        self.db = db
        self.automation_engine = automation_engine
        
        # Initialize analysis engines
        self.statistical_engine = StatisticalEngine(db)
        self.predictive_analytics = PredictiveAnalytics(db)
        self.cohort_analysis = CohortAnalysis(db)
        
        # Cache for expensive calculations
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    async def generate_comprehensive_analytics_report(
        self,
        organization_id: int,
        lead_ids: Optional[List[int]] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report combining all analysis types.
        
        Args:
            organization_id: Organization to analyze
            lead_ids: Specific leads to analyze (optional)
            days_back: Historical period to analyze
        """
        try:
            logger.info(f"Generating comprehensive analytics report for org {organization_id}")
            
            # Use automation engine for parallel processing if available
            if self.automation_engine:
                return await self._generate_report_parallel(organization_id, lead_ids, days_back)
            else:
                return await self._generate_report_sequential(organization_id, lead_ids, days_back)
                
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            raise
    
    async def analyze_lead_conversion_probability(
        self,
        lead_ids: List[int],
        model_type: str = "random_forest"
    ) -> List[Dict[str, Any]]:
        """
        Analyze conversion probability for multiple leads using machine learning.
        """
        try:
            results = []
            
            # Process leads in batches for performance
            batch_size = 50
            for i in range(0, len(lead_ids), batch_size):
                batch = lead_ids[i:i + batch_size]
                
                # Use automation engine for parallel processing
                if self.automation_engine:
                    batch_tasks = [
                        self.predictive_analytics.predict_lead_conversion(lead_id, model_type)
                        for lead_id in batch
                    ]
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Process results
                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            logger.error(f"Error predicting conversion for lead {batch[j]}: {result}")
                            continue
                        
                        # Convert to dict and add insights
                        prediction_dict = asdict(result)
                        prediction_dict['insights'] = self._generate_conversion_insights(result)
                        results.append(prediction_dict)
                else:
                    # Sequential processing
                    for lead_id in batch:
                        try:
                            prediction = await self.predictive_analytics.predict_lead_conversion(
                                lead_id, model_type
                            )
                            prediction_dict = asdict(prediction)
                            prediction_dict['insights'] = self._generate_conversion_insights(prediction)
                            results.append(prediction_dict)
                        except Exception as e:
                            logger.error(f"Error predicting conversion for lead {lead_id}: {e}")
                            continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing lead conversion probabilities: {e}")
            raise
    
    async def perform_statistical_analysis(
        self,
        organization_id: int,
        analysis_type: str = "comprehensive",
        custom_datasets: Optional[Dict[str, List[Union[int, float]]]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive statistical analysis on organizational data.
        
        Args:
            organization_id: Organization to analyze
            analysis_type: "comprehensive", "correlation", "trend", or "descriptive"
            custom_datasets: Custom data for analysis
        """
        try:
            results = {
                "organization_id": organization_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.utcnow().isoformat(),
                "results": {}
            }
            
            # Get organizational data
            leads = self.db.query(Lead).filter(
                Lead.organization_id == organization_id
            ).all()
            
            if not leads:
                raise ValueError(f"No leads found for organization {organization_id}")
            
            # Prepare datasets for analysis
            datasets = await self._prepare_statistical_datasets(leads)
            
            # Add custom datasets if provided
            if custom_datasets:
                datasets.update(custom_datasets)
            
            if analysis_type in ["comprehensive", "descriptive"]:
                # Descriptive statistics for all datasets
                descriptive_stats = {}
                for name, data in datasets.items():
                    if data and len(data) > 0:
                        try:
                            stats = self.statistical_engine.calculate_descriptive_stats(data)
                            descriptive_stats[name] = asdict(stats)
                        except Exception as e:
                            logger.warning(f"Could not calculate stats for {name}: {e}")
                
                results["results"]["descriptive_statistics"] = descriptive_stats
            
            if analysis_type in ["comprehensive", "correlation"]:
                # Correlation analysis between key metrics
                correlations = await self._calculate_correlation_matrix(datasets)
                results["results"]["correlations"] = correlations
            
            if analysis_type in ["comprehensive", "trend"]:
                # Trend analysis for time-series data
                trends = await self._analyze_trends(organization_id)
                results["results"]["trends"] = trends
            
            # Outlier detection
            outliers = {}
            for name, data in datasets.items():
                if data and len(data) >= 4:
                    try:
                        outlier_result = self.statistical_engine.detect_outliers(data)
                        outliers[name] = outlier_result
                    except Exception as e:
                        logger.warning(f"Could not detect outliers for {name}: {e}")
            
            results["results"]["outliers"] = outliers
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing statistical analysis: {e}")
            raise
    
    async def analyze_customer_lifecycle(
        self,
        organization_id: int,
        cohort_period: str = "month",
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive customer lifecycle analysis including cohorts and predictions.
        """
        try:
            results = {
                "organization_id": organization_id,
                "cohort_period": cohort_period,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cohort analysis
            cohort_metrics = await self.cohort_analysis.analyze_lead_cohorts(
                organization_id, cohort_period, 12
            )
            results["cohort_analysis"] = [asdict(metric) for metric in cohort_metrics]
            
            # Lifecycle stage analysis
            lifecycle_stages = await self.cohort_analysis.analyze_lead_lifecycle_stages(
                organization_id
            )
            results["lifecycle_stages"] = [asdict(stage) for stage in lifecycle_stages]
            
            # Customer retention analysis
            retention_analysis = await self.cohort_analysis.calculate_customer_retention_rate(
                organization_id
            )
            results["retention_analysis"] = retention_analysis
            
            # Behavioral segmentation
            behavioral_segments = await self.cohort_analysis.segment_leads_by_behavior(
                organization_id
            )
            results["behavioral_segments"] = behavioral_segments
            
            # Customer lifetime value
            clv_analysis = await self.predictive_analytics.calculate_customer_lifetime_value(
                organization_id
            )
            results["customer_lifetime_value"] = clv_analysis
            
            if include_predictions:
                # Revenue forecasting
                revenue_forecast = await self.predictive_analytics.forecast_revenue(
                    organization_id, 90
                )
                results["revenue_forecast"] = asdict(revenue_forecast)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing customer lifecycle: {e}")
            raise
    
    async def calculate_advanced_metrics(
        self,
        organization_id: int,
        metric_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate advanced metrics using complex mathematical operations.
        
        Args:
            organization_id: Organization to analyze
            metric_types: List of metric types to calculate
        """
        if metric_types is None:
            metric_types = ["conversion_funnel", "engagement_analytics", "performance_metrics"]
        
        try:
            results = {}
            
            for metric_type in metric_types:
                if metric_type == "conversion_funnel":
                    results["conversion_funnel"] = await self._calculate_conversion_funnel_metrics(
                        organization_id
                    )
                elif metric_type == "engagement_analytics":
                    results["engagement_analytics"] = await self._calculate_engagement_metrics(
                        organization_id
                    )
                elif metric_type == "performance_metrics":
                    results["performance_metrics"] = await self._calculate_performance_metrics(
                        organization_id
                    )
                elif metric_type == "predictive_scores":
                    results["predictive_scores"] = await self._calculate_predictive_scores(
                        organization_id
                    )
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating advanced metrics: {e}")
            raise
    
    async def _generate_report_parallel(
        self,
        organization_id: int,
        lead_ids: Optional[List[int]],
        days_back: int
    ) -> Dict[str, Any]:
        """Generate analytics report using parallel processing."""
        # Create tasks for parallel execution
        tasks = [
            self.perform_statistical_analysis(organization_id, "comprehensive"),
            self.analyze_customer_lifecycle(organization_id),
            self.calculate_advanced_metrics(organization_id)
        ]
        
        # Add lead conversion analysis if specific leads provided
        if lead_ids:
            tasks.append(self.analyze_lead_conversion_probability(lead_ids))
        
        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        report = {
            "organization_id": organization_id,
            "report_generated_at": datetime.utcnow().isoformat(),
            "days_analyzed": days_back,
            "statistical_analysis": results[0] if not isinstance(results[0], Exception) else None,
            "lifecycle_analysis": results[1] if not isinstance(results[1], Exception) else None,
            "advanced_metrics": results[2] if not isinstance(results[2], Exception) else None
        }
        
        if lead_ids and len(results) > 3:
            report["conversion_predictions"] = results[3] if not isinstance(results[3], Exception) else None
        
        # Add summary insights
        report["insights"] = self._generate_report_insights(report)
        
        return report
    
    async def _generate_report_sequential(
        self,
        organization_id: int,
        lead_ids: Optional[List[int]],
        days_back: int
    ) -> Dict[str, Any]:
        """Generate analytics report using sequential processing."""
        report = {
            "organization_id": organization_id,
            "report_generated_at": datetime.utcnow().isoformat(),
            "days_analyzed": days_back
        }
        
        # Sequential execution
        try:
            report["statistical_analysis"] = await self.perform_statistical_analysis(
                organization_id, "comprehensive"
            )
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
            report["statistical_analysis"] = None
        
        try:
            report["lifecycle_analysis"] = await self.analyze_customer_lifecycle(organization_id)
        except Exception as e:
            logger.error(f"Lifecycle analysis failed: {e}")
            report["lifecycle_analysis"] = None
        
        try:
            report["advanced_metrics"] = await self.calculate_advanced_metrics(organization_id)
        except Exception as e:
            logger.error(f"Advanced metrics calculation failed: {e}")
            report["advanced_metrics"] = None
        
        if lead_ids:
            try:
                report["conversion_predictions"] = await self.analyze_lead_conversion_probability(lead_ids)
            except Exception as e:
                logger.error(f"Conversion predictions failed: {e}")
                report["conversion_predictions"] = None
        
        # Add insights
        report["insights"] = self._generate_report_insights(report)
        
        return report
    
    async def _prepare_statistical_datasets(self, leads: List[Lead]) -> Dict[str, List[Union[int, float]]]:
        """Prepare datasets for statistical analysis."""
        datasets = {
            "lead_scores": [lead.score for lead in leads if lead.score is not None],
            "lead_values": [lead.value for lead in leads if lead.value is not None],
            "days_in_pipeline": [
                (datetime.utcnow() - lead.created_at).days for lead in leads
            ]
        }
        
        # Add communication counts
        comm_counts = []
        for lead in leads:
            count = self.db.query(Communication).filter(
                Communication.lead_id == lead.id
            ).count()
            comm_counts.append(count)
        datasets["communication_counts"] = comm_counts
        
        return datasets
    
    async def _calculate_correlation_matrix(
        self,
        datasets: Dict[str, List[Union[int, float]]]
    ) -> Dict[str, Any]:
        """Calculate correlation matrix between datasets."""
        correlations = {}
        dataset_names = list(datasets.keys())
        
        for i, name1 in enumerate(dataset_names):
            for name2 in dataset_names[i + 1:]:
                if len(datasets[name1]) > 3 and len(datasets[name2]) > 3:
                    # Ensure equal length
                    min_len = min(len(datasets[name1]), len(datasets[name2]))
                    data1 = datasets[name1][:min_len]
                    data2 = datasets[name2][:min_len]
                    
                    try:
                        correlation = self.statistical_engine.calculate_correlation(data1, data2)
                        correlations[f"{name1}_vs_{name2}"] = asdict(correlation)
                    except Exception as e:
                        logger.warning(f"Could not calculate correlation between {name1} and {name2}: {e}")
        
        return correlations
    
    async def _analyze_trends(self, organization_id: int) -> Dict[str, Any]:
        """Analyze trends in organizational metrics."""
        trends = {}
        
        # Lead score trend over time
        score_history = self.db.query(LeadScoreHistory).join(Lead).filter(
            Lead.organization_id == organization_id
        ).order_by(LeadScoreHistory.created_at).all()
        
        if len(score_history) > 3:
            score_time_series = [
                (history.created_at, history.new_score) for history in score_history
            ]
            try:
                score_trend = self.statistical_engine.analyze_trend(score_time_series)
                trends["lead_score_trend"] = asdict(score_trend)
            except Exception as e:
                logger.warning(f"Could not analyze score trend: {e}")
        
        # Lead creation trend
        leads = self.db.query(Lead).filter(
            Lead.organization_id == organization_id
        ).order_by(Lead.created_at).all()
        
        if len(leads) > 3:
            # Group by day and count
            daily_counts = {}
            for lead in leads:
                day_key = lead.created_at.date()
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            if len(daily_counts) > 3:
                creation_time_series = [
                    (datetime.combine(date, datetime.min.time()), count)
                    for date, count in sorted(daily_counts.items())
                ]
                try:
                    creation_trend = self.statistical_engine.analyze_trend(creation_time_series)
                    trends["lead_creation_trend"] = asdict(creation_trend)
                except Exception as e:
                    logger.warning(f"Could not analyze creation trend: {e}")
        
        return trends
    
    def _generate_conversion_insights(self, prediction) -> List[str]:
        """Generate insights from conversion prediction."""
        insights = []
        
        if prediction.probability_category == ConversionProbability.VERY_HIGH:
            insights.append("🔥 High-value lead - immediate sales attention recommended")
        elif prediction.probability_category == ConversionProbability.HIGH:
            insights.append("⭐ Strong conversion potential - prioritize for outreach")
        elif prediction.probability_category == ConversionProbability.MODERATE:
            insights.append("📈 Moderate potential - consider nurturing campaigns")
        else:
            insights.append("🔄 Low conversion probability - focus on engagement")
        
        # Add factor-based insights
        top_factors = prediction.key_factors[:2]
        for factor in top_factors:
            if factor["impact"] == "high":
                insights.append(f"💡 Key factor: {factor['factor']} (high impact)")
        
        return insights
    
    def _generate_report_insights(self, report: Dict[str, Any]) -> List[str]:
        """Generate high-level insights from the complete report."""
        insights = []
        
        # Statistical insights
        if report.get("statistical_analysis"):
            stats = report["statistical_analysis"]["results"]
            if "descriptive_statistics" in stats:
                insights.append("📊 Statistical analysis complete with descriptive metrics")
            
            if "correlations" in stats:
                strong_correlations = [
                    name for name, corr in stats["correlations"].items()
                    if corr.get("correlation_type") in ["strong", "very_strong"]
                ]
                if strong_correlations:
                    insights.append(f"🔗 Found {len(strong_correlations)} strong correlations")
        
        # Lifecycle insights
        if report.get("lifecycle_analysis"):
            lifecycle = report["lifecycle_analysis"]
            if "cohort_analysis" in lifecycle and lifecycle["cohort_analysis"]:
                insights.append(f"👥 Analyzed {len(lifecycle['cohort_analysis'])} customer cohorts")
            
            if "retention_analysis" in lifecycle:
                retention = lifecycle["retention_analysis"]["overall_retention_rates"]
                if retention:
                    avg_retention = sum(retention.values()) / len(retention)
                    insights.append(f"📈 Average customer retention rate: {avg_retention:.1f}%")
        
        # Advanced metrics insights
        if report.get("advanced_metrics"):
            insights.append("🚀 Advanced metrics calculation completed")
        
        return insights
    
    async def _calculate_conversion_funnel_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Calculate advanced conversion funnel metrics."""
        # Get leads at each stage
        stages = [
            ("new", [LeadStatus.NEW]),
            ("contacted", [LeadStatus.CONTACTED]),
            ("qualified", [LeadStatus.QUALIFIED]),
            ("proposal", [LeadStatus.PROPOSAL]),
            ("negotiation", [LeadStatus.NEGOTIATION]),
            ("won", [LeadStatus.CLOSED_WON]),
            ("lost", [LeadStatus.CLOSED_LOST])
        ]
        
        funnel_data = {}
        total_leads = self.db.query(Lead).filter(
            Lead.organization_id == organization_id
        ).count()
        
        for stage_name, statuses in stages:
            count = self.db.query(Lead).filter(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.status.in_(statuses)
                )
            ).count()
            
            funnel_data[stage_name] = {
                "count": count,
                "percentage": (count / total_leads * 100) if total_leads > 0 else 0
            }
        
        # Calculate stage-to-stage conversion rates
        conversion_rates = {}
        for i in range(len(stages) - 1):
            current_stage = stages[i][0]
            next_stage = stages[i + 1][0]
            
            current_count = funnel_data[current_stage]["count"]
            next_count = funnel_data[next_stage]["count"]
            
            if current_count > 0:
                conversion_rate = (next_count / current_count) * 100
                conversion_rates[f"{current_stage}_to_{next_stage}"] = conversion_rate
        
        return {
            "funnel_stages": funnel_data,
            "conversion_rates": conversion_rates,
            "total_leads": total_leads
        }
    
    async def _calculate_engagement_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Calculate advanced engagement metrics."""
        leads = self.db.query(Lead).filter(
            Lead.organization_id == organization_id
        ).all()
        
        if not leads:
            return {}
        
        engagement_scores = []
        response_rates = []
        
        for lead in leads:
            communications = self.db.query(Communication).filter(
                Communication.lead_id == lead.id
            ).all()
            
            if communications:
                # Calculate engagement score
                inbound_count = sum(1 for c in communications if c.direction.value == "inbound")
                outbound_count = len(communications) - inbound_count
                
                engagement_score = (inbound_count * 2 + outbound_count) / len(communications) * 100
                engagement_scores.append(engagement_score)
                
                # Calculate response rate
                response_rate = (inbound_count / outbound_count * 100) if outbound_count > 0 else 0
                response_rates.append(response_rate)
        
        if engagement_scores and response_rates:
            avg_engagement = sum(engagement_scores) / len(engagement_scores)
            avg_response_rate = sum(response_rates) / len(response_rates)
            
            return {
                "average_engagement_score": avg_engagement,
                "average_response_rate": avg_response_rate,
                "engagement_distribution": {
                    "high": len([s for s in engagement_scores if s >= 80]),
                    "medium": len([s for s in engagement_scores if 50 <= s < 80]),
                    "low": len([s for s in engagement_scores if s < 50])
                }
            }
        
        return {}
    
    async def _calculate_performance_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Calculate advanced performance metrics."""
        # Time-based performance metrics
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)
        
        # Lead velocity (leads created per day)
        recent_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.created_at >= last_30_days
            )
        ).count()
        
        lead_velocity = recent_leads / 30  # Per day
        
        # Conversion velocity (time from lead to conversion)
        converted_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CLOSED_WON,
                Lead.updated_at >= last_90_days
            )
        ).all()
        
        conversion_times = [
            (lead.updated_at - lead.created_at).days 
            for lead in converted_leads
        ]
        
        avg_conversion_time = sum(conversion_times) / len(conversion_times) if conversion_times else 0
        
        # Score improvement rate
        score_improvements = self.db.query(LeadScoreHistory).join(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                LeadScoreHistory.created_at >= last_30_days,
                LeadScoreHistory.score_change > 0
            )
        ).all()
        
        avg_score_improvement = (
            sum(history.score_change for history in score_improvements) / len(score_improvements)
            if score_improvements else 0
        )
        
        return {
            "lead_velocity_per_day": lead_velocity,
            "average_conversion_time_days": avg_conversion_time,
            "average_score_improvement": avg_score_improvement,
            "total_conversions_90_days": len(converted_leads)
        }
    
    async def _calculate_predictive_scores(self, organization_id: int) -> Dict[str, Any]:
        """Calculate predictive scoring metrics."""
        # Get active leads for scoring
        active_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status.in_([
                    LeadStatus.NEW, LeadStatus.CONTACTED, 
                    LeadStatus.QUALIFIED, LeadStatus.PROPOSAL, 
                    LeadStatus.NEGOTIATION
                ])
            )
        ).all()
        
        if not active_leads:
            return {}
        
        # Sample a subset for prediction (limit to avoid performance issues)
        sample_leads = active_leads[:50] if len(active_leads) > 50 else active_leads
        
        high_probability_count = 0
        total_predicted_revenue = 0
        
        for lead in sample_leads:
            try:
                prediction = await self.predictive_analytics.predict_lead_conversion(lead.id)
                
                if prediction.conversion_probability >= 0.6:
                    high_probability_count += 1
                
                # Estimate potential revenue
                if lead.value:
                    expected_revenue = lead.value * prediction.conversion_probability
                    total_predicted_revenue += expected_revenue
                    
            except Exception as e:
                logger.warning(f"Could not predict conversion for lead {lead.id}: {e}")
                continue
        
        return {
            "total_active_leads": len(active_leads),
            "high_probability_leads": high_probability_count,
            "high_probability_percentage": (high_probability_count / len(sample_leads) * 100) if sample_leads else 0,
            "predicted_revenue": total_predicted_revenue
        } 