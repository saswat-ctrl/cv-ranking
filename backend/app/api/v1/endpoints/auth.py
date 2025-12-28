from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserSetPassword, Token
from app.db.session import get_db

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) :
    """
    Create new user.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    user = User(
        email=user_in.email,
        name=user_in.full_name,
        is_verified=True # Auto-verify for MVP
    )
    
    if user_in.password:
        user.hashed_password = security.get_password_hash(user_in.password)
        
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/set_password", response_model=Any)
async def set_password(
    payload: UserSetPassword,
    db: AsyncSession = Depends(get_db)
) :
    """
    Set password for a user.
    """
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.hashed_password:
        raise HTTPException(
            status_code=400, 
            detail="Password already set. Please use password reset flow."
        )
        
    user.hashed_password = security.get_password_hash(payload.password)
    db.add(user)
    await db.commit()
    
    return {"message": "Password set successfully"}

@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db)
) :
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        result = await db.execute(select(User).where(User.email == user_in.email))
        user = result.scalars().first()
        
        if not user or not user.hashed_password:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
            
        if not security.verify_password(user_in.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
            
        if not user.is_verified:
            raise HTTPException(status_code=400, detail="User not verified")
            
        access_token = security.create_access_token(subject=user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    except HTTPException as e:
        # Re-raise HTTPException so it can be caught by the global handler or return it as JSON
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail, "code": "AUTH_ERROR"}
        )
    except Exception as e:
        # Catch-all for unexpected errors
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e), "code": "INTERNAL_ERROR"}
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(deps.get_current_user),
) :
    """
    Get current user.
    """
    return current_user

@router.post("/change_password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db)
) :
    """
    Change user password.
    """
    # Verify current password
    if not current_user.hashed_password:
        raise HTTPException(status_code=400, detail="No password set for this user")
        
    if not security.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Update password
    current_user.hashed_password = security.get_password_hash(new_password)
    db.add(current_user)
    await db.commit()
    
    return {"message": "Password changed successfully"}

