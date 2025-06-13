"""
Analytics Domain Models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...db.core_models import Base


class Integration(Base):
    """Integration configurations for external services"""
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # email, crm, analytics, etc.
    config = Column(JSON)  # Integration-specific configuration
    credentials = Column(JSON)  # Encrypted credentials
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="integrations")


class AnalyticsReport(Base):
    """Store generated analytics reports"""
    __tablename__ = "analytics_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(100), nullable=False)  # lead_performance, campaign_roi, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_data = Column(JSON)  # The actual report data
    filters = Column(JSON)  # Filters used to generate the report
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")