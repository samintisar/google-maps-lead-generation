"""
Pydantic schemas for API request and response validation.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import UserRole, LeadStatus, LeadSource


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
    first_contacted_at: Optional[datetime] = None
    last_contacted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    organization: Optional[OrganizationResponse] = None
    assigned_to: Optional[UserResponse] = None


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