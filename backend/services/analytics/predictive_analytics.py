"""
Predictive Analytics Module

Provides predictive modeling capabilities including lead conversion probability,
revenue forecasting, and customer lifetime value prediction.
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from models import (
    Lead, Communication, LeadScoreHistory, ActivityLog, Campaign, 
    CampaignLead, User, Organization, LeadStatus, LeadSource, 
    LeadTemperature, CommunicationType
)

logger = logging.getLogger(__name__)

class ConversionProbability(Enum):
    """Lead conversion probability categories"""
    VERY_HIGH = "very_high"    # > 80%
    HIGH = "high"              # 60-80%
    MODERATE = "moderate"      # 40-60%
    LOW = "low"                # 20-40%
    VERY_LOW = "very_low"      # < 20%

@dataclass
class ConversionPrediction:
    """Lead conversion prediction result"""
    lead_id: int
    conversion_probability: float
    probability_category: ConversionProbability
    confidence_score: float
    key_factors: List[Dict[str, Any]]
    recommended_actions: List[str]
    predicted_conversion_date: Optional[datetime]
    model_accuracy: float

@dataclass
class RevenueForcast:
    """Revenue forecasting result"""
    period: str
    predicted_revenue: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    contributing_factors: List[Dict[str, Any]]
    forecast_accuracy: float
    methodology: str

class PredictiveAnalytics:
    """
    Advanced predictive analytics for lead conversion and revenue forecasting.
    """
    
    def __init__(self, db: Session):
        """Initialize the predictive analytics engine."""
        self.db = db
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Model parameters
        self.random_state = 42
        self.test_size = 0.2
        self.cv_folds = 5
    
    async def predict_lead_conversion(
        self, 
        lead_id: int,
        model_type: str = "random_forest"
    ) -> ConversionPrediction:
        """
        Predict the probability of lead conversion using machine learning.
        
        Args:
            lead_id: ID of the lead to predict
            model_type: "random_forest" or "logistic_regression"
        """
        try:
            # Get lead data
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Prepare training data from historical leads
            training_data = await self._prepare_conversion_training_data(lead.organization_id)
            
            if len(training_data) < 20:
                raise ValueError("Insufficient historical data for reliable prediction")
            
            # Extract features and target
            X, y, feature_names = self._extract_conversion_features(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            if model_type == "random_forest":
                model = RandomForestClassifier(
                    n_estimators=100, 
                    random_state=self.random_state,
                    max_depth=10,
                    min_samples_split=5
                )
            else:
                model = LogisticRegression(
                    random_state=self.random_state,
                    max_iter=1000
                )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=self.cv_folds)
            
            # Prepare current lead features
            lead_features = await self._extract_lead_features(lead)
            lead_features_scaled = self.scaler.transform([lead_features])
            
            # Make prediction
            conversion_prob = model.predict_proba(lead_features_scaled)[0][1]  # Probability of class 1 (converted)
            
            # Categorize probability
            if conversion_prob >= 0.8:
                prob_category = ConversionProbability.VERY_HIGH
            elif conversion_prob >= 0.6:
                prob_category = ConversionProbability.HIGH
            elif conversion_prob >= 0.4:
                prob_category = ConversionProbability.MODERATE
            elif conversion_prob >= 0.2:
                prob_category = ConversionProbability.LOW
            else:
                prob_category = ConversionProbability.VERY_LOW
            
            # Get feature importance
            key_factors = self._get_feature_importance(model, feature_names, lead_features)
            
            # Generate recommendations
            recommended_actions = self._generate_conversion_recommendations(
                lead, conversion_prob, key_factors
            )
            
            # Predict conversion timeline
            predicted_date = self._predict_conversion_timeline(lead, conversion_prob)
            
            # Calculate confidence score
            confidence_score = min(cv_scores.std(), 1.0)  # Lower std = higher confidence
            
            return ConversionPrediction(
                lead_id=lead_id,
                conversion_probability=conversion_prob,
                probability_category=prob_category,
                confidence_score=confidence_score,
                key_factors=key_factors,
                recommended_actions=recommended_actions,
                predicted_conversion_date=predicted_date,
                model_accuracy=accuracy
            )
            
        except Exception as e:
            logger.error(f"Error predicting lead conversion for {lead_id}: {e}")
            raise
    
    async def forecast_revenue(
        self,
        organization_id: int,
        forecast_days: int = 90,
        model_type: str = "random_forest"
    ) -> RevenueForcast:
        """
        Forecast revenue for the specified period using historical data.
        
        Args:
            organization_id: Organization to forecast for
            forecast_days: Number of days to forecast
            model_type: "random_forest" or "linear_regression"
        """
        try:
            # Prepare training data
            revenue_data = await self._prepare_revenue_training_data(organization_id)
            
            if len(revenue_data) < 30:
                raise ValueError("Insufficient historical data for revenue forecasting")
            
            # Extract features and target
            X, y, feature_names = self._extract_revenue_features(revenue_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            if model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    random_state=self.random_state,
                    max_depth=15
                )
            else:
                model = LinearRegression()
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            # Prepare future features
            future_features = await self._prepare_future_features(organization_id, forecast_days)
            future_features_scaled = self.scaler.transform([future_features])
            
            # Make forecast
            predicted_revenue = model.predict(future_features_scaled)[0]
            
            # Calculate confidence interval (simple approach)
            prediction_std = np.sqrt(mean_squared_error(y_test, y_pred))
            confidence_interval = (
                predicted_revenue - 1.96 * prediction_std,
                predicted_revenue + 1.96 * prediction_std
            )
            
            # Calculate growth rate
            recent_revenue = await self._get_recent_revenue(organization_id, forecast_days)
            growth_rate = ((predicted_revenue - recent_revenue) / recent_revenue * 100) if recent_revenue > 0 else 0
            
            # Get contributing factors
            contributing_factors = self._get_revenue_factors(model, feature_names, future_features)
            
            return RevenueForcast(
                period=f"Next {forecast_days} days",
                predicted_revenue=predicted_revenue,
                confidence_interval=confidence_interval,
                growth_rate=growth_rate,
                contributing_factors=contributing_factors,
                forecast_accuracy=r2,
                methodology=model_type
            )
            
        except Exception as e:
            logger.error(f"Error forecasting revenue for organization {organization_id}: {e}")
            raise
    
    async def calculate_customer_lifetime_value(
        self,
        organization_id: int,
        customer_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value (CLV) for leads/customers.
        """
        try:
            # Get historical customer data
            base_query = self.db.query(Lead).filter(
                and_(
                    Lead.organization_id == organization_id,
                    Lead.status == LeadStatus.CLOSED_WON
                )
            )
            
            if customer_segment:
                base_query = base_query.filter(Lead.tags.contains([customer_segment]))
            
            won_leads = base_query.all()
            
            if len(won_leads) < 10:
                raise ValueError("Insufficient customer data for CLV calculation")
            
            # Calculate CLV components
            total_revenue = sum([lead.value or 0 for lead in won_leads])
            customer_count = len(won_leads)
            
            # Average order value
            aov = total_revenue / customer_count if customer_count > 0 else 0
            
            # Calculate purchase frequency (simplified)
            total_communications = self.db.query(Communication).filter(
                Communication.lead_id.in_([lead.id for lead in won_leads])
            ).count()
            
            purchase_frequency = total_communications / customer_count if customer_count > 0 else 1
            
            # Customer lifespan (days between first and last interaction)
            lifespans = []
            for lead in won_leads:
                first_contact = lead.created_at
                last_contact = lead.updated_at
                lifespan_days = (last_contact - first_contact).days
                lifespans.append(max(lifespan_days, 1))  # Minimum 1 day
            
            avg_lifespan_days = sum(lifespans) / len(lifespans) if lifespans else 30
            
            # Calculate CLV
            clv = aov * purchase_frequency * (avg_lifespan_days / 365)  # Annualized
            
            return {
                "customer_lifetime_value": clv,
                "average_order_value": aov,
                "purchase_frequency": purchase_frequency,
                "average_lifespan_days": avg_lifespan_days,
                "customer_count": customer_count,
                "total_revenue": total_revenue,
                "segment": customer_segment or "all"
            }
            
        except Exception as e:
            logger.error(f"Error calculating CLV for organization {organization_id}: {e}")
            raise
    
    async def _prepare_conversion_training_data(self, organization_id: int) -> List[Dict[str, Any]]:
        """Prepare training data for conversion prediction."""
        # Get historical leads with known outcomes
        leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                or_(
                    Lead.status == LeadStatus.CLOSED_WON,
                    Lead.status == LeadStatus.CLOSED_LOST
                )
            )
        ).all()
        
        training_data = []
        for lead in leads:
            # Get lead communications
            communications = self.db.query(Communication).filter(
                Communication.lead_id == lead.id
            ).all()
            
            # Get score history
            score_history = self.db.query(LeadScoreHistory).filter(
                LeadScoreHistory.lead_id == lead.id
            ).order_by(desc(LeadScoreHistory.created_at)).all()
            
            training_data.append({
                "lead": lead,
                "communications": communications,
                "score_history": score_history,
                "converted": 1 if lead.status == LeadStatus.CLOSED_WON else 0
            })
        
        return training_data
    
    def _extract_conversion_features(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Extract features for conversion prediction."""
        features = []
        targets = []
        
        feature_names = [
            "lead_score", "days_since_creation", "communication_count", "email_count",
            "call_count", "meeting_count", "inbound_comm_ratio", "score_trend",
            "has_company", "has_phone", "has_linkedin", "source_score",
            "temperature_score", "response_rate"
        ]
        
        for data in training_data:
            lead = data["lead"]
            communications = data["communications"]
            score_history = data["score_history"]
            
            # Calculate features
            lead_features = []
            
            # Basic lead features
            lead_features.append(lead.score)
            lead_features.append((datetime.utcnow() - lead.created_at).days)
            lead_features.append(len(communications))
            
            # Communication type counts
            email_count = len([c for c in communications if c.communication_type == CommunicationType.EMAIL])
            call_count = len([c for c in communications if c.communication_type == CommunicationType.CALL])
            meeting_count = len([c for c in communications if c.communication_type == CommunicationType.MEETING])
            
            lead_features.extend([email_count, call_count, meeting_count])
            
            # Inbound communication ratio
            inbound_count = len([c for c in communications if c.direction.value == "inbound"])
            inbound_ratio = inbound_count / len(communications) if communications else 0
            lead_features.append(inbound_ratio)
            
            # Score trend
            if len(score_history) >= 2:
                recent_scores = [h.new_score for h in score_history[:5]]
                score_trend = (recent_scores[0] - recent_scores[-1]) / len(recent_scores)
            else:
                score_trend = 0
            lead_features.append(score_trend)
            
            # Profile completeness
            lead_features.append(1 if lead.company else 0)
            lead_features.append(1 if lead.phone else 0)
            lead_features.append(1 if lead.linkedin_url else 0)
            
            # Source scoring
            source_scores = {
                LeadSource.REFERRAL: 5,
                LeadSource.WEBSITE: 4,
                LeadSource.SOCIAL_MEDIA: 3,
                LeadSource.EMAIL: 3,
                LeadSource.ADVERTISING: 2,
                LeadSource.COLD_OUTREACH: 1,
                LeadSource.OTHER: 1
            }
            lead_features.append(source_scores.get(lead.source, 1))
            
            # Temperature scoring
            temp_scores = {
                LeadTemperature.HOT: 3,
                LeadTemperature.WARM: 2,
                LeadTemperature.COLD: 1
            }
            lead_features.append(temp_scores.get(lead.lead_temperature, 1))
            
            # Response rate (simplified)
            outbound_count = len([c for c in communications if c.direction.value == "outbound"])
            response_rate = inbound_count / outbound_count if outbound_count > 0 else 0
            lead_features.append(response_rate)
            
            features.append(lead_features)
            targets.append(data["converted"])
        
        return np.array(features), np.array(targets), feature_names
    
    async def _extract_lead_features(self, lead: Lead) -> List[float]:
        """Extract features for a single lead."""
        # Get communications
        communications = self.db.query(Communication).filter(
            Communication.lead_id == lead.id
        ).all()
        
        # Get score history
        score_history = self.db.query(LeadScoreHistory).filter(
            LeadScoreHistory.lead_id == lead.id
        ).order_by(desc(LeadScoreHistory.created_at)).all()
        
        features = []
        
        # Basic features
        features.append(lead.score)
        features.append((datetime.utcnow() - lead.created_at).days)
        features.append(len(communications))
        
        # Communication counts
        email_count = len([c for c in communications if c.communication_type == CommunicationType.EMAIL])
        call_count = len([c for c in communications if c.communication_type == CommunicationType.CALL])
        meeting_count = len([c for c in communications if c.communication_type == CommunicationType.MEETING])
        
        features.extend([email_count, call_count, meeting_count])
        
        # Inbound ratio
        inbound_count = len([c for c in communications if c.direction.value == "inbound"])
        inbound_ratio = inbound_count / len(communications) if communications else 0
        features.append(inbound_ratio)
        
        # Score trend
        if len(score_history) >= 2:
            recent_scores = [h.new_score for h in score_history[:5]]
            score_trend = (recent_scores[0] - recent_scores[-1]) / len(recent_scores)
        else:
            score_trend = 0
        features.append(score_trend)
        
        # Profile completeness
        features.append(1 if lead.company else 0)
        features.append(1 if lead.phone else 0)
        features.append(1 if lead.linkedin_url else 0)
        
        # Source and temperature scores (same as training)
        source_scores = {
            LeadSource.REFERRAL: 5,
            LeadSource.WEBSITE: 4,
            LeadSource.SOCIAL_MEDIA: 3,
            LeadSource.EMAIL: 3,
            LeadSource.ADVERTISING: 2,
            LeadSource.COLD_OUTREACH: 1,
            LeadSource.OTHER: 1
        }
        features.append(source_scores.get(lead.source, 1))
        
        temp_scores = {
            LeadTemperature.HOT: 3,
            LeadTemperature.WARM: 2,
            LeadTemperature.COLD: 1
        }
        features.append(temp_scores.get(lead.lead_temperature, 1))
        
        # Response rate
        outbound_count = len([c for c in communications if c.direction.value == "outbound"])
        response_rate = inbound_count / outbound_count if outbound_count > 0 else 0
        features.append(response_rate)
        
        return features
    
    def _get_feature_importance(
        self, 
        model, 
        feature_names: List[str], 
        lead_features: List[float]
    ) -> List[Dict[str, Any]]:
        """Get feature importance for the prediction."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = abs(model.coef_[0])
        else:
            return []
        
        # Combine feature names, values, and importances
        factors = []
        for i, (name, importance) in enumerate(zip(feature_names, importances)):
            factors.append({
                "factor": name,
                "importance": float(importance),
                "value": float(lead_features[i]),
                "impact": "high" if importance > np.mean(importances) else "medium" if importance > np.mean(importances) * 0.5 else "low"
            })
        
        # Sort by importance
        factors.sort(key=lambda x: x["importance"], reverse=True)
        
        return factors[:5]  # Top 5 factors
    
    def _generate_conversion_recommendations(
        self,
        lead: Lead,
        conversion_prob: float,
        key_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on prediction."""
        recommendations = []
        
        if conversion_prob < 0.3:
            recommendations.append("Consider lead nurturing campaigns to increase engagement")
            recommendations.append("Schedule a discovery call to understand pain points")
        elif conversion_prob < 0.6:
            recommendations.append("Provide targeted content based on lead interests")
            recommendations.append("Follow up with personalized outreach")
        else:
            recommendations.append("Prioritize this lead for immediate sales attention")
            recommendations.append("Prepare a customized proposal or demo")
        
        # Factor-based recommendations
        for factor in key_factors[:3]:
            if factor["factor"] == "communication_count" and factor["value"] < 3:
                recommendations.append("Increase communication frequency")
            elif factor["factor"] == "lead_score" and factor["value"] < 50:
                recommendations.append("Focus on activities that increase lead score")
            elif factor["factor"] == "inbound_comm_ratio" and factor["value"] < 0.2:
                recommendations.append("Encourage inbound responses with engaging content")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _predict_conversion_timeline(self, lead: Lead, conversion_prob: float) -> Optional[datetime]:
        """Predict when conversion might occur."""
        if conversion_prob < 0.2:
            return None
        
        # Simple timeline estimation based on probability and lead age
        days_since_creation = (datetime.utcnow() - lead.created_at).days
        
        if conversion_prob > 0.8:
            estimated_days = max(7, 30 - days_since_creation)
        elif conversion_prob > 0.6:
            estimated_days = max(14, 60 - days_since_creation)
        elif conversion_prob > 0.4:
            estimated_days = max(21, 90 - days_since_creation)
        else:
            estimated_days = max(30, 120 - days_since_creation)
        
        return datetime.utcnow() + timedelta(days=estimated_days)
    
    async def _prepare_revenue_training_data(self, organization_id: int) -> List[Dict[str, Any]]:
        """Prepare training data for revenue forecasting."""
        # Get historical won leads with revenue data
        won_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CLOSED_WON,
                Lead.value.isnot(None),
                Lead.value > 0
            )
        ).order_by(Lead.updated_at).all()
        
        # Group by month for revenue aggregation
        monthly_data = {}
        for lead in won_leads:
            month_key = lead.updated_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "revenue": 0,
                    "lead_count": 0,
                    "avg_deal_size": 0,
                    "month": lead.updated_at.replace(day=1)
                }
            
            monthly_data[month_key]["revenue"] += lead.value
            monthly_data[month_key]["lead_count"] += 1
        
        # Calculate average deal sizes
        for data in monthly_data.values():
            data["avg_deal_size"] = data["revenue"] / data["lead_count"]
        
        return list(monthly_data.values())
    
    def _extract_revenue_features(self, revenue_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Extract features for revenue forecasting."""
        features = []
        targets = []
        
        feature_names = [
            "month_numeric", "lead_count", "avg_deal_size", 
            "revenue_trend", "seasonal_factor"
        ]
        
        sorted_data = sorted(revenue_data, key=lambda x: x["month"])
        
        for i, data in enumerate(sorted_data):
            row_features = []
            
            # Month as numeric (for trend)
            row_features.append(i + 1)
            
            # Lead metrics
            row_features.append(data["lead_count"])
            row_features.append(data["avg_deal_size"])
            
            # Revenue trend (3-month moving average)
            if i >= 2:
                recent_revenues = [sorted_data[j]["revenue"] for j in range(i-2, i+1)]
                trend = (recent_revenues[-1] - recent_revenues[0]) / 3
            else:
                trend = 0
            row_features.append(trend)
            
            # Seasonal factor (simplified - month of year)
            month_factor = data["month"].month / 12
            row_features.append(month_factor)
            
            features.append(row_features)
            targets.append(data["revenue"])
        
        return np.array(features), np.array(targets), feature_names
    
    async def _prepare_future_features(self, organization_id: int, forecast_days: int) -> List[float]:
        """Prepare features for future revenue prediction."""
        # Get recent metrics for feature preparation
        recent_leads = self.db.query(Lead).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        # Estimate future features based on recent trends
        future_features = []
        
        # Month numeric (next period)
        future_features.append(forecast_days / 30)  # Simplified month representation
        
        # Estimated lead count (based on recent average)
        recent_lead_count = len(recent_leads)
        future_features.append(recent_lead_count * (forecast_days / 30))
        
        # Estimated average deal size (based on recent won deals)
        recent_won = [lead for lead in recent_leads if lead.status == LeadStatus.CLOSED_WON and lead.value]
        avg_deal_size = sum([lead.value for lead in recent_won]) / len(recent_won) if recent_won else 5000
        future_features.append(avg_deal_size)
        
        # Revenue trend (simplified)
        future_features.append(0)  # Neutral trend assumption
        
        # Seasonal factor
        future_month = (datetime.utcnow() + timedelta(days=forecast_days)).month
        future_features.append(future_month / 12)
        
        return future_features
    
    async def _get_recent_revenue(self, organization_id: int, days_back: int) -> float:
        """Get recent revenue for growth rate calculation."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        recent_revenue = self.db.query(func.sum(Lead.value)).filter(
            and_(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CLOSED_WON,
                Lead.updated_at >= cutoff_date,
                Lead.value.isnot(None)
            )
        ).scalar()
        
        return recent_revenue or 0
    
    def _get_revenue_factors(
        self, 
        model, 
        feature_names: List[str], 
        future_features: List[float]
    ) -> List[Dict[str, Any]]:
        """Get contributing factors for revenue forecast."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = abs(model.coef_)
        else:
            return []
        
        factors = []
        for i, (name, importance) in enumerate(zip(feature_names, importances)):
            factors.append({
                "factor": name,
                "importance": float(importance),
                "projected_value": float(future_features[i]),
                "impact": "high" if importance > np.mean(importances) else "medium"
            })
        
        factors.sort(key=lambda x: x["importance"], reverse=True)
        return factors[:3]  # Top 3 factors 