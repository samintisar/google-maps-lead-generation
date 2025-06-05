"""
Pydantic schemas for API request and response validation.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from models import (
    UserRole, LeadStatus, LeadSource, LeadTemperature,
    CommunicationType, CommunicationDirection, CommunicationStatus,
    CampaignStatus, IntegrationStatus
)


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.SALES_REP
    timezone: str = 'UTC'
    preferences: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseSchema):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[int] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserLogin(BaseSchema):
    """Schema for user login."""
    username: str  # Can be username or email
    password: str


class Token(BaseSchema):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Organization schemas
class OrganizationBase(BaseSchema):
    """Base organization schema."""
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    subscription_tier: str = 'free'
    billing_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationCreate(OrganizationBase):
    """Schema for organization creation."""
    pass


class OrganizationUpdate(BaseSchema):
    """Schema for organization updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    subscription_tier: Optional[str] = None
    billing_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization responses."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Lead schemas
class LeadBase(BaseSchema):
    """Base lead schema."""
    email: EmailStr
    first_name: str
    last_name: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    lead_temperature: LeadTemperature = LeadTemperature.COLD
    expected_close_date: Optional[date] = None
    status: LeadStatus = LeadStatus.NEW
    source: LeadSource = LeadSource.OTHER
    score: int = 0
    value: Optional[int] = None  # Value in cents
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    assigned_to_id: Optional[int] = None


class LeadCreate(LeadBase):
    """Schema for lead creation."""
    organization_id: int
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        """Validate lead score is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError('Lead score must be between 0 and 100')
        return v


class LeadUpdate(BaseSchema):
    """Schema for lead updates."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    lead_temperature: Optional[LeadTemperature] = None
    expected_close_date: Optional[date] = None
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None
    score: Optional[int] = None
    value: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    assigned_to_id: Optional[int] = None
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        """Validate lead score is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Lead score must be between 0 and 100')
        return v


class LeadResponse(LeadBase):
    """Schema for lead responses."""
    id: int
    organization_id: int
    last_engagement_date: Optional[datetime] = None
    first_contacted_at: Optional[datetime] = None
    last_contacted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    organization: Optional[OrganizationResponse] = None
    assigned_to: Optional[UserResponse] = None


# Workflow schemas
class WorkflowBase(BaseSchema):
    """Base workflow schema."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: bool = True


class WorkflowCreate(WorkflowBase):
    """Schema for workflow creation."""
    organization_id: int
    n8n_workflow_id: str


class WorkflowUpdate(BaseSchema):
    """Schema for workflow updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow responses."""
    id: int
    organization_id: int
    n8n_workflow_id: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Lead Scoring Rule schemas
class LeadScoringRuleBase(BaseSchema):
    """Base lead scoring rule schema."""
    name: str
    description: Optional[str] = None
    rule_type: str
    criteria: Dict[str, Any]
    score_points: int
    is_active: bool = True
    priority: int = 1


class LeadScoringRuleCreate(LeadScoringRuleBase):
    """Schema for lead scoring rule creation."""
    organization_id: int


class LeadScoringRuleUpdate(BaseSchema):
    """Schema for lead scoring rule updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    score_points: Optional[int] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class LeadScoringRuleResponse(LeadScoringRuleBase):
    """Schema for lead scoring rule responses."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


# Lead Score History schemas
class LeadScoreHistoryResponse(BaseSchema):
    """Schema for lead score history responses."""
    id: int
    lead_id: int
    previous_score: int
    new_score: int
    score_change: int
    reason: Optional[str] = None
    rule_id: Optional[int] = None
    created_at: datetime


# Communication schemas
class CommunicationBase(BaseSchema):
    """Base communication schema."""
    communication_type: CommunicationType
    direction: CommunicationDirection
    subject: Optional[str] = None
    content: Optional[str] = None
    status: CommunicationStatus = CommunicationStatus.COMPLETED
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    comm_metadata: Optional[Dict[str, Any]] = None


class CommunicationCreate(CommunicationBase):
    """Schema for communication creation."""
    lead_id: int
    user_id: Optional[int] = None


class CommunicationUpdate(BaseSchema):
    """Schema for communication updates."""
    subject: Optional[str] = None
    content: Optional[str] = None
    status: Optional[CommunicationStatus] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    comm_metadata: Optional[Dict[str, Any]] = None


class CommunicationResponse(CommunicationBase):
    """Schema for communication responses."""
    id: int
    lead_id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Lead Note schemas
class LeadNoteBase(BaseSchema):
    """Base lead note schema."""
    note_type: str = 'general'
    content: str
    is_private: bool = False
    mentioned_users: Optional[List[int]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class LeadNoteCreate(LeadNoteBase):
    """Schema for lead note creation."""
    lead_id: int
    user_id: Optional[int] = None


class LeadNoteUpdate(BaseSchema):
    """Schema for lead note updates."""
    note_type: Optional[str] = None
    content: Optional[str] = None
    is_private: Optional[bool] = None
    mentioned_users: Optional[List[int]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class LeadNoteResponse(LeadNoteBase):
    """Schema for lead note responses."""
    id: int
    lead_id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Campaign schemas
class CampaignBase(BaseSchema):
    """Base campaign schema."""
    name: str
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    target_criteria: Optional[Dict[str, Any]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_allocated: Optional[int] = None  # in cents
    budget_spent: int = 0  # in cents
    goals: Optional[Dict[str, Any]] = None


class CampaignCreate(CampaignBase):
    """Schema for campaign creation."""
    organization_id: int


class CampaignUpdate(BaseSchema):
    """Schema for campaign updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    status: Optional[CampaignStatus] = None
    target_criteria: Optional[Dict[str, Any]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_allocated: Optional[int] = None
    budget_spent: Optional[int] = None
    goals: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign responses."""
    id: int
    organization_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Campaign Lead schemas
class CampaignLeadBase(BaseSchema):
    """Base campaign lead schema."""
    status: str = 'pending'


class CampaignLeadCreate(CampaignLeadBase):
    """Schema for campaign lead creation."""
    campaign_id: int
    lead_id: int


class CampaignLeadUpdate(BaseSchema):
    """Schema for campaign lead updates."""
    status: Optional[str] = None
    last_contact_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    conversion_at: Optional[datetime] = None


class CampaignLeadResponse(CampaignLeadBase):
    """Schema for campaign lead responses."""
    id: int
    campaign_id: int
    lead_id: int
    added_at: datetime
    last_contact_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    conversion_at: Optional[datetime] = None


# Integration schemas
class IntegrationBase(BaseSchema):
    """Base integration schema."""
    integration_type: str
    provider_name: str
    display_name: Optional[str] = None
    configuration: Dict[str, Any]
    status: IntegrationStatus = IntegrationStatus.ACTIVE
    sync_frequency_minutes: int = 60


class IntegrationCreate(IntegrationBase):
    """Schema for integration creation."""
    organization_id: int


class IntegrationUpdate(BaseSchema):
    """Schema for integration updates."""
    display_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[IntegrationStatus] = None
    sync_frequency_minutes: Optional[int] = None


class IntegrationResponse(IntegrationBase):
    """Schema for integration responses."""
    id: int
    organization_id: int
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Lead Assignment schemas
class LeadAssignmentResponse(BaseSchema):
    """Schema for lead assignment responses."""
    id: int
    lead_id: int
    assigned_from: Optional[int] = None
    assigned_to: Optional[int] = None
    assigned_by: Optional[int] = None
    reason: Optional[str] = None
    assigned_at: datetime


# Activity log schemas
class ActivityLogBase(BaseSchema):
    """Base activity log schema."""
    activity_type: str
    description: str
    activity_metadata: Optional[Dict[str, Any]] = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for activity log creation."""
    lead_id: Optional[int] = None
    user_id: Optional[int] = None


class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log responses."""
    id: int
    lead_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime


# Workflow execution schemas
class WorkflowExecutionResponse(BaseSchema):
    """Schema for workflow execution responses."""
    id: int
    workflow_id: str
    execution_id: str
    lead_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_data: Optional[Dict[str, Any]] = None


# Common response schemas
class MessageResponse(BaseSchema):
    """Schema for simple message responses."""
    message: str


class ListResponse(BaseSchema):
    """Schema for paginated list responses."""
    items: List[Any]
    total: int
    page: int = 1
    per_page: int = 50
    pages: int


# API response wrapper
class APIResponse(BaseSchema):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None


# Lead Enrichment schemas
class LeadEnrichmentRequest(BaseSchema):
    """Schema for lead enrichment requests."""
    enrichment_types: Optional[List[str]] = None


class ValidationResult(BaseSchema):
    """Schema for validation results."""
    is_valid: bool
    error: Optional[str] = None
    normalized_email: Optional[str] = None
    domain: Optional[str] = None
    local_part: Optional[str] = None
    ascii_email: Optional[str] = None
    ascii_domain: Optional[str] = None
    digits_only: Optional[str] = None


class FormattedData(BaseSchema):
    """Schema for formatted data results."""
    national: Optional[str] = None
    international: Optional[str] = None
    e164: Optional[str] = None


class EnrichmentData(BaseSchema):
    """Schema for individual enrichment data."""
    original_email: Optional[str] = None
    original_phone: Optional[str] = None
    original_company: Optional[str] = None
    original_website: Optional[str] = None
    validation: Optional[ValidationResult] = None
    formatted: Optional[FormattedData] = None
    domain_info: Optional[Dict[str, Any]] = None
    reputation: Optional[Dict[str, Any]] = None
    normalized_company: Optional[str] = None
    industry: Optional[str] = None
    size_estimate: Optional[str] = None
    social_profiles: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class NormalizationData(BaseSchema):
    """Schema for data normalization results."""
    original_data: Optional[Dict[str, Any]] = None
    normalized_data: Optional[Dict[str, Any]] = None
    changes: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None


class DuplicateMatch(BaseSchema):
    """Schema for duplicate match information."""
    lead_id: int
    match_type: str
    score: int
    matched_field: str
    matched_value: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None


class DeduplicationData(BaseSchema):
    """Schema for deduplication results."""
    potential_duplicates: List[DuplicateMatch] = []
    duplicate_score: int = 0
    matching_criteria: List[str] = []
    errors: Optional[List[str]] = None


class EnrichmentMetadata(BaseSchema):
    """Schema for enrichment metadata."""
    enriched_at: str
    processing_time_ms: float


class LeadEnrichmentResponse(BaseSchema):
    """Schema for lead enrichment responses."""
    lead_id: int
    enrichment_types: List[str]
    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    data_sources: List[str]
    validation_results: Dict[str, Any]
    errors: List[str]
    metadata: EnrichmentMetadata


class BulkEnrichmentRequest(BaseSchema):
    """Schema for bulk enrichment requests."""
    lead_ids: Optional[List[int]] = None
    enrichment_types: Optional[List[str]] = None
    batch_size: int = 10
    async_mode: bool = False


class BulkEnrichmentResult(BaseSchema):
    """Schema for individual bulk enrichment result."""
    lead_id: int
    success: bool
    error: Optional[str] = None
    enrichment_data: Optional[LeadEnrichmentResponse] = None


class BulkEnrichmentResponse(BaseSchema):
    """Schema for bulk enrichment responses."""
    total_leads: int
    enriched_leads: int
    failed_leads: int
    results: List[BulkEnrichmentResult] = []
    errors: List[Dict[str, Any]] = []


class EnrichmentStatusResponse(BaseSchema):
    """Schema for enrichment status responses."""
    lead_id: int
    has_been_enriched: bool
    last_enriched: Optional[str] = None
    enrichment_types: List[str] = []
    data_sources: List[str] = []
    validation_results: Dict[str, Any] = {}
    duplicate_check: Dict[str, Any] = {}
    enriched_fields: Dict[str, Any] = {}


class ValidationRequest(BaseSchema):
    """Schema for validation requests."""
    validation_types: Optional[List[str]] = None


class ValidationResponse(BaseSchema):
    """Schema for validation responses."""
    lead_id: int
    validation_types: List[str]
    validation_results: Dict[str, Any]
    validated_at: str


class DuplicateSearchResponse(BaseSchema):
    """Schema for duplicate search responses."""
    lead_id: int
    duplicate_score: int
    potential_duplicates_count: int
    potential_duplicates: List[DuplicateMatch]
    matching_criteria: List[str]


class EnrichmentType(BaseSchema):
    """Schema for enrichment type information."""
    name: str
    description: str
    data_sources: List[str]


class EnrichmentTypesResponse(BaseSchema):
    """Schema for available enrichment types response."""
    enrichment_types: Dict[str, EnrichmentType]
    default_types: List[str]
    total_types: int 