"""
Organization management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Organization, User, UserRole
from schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    APIResponse, ListResponse
)
from routers.auth import get_current_active_user

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new organization (admin only)."""
    # Only admins can create organizations
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create organizations"
        )
    
    # Check if organization with same slug already exists
    existing_org = db.query(Organization).filter(
        Organization.slug == org_data.slug
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this slug already exists"
        )
    
    # Create new organization
    db_org = Organization(**org_data.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    return APIResponse(
        success=True,
        data=OrganizationResponse.model_validate(db_org),
        message="Organization created successfully"
    )


@router.get("/", response_model=ListResponse)
async def get_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in organization name"),
    active_only: bool = Query(True, description="Show only active organizations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get organizations (admin sees all, users see their own)."""
    query = db.query(Organization)
    
    # Non-admin users can only see their own organization
    if current_user.role != UserRole.ADMIN:
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not assigned to any organization"
            )
        query = query.filter(Organization.id == current_user.organization_id)
    
    # Apply filters
    if active_only:
        query = query.filter(Organization.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(Organization.name.ilike(search_term))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    organizations = query.offset(skip).limit(limit).all()
    
    return ListResponse(
        items=[OrganizationResponse.model_validate(org) for org in organizations],
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific organization by ID."""
    # Non-admin users can only access their own organization
    if current_user.role != UserRole.ADMIN and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse.model_validate(organization)


@router.put("/{org_id}", response_model=APIResponse)
async def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an organization."""
    # Only admins or managers from the same org can update
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check permissions
    if (current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] or 
        (current_user.role == UserRole.MANAGER and current_user.organization_id != org_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this organization"
        )
    
    # Update fields
    update_data = org_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    return APIResponse(
        success=True,
        data=OrganizationResponse.model_validate(organization),
        message="Organization updated successfully"
    )


@router.delete("/{org_id}", response_model=APIResponse)
async def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an organization (admin only)."""
    # Only admins can delete organizations
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if organization has users
    user_count = db.query(User).filter(User.organization_id == org_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete organization with existing users"
        )
    
    db.delete(organization)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Organization deleted successfully"
    )


@router.patch("/{org_id}/deactivate", response_model=APIResponse)
async def deactivate_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate an organization (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    organization.is_active = False
    db.commit()
    
    return APIResponse(
        success=True,
        data=OrganizationResponse.model_validate(organization),
        message="Organization deactivated successfully"
    )


@router.patch("/{org_id}/activate", response_model=APIResponse)
async def activate_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activate an organization (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    organization.is_active = True
    db.commit()
    
    return APIResponse(
        success=True,
        data=OrganizationResponse.model_validate(organization),
        message="Organization activated successfully"
    ) 