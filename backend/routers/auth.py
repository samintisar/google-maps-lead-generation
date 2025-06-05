"""
Authentication API endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db, get_redis
from models import User
from schemas import UserCreate, UserLogin, Token, UserResponse, MessageResponse, APIResponse
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token
)

from config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Dependencies
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(
        or_(User.username == username, User.email == username)
    ).first()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user





# Authentication endpoints
@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.email == user_data.email, User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role=user_data.role,
        organization_id=user_data.organization_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token for automatic login
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": db_user.username}, 
        expires_delta=access_token_expires
    )
    
    # Store token in Redis for session management
    redis.setex(
        f"token:{db_user.id}",
        int(access_token_expires.total_seconds()),
        access_token
    )
    
    # Return user data with access token
    response_data = {
        "success": True,
        "data": UserResponse.from_orm(db_user),
        "message": "User registered successfully",
        "access_token": access_token
    }
    
    return response_data


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """Authenticate user and return access token."""
    # Find user by username or email
    user = db.query(User).filter(
        or_(
            User.username == user_credentials.username,
            User.email == user_credentials.username
        )
    ).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Store token in Redis for session management (optional)
    redis.setex(
        f"token:{user.id}",
        int(access_token_expires.total_seconds()),
        access_token
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    redis = Depends(get_redis)
):
    """Logout user and invalidate token."""
    # Remove token from Redis
    redis.delete(f"token:{current_user.id}")
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse.from_orm(current_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """Refresh access token."""
    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username}, 
        expires_delta=access_token_expires
    )
    
    # Update token in Redis
    redis.setex(
        f"token:{current_user.id}",
        int(access_token_expires.total_seconds()),
        access_token
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(current_user)
    )


@router.post("/verify-token", response_model=UserResponse)
async def verify_user_token(
    current_user: User = Depends(get_current_active_user)
):
    """Verify if token is valid and return user info."""
    return UserResponse.from_orm(current_user) 