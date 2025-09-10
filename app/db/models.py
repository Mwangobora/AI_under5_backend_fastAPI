from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class User(Base):
    """User model for authentication and profile data."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    language = Column(String(10), nullable=False, default="english")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class RevokedToken(Base):
    """Model to track revoked JWT tokens."""
    __tablename__ = "revoked_tokens"
    
    jti = Column(String(36), primary_key=True)  # JWT ID
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    user_id = Column(UUID(as_uuid=True), nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Index for efficient cleanup of expired tokens
    __table_args__ = (
        Index('idx_revoked_tokens_expires_at', 'expires_at'),
        Index('idx_revoked_tokens_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<RevokedToken(jti={self.jti}, user_id={self.user_id})>"


class PasswordResetToken(Base):
    """Model for password reset tokens."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)  # Hashed token for security
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for cleanup of expired tokens
    __table_args__ = (
        Index('idx_password_reset_expires_at', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"
