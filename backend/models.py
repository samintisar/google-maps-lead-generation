"""
Database models for the Lead Management Automation Platform.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime


class UserRole(enum.Enum):
    """User roles enum."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SALES_REP = "SALES_REP"
    VIEWER = "VIEWER"


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
    WEBSITE = "WEBSITE"
    EMAIL = "EMAIL"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    REFERRAL = "REFERRAL"
    ADVERTISING = "ADVERTISING"
    COLD_OUTREACH = "COLD_OUTREACH"
    EVENT = "EVENT"
    OTHER = "OTHER"


class LeadTemperature(enum.Enum):
    """Lead temperature enum."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class CommunicationType(enum.Enum):
    """Communication type enum."""
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    LINKEDIN = "linkedin"
    SMS = "sms"


class CommunicationDirection(enum.Enum):
    """Communication direction enum."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CommunicationStatus(enum.Enum):
    """Communication status enum."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CampaignStatus(enum.Enum):
    """Campaign status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IntegrationStatus(enum.Enum):
    """Integration status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    EXPIRED = "expired"


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
    
    # Enhanced fields
    timezone = Column(String(50), default='UTC', nullable=False)
    preferences = Column(JSON, default={}, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    leads = relationship("Lead", back_populates="assigned_to")
    communications = relationship("Communication", back_populates="user")
    lead_notes = relationship("LeadNote", back_populates="user")
    workflows = relationship("Workflow", back_populates="created_by_user")
    campaigns = relationship("Campaign", back_populates="created_by_user")
    integrations = relationship("Integration", back_populates="created_by_user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    
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
    
    # Enhanced fields
    subscription_tier = Column(String(50), default='free', nullable=False)
    billing_email = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    leads = relationship("Lead", back_populates="organization")
    workflows = relationship("Workflow", back_populates="organization")
    campaigns = relationship("Campaign", back_populates="organization")
    lead_scoring_rules = relationship("LeadScoringRule", back_populates="organization")
    integrations = relationship("Integration", back_populates="organization")
    
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
    
    # Enhanced fields
    linkedin_url = Column(String(500), nullable=True)
    lead_temperature = Column(Enum(LeadTemperature, values_callable=lambda x: [e.value for e in x]), default=LeadTemperature.COLD, nullable=False)
    expected_close_date = Column(Date, nullable=True)
    last_engagement_date = Column(DateTime(timezone=True), nullable=True)
    
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
    communications = relationship("Communication", back_populates="lead")
    lead_notes = relationship("LeadNote", back_populates="lead")
    workflow_executions = relationship("WorkflowExecution", back_populates="lead")
    activity_logs = relationship("ActivityLog", back_populates="lead")
    score_history = relationship("LeadScoreHistory", back_populates="lead")
    assignments = relationship("LeadAssignment", back_populates="lead")
    campaign_leads = relationship("CampaignLead", back_populates="lead")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"{self.full_name} ({self.email})"


class Workflow(Base):
    """Workflow model for n8n workflow templates."""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    n8n_workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # lead_nurturing, follow_up, qualification, etc.
    trigger_type = Column(String(100), nullable=True, index=True)  # manual, scheduled, event_based, lead_status_change
    trigger_conditions = Column(JSON, default={}, nullable=False)
    configuration = Column(JSON, default={}, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    created_by_user = relationship("User", back_populates="workflows")
    # Remove the problematic executions relationship for now
    # executions = relationship("WorkflowExecution", back_populates="workflow")


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
    lead = relationship("Lead", back_populates="workflow_executions")
    # Remove the problematic workflow relationship for now
    # workflow = relationship("Workflow", back_populates="executions", foreign_keys=[workflow_id], primaryjoin="WorkflowExecution.workflow_id == Workflow.n8n_workflow_id")


class LeadScoringRule(Base):
    """Lead scoring rules for automated scoring."""
    __tablename__ = "lead_scoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False, index=True)  # demographic, behavioral, engagement, firmographic
    criteria = Column(JSON, nullable=False)  # JSON conditions for scoring
    score_points = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # Higher priority rules applied first
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="lead_scoring_rules")
    score_history = relationship("LeadScoreHistory", back_populates="rule")


class LeadScoreHistory(Base):
    """Lead score change history."""
    __tablename__ = "lead_score_history"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    previous_score = Column(Integer, nullable=False)
    new_score = Column(Integer, nullable=False)
    score_change = Column(Integer, nullable=False)  # calculated: new_score - previous_score
    reason = Column(String(500), nullable=True)  # reason for score change
    rule_id = Column(Integer, ForeignKey("lead_scoring_rules.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="score_history")
    rule = relationship("LeadScoringRule", back_populates="score_history")


class Communication(Base):
    """Communication log for tracking lead interactions."""
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    communication_type = Column(Enum(CommunicationType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    direction = Column(Enum(CommunicationDirection, values_callable=lambda x: [e.value for e in x]), nullable=False)
    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(Enum(CommunicationStatus, values_callable=lambda x: [e.value for e in x]), default=CommunicationStatus.COMPLETED, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    comm_metadata = Column(JSON, default={}, nullable=False)  # email headers, call duration, meeting attendees, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="communications")
    user = relationship("User", back_populates="communications")


class LeadNote(Base):
    """Lead notes for detailed notes and collaboration."""
    __tablename__ = "lead_notes"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note_type = Column(String(50), default='general', nullable=False, index=True)  # general, meeting, call, research, reminder
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)  # Private to the user who created it
    mentioned_users = Column(JSON, default=[], nullable=False)  # Array of user IDs mentioned in the note (stored as JSON)
    attachments = Column(JSON, default=[], nullable=False)  # Array of attachment metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="lead_notes")
    user = relationship("User", back_populates="lead_notes")


class Campaign(Base):
    """Campaign model for organizing marketing/outreach campaigns."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(String(100), nullable=True, index=True)  # email, cold_outreach, content, social, event
    status = Column(Enum(CampaignStatus, values_callable=lambda x: [e.value for e in x]), default=CampaignStatus.DRAFT, nullable=False, index=True)
    target_criteria = Column(JSON, default={}, nullable=False)  # JSON criteria for lead targeting
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    budget_allocated = Column(Integer, nullable=True)  # in cents
    budget_spent = Column(Integer, default=0, nullable=False)  # in cents
    goals = Column(JSON, default={}, nullable=False)  # campaign goals and KPIs
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="campaigns")
    created_by_user = relationship("User", back_populates="campaigns")
    campaign_leads = relationship("CampaignLead", back_populates="campaign")


class CampaignLead(Base):
    """Many-to-many relationship between campaigns and leads."""
    __tablename__ = "campaign_leads"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default='pending', nullable=False, index=True)  # pending, contacted, responded, converted, excluded
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    response_at = Column(DateTime(timezone=True), nullable=True)
    conversion_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_leads")
    lead = relationship("Lead", back_populates="campaign_leads")
    
    # Unique constraint
    __table_args__ = (
        {'extend_existing': True},
    )


class Integration(Base):
    """Integration model for managing external system connections."""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    integration_type = Column(String(100), nullable=False, index=True)  # crm, email_provider, social, calendar, etc.
    provider_name = Column(String(100), nullable=False)  # salesforce, hubspot, gmail, outlook, etc.
    display_name = Column(String(255), nullable=True)
    configuration = Column(JSON, nullable=False)  # API keys, endpoints, settings (encrypted)
    status = Column(Enum(IntegrationStatus, values_callable=lambda x: [e.value for e in x]), default=IntegrationStatus.ACTIVE, nullable=False, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_frequency_minutes = Column(Integer, default=60, nullable=False)
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="integrations")
    created_by_user = relationship("User", back_populates="integrations")


class LeadAssignment(Base):
    """Lead assignment history for tracking lead ownership changes."""
    __tablename__ = "lead_assignments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    assigned_from = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(500), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="assignments")


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
    lead = relationship("Lead", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs") 