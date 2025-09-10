from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models import User, RevokedToken, PasswordResetToken
from app.core.security import get_password_hash, verify_password
from app.schemas.auth import UserRegister


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserRegister) -> User:
    """Create a new user."""
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create user instance
    db_user = User(
        email=user.email,
        name=user.name,
        phone=user.phone,
        password_hash=hashed_password,
        is_active=True,
        is_verified=False,
        language="english"
    )
    
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def update_user_password(db: AsyncSession, user_id: UUID, new_password: str) -> bool:
    """Update user password."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    """Check if a token is revoked."""
    result = await db.execute(
        select(RevokedToken).where(
            and_(
                RevokedToken.jti == jti,
                RevokedToken.expires_at > datetime.utcnow()
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def revoke_token(
    db: AsyncSession, 
    jti: str, 
    user_id: UUID, 
    token_type: str, 
    expires_at: datetime
) -> None:
    """Revoke a token by storing its JTI."""
    revoked_token = RevokedToken(
        jti=jti,
        user_id=user_id,
        token_type=token_type,
        expires_at=expires_at
    )
    
    db.add(revoked_token)
    await db.commit()


async def cleanup_expired_tokens(db: AsyncSession) -> None:
    """Clean up expired revoked tokens."""
    result = await db.execute(
        select(RevokedToken).where(RevokedToken.expires_at <= datetime.utcnow())
    )
    expired_tokens = result.scalars().all()
    
    for token in expired_tokens:
        await db.delete(token)
    
    await db.commit()


async def create_password_reset_token(
    db: AsyncSession, 
    user_id: UUID, 
    token_hash: str,
    expires_at: datetime
) -> PasswordResetToken:
    """Create a password reset token record."""
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)
    return reset_token


async def validate_password_reset_token(
    db: AsyncSession, 
    token_hash: str
) -> Optional[PasswordResetToken]:
    """Validate and get password reset token."""
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.used_at.is_(None)
            )
        )
    )
    return result.scalar_one_or_none()


async def mark_password_reset_token_used(
    db: AsyncSession, 
    token_id: UUID
) -> None:
    """Mark password reset token as used."""
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.id == token_id)
    )
    token = result.scalar_one_or_none()
    
    if token:
        token.used_at = datetime.utcnow()
        await db.commit()


async def update_user_language(db: AsyncSession, user_id: UUID, language: str) -> bool:
    """Update user's language preference."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.language = language
    user.updated_at = datetime.utcnow()
    await db.commit()
    return True
