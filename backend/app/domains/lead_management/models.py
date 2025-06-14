"""
Lead Management Domain Models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...db.core_models import Base


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, default=1)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    company = Column(String(255))
    industry = Column(String(100))  # Added: Business industry/category
    website = Column(String(500))   # Added: Company website URL
    address = Column(Text)          # Added: Business address
    google_maps_url = Column(String(500))  # Added: Google Maps link
    status = Column(String(100), default="new")
    source = Column(String(100))
    score = Column(Float, default=0.0)
    notes = Column(Text)
    
    # Enrichment fields from Perplexity API
    linkedin_profile = Column(String(500))  # LinkedIn profile URL
    twitter_profile = Column(String(500))   # Twitter/X profile URL
    facebook_profile = Column(String(500))  # Facebook profile URL
    instagram_profile = Column(String(500)) # Instagram profile URL
    ideal_customer_profile = Column(Text)   # Descriptive ICP analysis
    pain_points = Column(Text)              # Identified pain points
    key_goals = Column(Text)                # Business goals and objectives
    company_description = Column(Text)      # Company overview from web research
    recent_news = Column(Text)              # Recent company news/updates
    key_personnel = Column(JSONB)           # Key decision makers and contacts (PostgreSQL JSONB)
    enrichment_status = Column(String(50), default="pending")  # pending, completed, failed
    enriched_at = Column(DateTime(timezone=True))  # When enrichment was completed
    enrichment_confidence = Column(Float, default=0.0)  # Confidence score of enrichment data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="leads")
    activities = relationship("Activity", back_populates="lead")
    campaign_leads = relationship("CampaignLead", back_populates="lead")
    lead_scoring_rules = relationship("LeadScoringRule", back_populates="lead")


class Activity(Base):
    """Unified Activity System - replaces separate activity tables"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(100), nullable=False)  # email, call, meeting, note, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(100), default="completed")
    scheduled_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    activity_data = Column(JSONB)  # Flexible field for activity-specific data (PostgreSQL JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    user = relationship("User", back_populates="activities")


class LeadScoringRule(Base):
    """Lead Scoring System - single table instead of separate rule/score tables"""
    __tablename__ = "lead_scoring_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)  # Null for global rules
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rule_type = Column(String(100), nullable=False)  # demographic, behavioral, engagement
    conditions = Column(JSONB)  # Rule conditions and criteria (PostgreSQL JSONB)
    score_value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="lead_scoring_rules")
    lead = relationship("Lead", back_populates="lead_scoring_rules")