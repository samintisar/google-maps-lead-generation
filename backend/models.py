"""
Database models for the Lead Management Automation Platform.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime


class UserRole(enum.Enum):
    """User roles enum."""
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class LeadStatus(enum.Enum):
    """Lead status enum."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(enum.Enum):
    """Lead source enum."""
    WEBSITE = "website"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    ADVERTISING = "advertising"
    COLD_OUTREACH = "cold_outreach"
    EVENT = "event"
    OTHER = "other"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.SALES_REP, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    leads = relationship("Lead", back_populates="assigned_to")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"{self.full_name} ({self.email})"


class Organization(Base):
    """Organization model for multi-tenancy."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # startup, small, medium, large, enterprise
    settings = Column(JSON, nullable=True)  # Organization-specific settings
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    leads = relationship("Lead", back_populates="organization")
    
    def __repr__(self):
        return self.name


class Lead(Base):
    """Lead model for managing potential customers."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(255), nullable=True, index=True)
    job_title = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Lead management fields
    status = Column(Enum(LeadStatus, values_callable=lambda x: [e.value for e in x]), default=LeadStatus.NEW, nullable=False, index=True)
    source = Column(Enum(LeadSource, values_callable=lambda x: [e.value for e in x]), default=LeadSource.OTHER, nullable=False, index=True)
    score = Column(Integer, default=0, nullable=False)  # Lead scoring 0-100
    value = Column(Integer, nullable=True)  # Potential deal value in cents
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    custom_fields = Column(JSON, nullable=True)  # Flexible custom data
    
    # Tracking fields
    first_contacted_at = Column(DateTime(timezone=True), nullable=True)
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="leads")
    assigned_to = relationship("User", back_populates="leads")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"{self.full_name} ({self.email})"


class WorkflowExecution(Base):
    """Track n8n workflow executions for leads."""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)  # n8n workflow ID
    execution_id = Column(String(100), nullable=False, index=True)  # n8n execution ID
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    status = Column(String(50), nullable=False)  # running, success, error, cancelled
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    execution_data = Column(JSON, nullable=True)  # Store execution details
    
    # Relationships
    lead = relationship("Lead")


class ActivityLog(Base):
    """Activity log for tracking lead interactions and system events."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    activity_type = Column(String(100), nullable=False, index=True)  # email_sent, call_made, note_added, etc.
    description = Column(String(500), nullable=False)
    activity_metadata = Column(JSON, nullable=True)  # Additional activity data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead")
    user = relationship("User") 