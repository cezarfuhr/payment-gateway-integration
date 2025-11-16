"""Subscription and recurring payment models"""

import enum
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BillingCycle(str, enum.Enum):
    """Billing cycle enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAUSED = "paused"


class Subscription(Base):
    """Subscription model for recurring payments"""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_name = Column(String(255))

    # Pricing
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    billing_cycle = Column(Enum(BillingCycle), nullable=False, default=BillingCycle.MONTHLY)

    # Status
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE, index=True)

    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    end_date = Column(DateTime(timezone=True))
    next_billing_date = Column(DateTime(timezone=True), nullable=False, index=True)
    trial_end_date = Column(DateTime(timezone=True))

    # Cancellation
    cancelled_at = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    cancellation_reason = Column(String(500))

    # Metadata
    description = Column(String(500))
    metadata = Column(JSONB, default={})

    # Gateway info
    gateway = Column(String(50), nullable=False)
    gateway_subscription_id = Column(String(255))

    # Relationships
    payments = relationship("SubscriptionPayment", back_populates="subscription", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Subscription {self.id} - {self.status.value}>"


class SubscriptionPayment(Base):
    """Individual payments for a subscription"""
    __tablename__ = "subscription_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"))

    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False)
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)

    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self) -> str:
        return f"<SubscriptionPayment {self.id}>"
