from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.auth import (
    UserRegister, UserLogin, Token, TokenRefresh, PasswordResetRequest, 
    PasswordReset, Message
)
from app.crud.user import (
    create_user, authenticate_user, get_user_by_email, get_user_by_id,
    is_token_revoked, revoke_token, update_user_password
)
from app.core.security import (
    create_access_token, create_refresh_token, verify_token, 
    create_password_reset_token, verify_password_reset_token,
    validate_password, get_current_user_token
)
from app.emails.email_sender import send_password_reset_email
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Message:
    """Register a new user."""
    # Validate password
    validate_password(user_data.password)
    
    # Create user
    user = await create_user(db, user_data)
    
    # TODO: Send verification email if SMTP is configured
    # if settings.smtp_host:
    #     verification_token = create_email_verification_token(user.email)
    #     await send_verification_email(user.email, verification_token)
    
    return Message(message="User registered successfully. Please check your email for verification.")


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Token:
    """Authenticate user and return JWT tokens."""
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(token_data.refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check if token is revoked
        jti = payload.get("jti")
        if await is_token_revoked(db, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        user_id = payload.get("sub")
        user = await get_user_by_id(db, UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(subject=user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep same refresh token
            token_type="bearer"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.post("/logout", response_model=Message)
async def logout(
    current_user: Annotated[dict, Depends(get_current_user_token)],
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Message:
    """Logout user by revoking current token."""
    jti = current_user.get("jti")
    user_id = UUID(current_user.get("sub"))
    exp = current_user.get("exp")
    
    # Calculate expiration datetime
    expires_at = datetime.utcfromtimestamp(exp)
    
    # Revoke token
    await revoke_token(db, jti, user_id, "access", expires_at)
    
    return Message(message="Successfully logged out")


@router.post("/request-password-reset", response_model=Message)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Message:
    """Request password reset token."""
    user = await get_user_by_email(db, reset_data.email)
    
    # Always return success message for security (don't reveal if email exists)
    if user and user.is_active:
        # Create reset token
        reset_token = create_password_reset_token(reset_data.email)
        
        # Send reset email if SMTP is configured
        if settings.smtp_host:
            await send_password_reset_email(reset_data.email, reset_token)
    
    return Message(message="If your email is registered, you will receive a password reset link.")


@router.post("/reset-password", response_model=Message)
async def reset_password(
    reset_data: PasswordReset,
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Message:
    """Reset user password using reset token."""
    # Validate password
    validate_password(reset_data.new_password)
    
    # Verify reset token
    email = verify_password_reset_token(reset_data.token)
    
    # Get user
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    success = await update_user_password(db, user.id, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )
    
    return Message(message="Password has been reset successfully")
