from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.auth import UserProfile, Message
from app.schemas.ml_models import LanguagePreference, LanguageResponse
from app.crud.user import get_user_by_id, is_token_revoked, update_user_language
from app.core.security import get_current_user_token

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


async def get_current_user(
    current_user_token: Annotated[dict, Depends(get_current_user_token)],
    db: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Get current authenticated user from token."""
    jti = current_user_token.get("jti")
    user_id = UUID(current_user_token.get("sub"))
    
    # Check if token is revoked
    if await is_token_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Get user from database
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
) -> UserProfile:
    """Get current user profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        language=current_user.language,
        created_at=current_user.created_at
    )


@router.put("/language", response_model=LanguageResponse)
async def update_language_preference(
    language_data: LanguagePreference,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user=Depends(get_current_user)
) -> LanguageResponse:
    """Update user's language preference."""
    success = await update_user_language(db, current_user.id, language_data.language)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language preference"
        )
    
    # Return appropriate message based on language
    if language_data.language == "swahili":
        message = "Lugha imebadilishwa kuwa Kiswahili"
    else:
        message = "Language changed to English"
    
    return LanguageResponse(
        language=language_data.language,
        message=message
    )
