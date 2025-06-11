"""
Statistical Analysis Engine

Provides comprehensive statistical analysis, correlation analysis, trend detection,
and data science utilities for the LMA platform analytics.
"""

import logging
import math
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr, chi2_contingency
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from models import Lead, Communication, LeadScoreHistory, ActivityLog, Campaign

logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    """Trend direction classification"""
    STRONG_UPWARD = "strong_upward"
    MODERATE_UPWARD = "moderate_upward"
    SLIGHT_UPWARD = "slight_upward"
    STABLE = "stable"
    SLIGHT_DOWNWARD = "slight_downward"
    MODERATE_DOWNWARD = "moderate_downward"
    STRONG_DOWNWARD = "strong_downward"

class CorrelationType(Enum):
    """Correlation strength classification"""
    VERY_STRONG = "very_strong"      # |r| >= 0.8
    STRONG = "strong"                # 0.6 <= |r| < 0.8
    MODERATE = "moderate"            # 0.4 <= |r| < 0.6
    WEAK = "weak"                    # 0.2 <= |r| < 0.4
    VERY_WEAK = "very_weak"          # |r| < 0.2

@dataclass
class StatisticalSummary:
    """Statistical summary of a dataset"""
    count: int
    mean: float
    median: float
    mode: Optional[float]
    std_dev: float
    variance: float
    min_value: float
    max_value: float
    range_value: float
    q1: float
    q3: float
    iqr: float
    skewness: float
    kurtosis: float
    confidence_interval_95: Tuple[float, float]

@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    correlation_coefficient: float
    p_value: float
    correlation_type: CorrelationType
    is_significant: bool
    sample_size: int
    confidence_interval: Tuple[float, float]
    interpretation: str

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    trend_direction: TrendDirection
    slope: float
    r_squared: float
    p_value: float
    is_significant: bool
    predicted_next_value: float
    confidence_interval: Tuple[float, float]
    trend_strength: str

class StatisticalEngine:
    """
    Advanced statistical analysis engine for LMA platform.
    Provides correlation analysis, trend detection, and statistical testing.
    """
    
    def __init__(self, db: Session):
        """Initialize the statistical engine."""
        self.db = db
        self.significance_level = 0.05
    
    def calculate_descriptive_stats(self, data: List[Union[int, float]]) -> StatisticalSummary:
        """
        Calculate comprehensive descriptive statistics for a dataset.
        """
        if not data or len(data) == 0:
            raise ValueError("Dataset cannot be empty")
        
        try:
            # Remove None values and convert to float
            clean_data = [float(x) for x in data if x is not None]
            
            if len(clean_data) == 0:
                raise ValueError("No valid numeric data found")
            
            # Basic statistics
            count = len(clean_data)
            mean_val = statistics.mean(clean_data)
            median_val = statistics.median(clean_data)
            
            # Mode (handle case where no mode exists)
            try:
                mode_val = statistics.mode(clean_data)
            except statistics.StatisticsError:
                mode_val = None
            
            # Variability measures
            if count > 1:
                std_dev = statistics.stdev(clean_data)
                variance = statistics.variance(clean_data)
            else:
                std_dev = 0.0
                variance = 0.0
            
            min_val = min(clean_data)
            max_val = max(clean_data)
            range_val = max_val - min_val
            
            # Quartiles
            q1 = np.percentile(clean_data, 25)
            q3 = np.percentile(clean_data, 75)
            iqr = q3 - q1
            
            # Shape measures
            if count > 2 and std_dev > 0:
                skewness = stats.skew(clean_data)
                kurtosis = stats.kurtosis(clean_data)
            else:
                skewness = 0.0
                kurtosis = 0.0
            
            # Confidence interval (95%)
            if count > 1 and std_dev > 0:
                confidence_interval = stats.t.interval(
                    0.95, count - 1,
                    loc=mean_val,
                    scale=stats.sem(clean_data)
                )
            else:
                confidence_interval = (mean_val, mean_val)
            
            return StatisticalSummary(
                count=count,
                mean=mean_val,
                median=median_val,
                mode=mode_val,
                std_dev=std_dev,
                variance=variance,
                min_value=min_val,
                max_value=max_val,
                range_value=range_val,
                q1=q1,
                q3=q3,
                iqr=iqr,
                skewness=skewness,
                kurtosis=kurtosis,
                confidence_interval_95=confidence_interval
            )
            
        except Exception as e:
            logger.error(f"Error calculating descriptive statistics: {e}")
            raise
    
    def calculate_correlation(
        self, 
        x_data: List[Union[int, float]], 
        y_data: List[Union[int, float]],
        method: str = "pearson"
    ) -> CorrelationResult:
        """
        Calculate correlation between two variables with significance testing.
        
        Args:
            x_data: First variable data
            y_data: Second variable data  
            method: "pearson" or "spearman"
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have the same length")
        
        if len(x_data) < 3:
            raise ValueError("Need at least 3 data points for correlation analysis")
        
        try:
            # Clean data
            clean_pairs = [(float(x), float(y)) for x, y in zip(x_data, y_data) 
                          if x is not None and y is not None]
            
            if len(clean_pairs) < 3:
                raise ValueError("Need at least 3 valid data pairs")
            
            x_clean = [pair[0] for pair in clean_pairs]
            y_clean = [pair[1] for pair in clean_pairs]
            
            # Calculate correlation
            if method.lower() == "pearson":
                corr_coef, p_value = pearsonr(x_clean, y_clean)
            elif method.lower() == "spearman":
                corr_coef, p_value = spearmanr(x_clean, y_clean)
            else:
                raise ValueError("Method must be 'pearson' or 'spearman'")
            
            # Classify correlation strength
            abs_corr = abs(corr_coef)
            if abs_corr >= 0.8:
                corr_type = CorrelationType.VERY_STRONG
            elif abs_corr >= 0.6:
                corr_type = CorrelationType.STRONG
            elif abs_corr >= 0.4:
                corr_type = CorrelationType.MODERATE
            elif abs_corr >= 0.2:
                corr_type = CorrelationType.WEAK
            else:
                corr_type = CorrelationType.VERY_WEAK
            
            # Significance test
            is_significant = p_value < self.significance_level
            
            # Confidence interval for correlation coefficient
            n = len(clean_pairs)
            if n > 3:
                # Fisher's z-transformation for confidence interval
                z = 0.5 * math.log((1 + corr_coef) / (1 - corr_coef))
                se = 1 / math.sqrt(n - 3)
                z_critical = stats.norm.ppf(0.975)  # 95% CI
                
                z_lower = z - z_critical * se
                z_upper = z + z_critical * se
                
                # Transform back
                ci_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
                ci_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)
                confidence_interval = (ci_lower, ci_upper)
            else:
                confidence_interval = (corr_coef, corr_coef)
            
            # Generate interpretation
            direction = "positive" if corr_coef > 0 else "negative"
            strength = corr_type.value.replace("_", " ")
            significance = "significant" if is_significant else "not significant"
            
            interpretation = (
                f"There is a {strength} {direction} correlation (r = {corr_coef:.3f}) "
                f"that is {significance} at α = {self.significance_level} (p = {p_value:.3f})"
            )
            
            return CorrelationResult(
                correlation_coefficient=corr_coef,
                p_value=p_value,
                correlation_type=corr_type,
                is_significant=is_significant,
                sample_size=n,
                confidence_interval=confidence_interval,
                interpretation=interpretation
            )
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            raise
    
    def analyze_trend(
        self, 
        time_series_data: List[Tuple[datetime, Union[int, float]]]
    ) -> TrendAnalysis:
        """
        Analyze trend in time series data using linear regression.
        
        Args:
            time_series_data: List of (datetime, value) tuples
        """
        if len(time_series_data) < 3:
            raise ValueError("Need at least 3 data points for trend analysis")
        
        try:
            # Convert to numeric arrays
            dates = [item[0] for item in time_series_data]
            values = [float(item[1]) for item in time_series_data if item[1] is not None]
            
            if len(values) < 3:
                raise ValueError("Need at least 3 valid data points")
            
            # Convert dates to numeric (days since first date)
            base_date = min(dates)
            x_numeric = [(date - base_date).days for date in dates[:len(values)]]
            
            # Fit linear regression
            X = np.array(x_numeric).reshape(-1, 1)
            y = np.array(values)
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Get predictions
            y_pred = model.predict(X)
            
            # Calculate metrics
            slope = model.coef_[0]
            r_squared = r2_score(y, y_pred)
            
            # Statistical significance of slope
            n = len(values)
            if n > 2:
                # Calculate t-statistic for slope
                mse = mean_squared_error(y, y_pred)
                se_slope = math.sqrt(mse / sum([(x - np.mean(x_numeric))**2 for x in x_numeric]))
                t_stat = slope / se_slope if se_slope > 0 else 0
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_value = 1.0
            
            is_significant = p_value < self.significance_level
            
            # Classify trend direction
            if slope > 0:
                if r_squared >= 0.8:
                    trend_direction = TrendDirection.STRONG_UPWARD
                elif r_squared >= 0.5:
                    trend_direction = TrendDirection.MODERATE_UPWARD
                else:
                    trend_direction = TrendDirection.SLIGHT_UPWARD
            elif slope < 0:
                if r_squared >= 0.8:
                    trend_direction = TrendDirection.STRONG_DOWNWARD
                elif r_squared >= 0.5:
                    trend_direction = TrendDirection.MODERATE_DOWNWARD
                else:
                    trend_direction = TrendDirection.SLIGHT_DOWNWARD
            else:
                trend_direction = TrendDirection.STABLE
            
            # Predict next value
            next_x = max(x_numeric) + 1
            predicted_next = model.predict([[next_x]])[0]
            
            # Confidence interval for prediction
            if n > 2 and mse > 0:
                # Simple prediction interval calculation
                std_error = math.sqrt(mse)
                t_critical = stats.t.ppf(0.975, n - 2)
                margin_error = t_critical * std_error
                confidence_interval = (
                    predicted_next - margin_error,
                    predicted_next + margin_error
                )
            else:
                confidence_interval = (predicted_next, predicted_next)
            
            # Determine trend strength
            if r_squared >= 0.8:
                trend_strength = "strong"
            elif r_squared >= 0.5:
                trend_strength = "moderate"
            elif r_squared >= 0.2:
                trend_strength = "weak"
            else:
                trend_strength = "very weak"
            
            return TrendAnalysis(
                trend_direction=trend_direction,
                slope=slope,
                r_squared=r_squared,
                p_value=p_value,
                is_significant=is_significant,
                predicted_next_value=predicted_next,
                confidence_interval=confidence_interval,
                trend_strength=trend_strength
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            raise
    
    def calculate_moving_average(
        self, 
        data: List[Union[int, float]], 
        window_size: int = 7
    ) -> List[float]:
        """
        Calculate moving average with specified window size.
        """
        if window_size <= 0:
            raise ValueError("Window size must be positive")
        
        if len(data) < window_size:
            raise ValueError(f"Need at least {window_size} data points")
        
        try:
            clean_data = [float(x) for x in data if x is not None]
            moving_averages = []
            
            for i in range(window_size - 1, len(clean_data)):
                window = clean_data[i - window_size + 1:i + 1]
                avg = sum(window) / len(window)
                moving_averages.append(avg)
            
            return moving_averages
            
        except Exception as e:
            logger.error(f"Error calculating moving average: {e}")
            raise
    
    def calculate_percentage_change(
        self, 
        current_value: Union[int, float], 
        previous_value: Union[int, float]
    ) -> float:
        """
        Calculate percentage change between two values.
        """
        if previous_value == 0:
            return float('inf') if current_value > 0 else 0.0
        
        return ((current_value - previous_value) / previous_value) * 100
    
    def detect_outliers(
        self, 
        data: List[Union[int, float]], 
        method: str = "iqr"
    ) -> Dict[str, Any]:
        """
        Detect outliers using specified method.
        
        Args:
            data: Numeric data
            method: "iqr" (Interquartile Range) or "zscore"
        """
        if len(data) < 4:
            raise ValueError("Need at least 4 data points for outlier detection")
        
        try:
            clean_data = [float(x) for x in data if x is not None]
            
            if method.lower() == "iqr":
                q1 = np.percentile(clean_data, 25)
                q3 = np.percentile(clean_data, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [x for x in clean_data if x < lower_bound or x > upper_bound]
                outlier_indices = [i for i, x in enumerate(clean_data) 
                                 if x < lower_bound or x > upper_bound]
                
            elif method.lower() == "zscore":
                mean_val = np.mean(clean_data)
                std_val = np.std(clean_data)
                
                if std_val == 0:
                    outliers = []
                    outlier_indices = []
                else:
                    z_scores = [(x - mean_val) / std_val for x in clean_data]
                    outliers = [clean_data[i] for i, z in enumerate(z_scores) if abs(z) > 3]
                    outlier_indices = [i for i, z in enumerate(z_scores) if abs(z) > 3]
            
            else:
                raise ValueError("Method must be 'iqr' or 'zscore'")
            
            return {
                "outliers": outliers,
                "outlier_indices": outlier_indices,
                "outlier_count": len(outliers),
                "outlier_percentage": (len(outliers) / len(clean_data)) * 100,
                "method": method
            }
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            raise
    
    def perform_normality_test(self, data: List[Union[int, float]]) -> Dict[str, Any]:
        """
        Perform Shapiro-Wilk normality test.
        """
        if len(data) < 3:
            raise ValueError("Need at least 3 data points for normality test")
        
        try:
            clean_data = [float(x) for x in data if x is not None]
            
            if len(clean_data) < 3:
                raise ValueError("Need at least 3 valid data points")
            
            # Shapiro-Wilk test
            statistic, p_value = stats.shapiro(clean_data)
            
            is_normal = p_value > self.significance_level
            
            return {
                "test_statistic": statistic,
                "p_value": p_value,
                "is_normal": is_normal,
                "alpha": self.significance_level,
                "interpretation": (
                    f"Data {'appears to be' if is_normal else 'does not appear to be'} "
                    f"normally distributed (p = {p_value:.3f})"
                )
            }
            
        except Exception as e:
            logger.error(f"Error performing normality test: {e}")
            raise 