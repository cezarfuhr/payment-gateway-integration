"""Idempotency key model"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class IdempotencyKey(Base):
    """Idempotency key model to prevent duplicate requests"""
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String(255), unique=True, nullable=False, index=True)
    request_path = Column(String(500), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_body = Column(JSONB)
    response_status = Column(Integer)
    response_body = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<IdempotencyKey {self.key}>"
