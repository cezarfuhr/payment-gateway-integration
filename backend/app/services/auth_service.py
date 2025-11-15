"""Authentication service"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, APIKey, UserRole
from app.schemas.user import UserCreate, LoginRequest, APIKeyCreate
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.logging import logger


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("Email already registered")
            if existing_user.username == user_data.username:
                raise ValueError("Username already taken")

        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            tenant_id=user_data.tenant_id,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User registered: {user.username}")
        return user

    async def authenticate_user(self, login_data: LoginRequest) -> Optional[User]:
        """Authenticate user with username/password"""
        result = await self.db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(login_data.password, user.hashed_password):
            return None

        if not user.is_active:
            raise ValueError("User account is disabled")

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()

        logger.info(f"User authenticated: {user.username}")
        return user

    async def create_token(self, user: User) -> dict:
        """Create JWT token for user"""
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        }

        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 hours
            "user": user,
        }

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)

        if not user:
            return False

        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        await self.db.commit()

        logger.info(f"Password changed for user: {user.username}")
        return True

    async def create_api_key(
        self, user_id: UUID, key_data: APIKeyCreate
    ) -> APIKey:
        """Create API key for user"""
        # Generate secure API key
        api_key = f"pk_{secrets.token_urlsafe(32)}"

        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)

        api_key_obj = APIKey(
            name=key_data.name,
            key=api_key,
            user_id=user_id,
            expires_at=expires_at,
        )

        self.db.add(api_key_obj)
        await self.db.commit()
        await self.db.refresh(api_key_obj)

        logger.info(f"API key created: {key_data.name} for user: {user_id}")
        return api_key_obj

    async def validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate API key and return associated user"""
        result = await self.db.execute(
            select(APIKey).where(APIKey.key == api_key)
        )
        key_obj = result.scalar_one_or_none()

        if not key_obj:
            return None

        if not key_obj.is_active:
            return None

        if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
            return None

        # Update last used
        key_obj.last_used = datetime.utcnow()
        await self.db.commit()

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == key_obj.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        return user

    async def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """Revoke API key"""
        result = await self.db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        )
        key_obj = result.scalar_one_or_none()

        if not key_obj:
            return False

        key_obj.is_active = False
        await self.db.commit()

        logger.info(f"API key revoked: {key_obj.name}")
        return True

    async def list_user_api_keys(self, user_id: UUID) -> list[APIKey]:
        """List all API keys for a user"""
        result = await self.db.execute(
            select(APIKey).where(APIKey.user_id == user_id)
        )
        return list(result.scalars().all())
