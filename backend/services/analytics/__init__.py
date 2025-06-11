"""
Analytics Services Module

Provides comprehensive analytics capabilities including:
- Statistical analysis and data science utilities
- Predictive analytics for lead conversion and revenue forecasting
- Cohort analysis for customer lifecycle tracking
- Advanced calculations and machine learning features
"""

from .statistical_engine import StatisticalEngine, StatisticalSummary, CorrelationResult, TrendAnalysis
from .predictive_analytics import PredictiveAnalytics, ConversionPrediction, RevenueForcast
from .cohort_analysis import CohortAnalysis, CohortMetrics, LeadLifecycleStage

__all__ = [
    "StatisticalEngine",
    "StatisticalSummary", 
    "CorrelationResult",
    "TrendAnalysis",
    "PredictiveAnalytics",
    "ConversionPrediction",
    "RevenueForcast",
    "CohortAnalysis",
    "CohortMetrics",
    "LeadLifecycleStage"
] 