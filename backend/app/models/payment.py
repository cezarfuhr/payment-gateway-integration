"""Payment related database models"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, Numeric, DateTime, Text, Boolean,
    Integer, ForeignKey, Enum, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class GatewayType(str, enum.Enum):
    """Payment gateway enum"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MERCADOPAGO = "mercadopago"
    PAGSEGURO = "pagseguro"


class TransactionType(str, enum.Enum):
    """Transaction type enum"""
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    gateway = Column(Enum(GatewayType), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True
    )
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    description = Column(Text)
    metadata = Column(JSONB, default={})
    gateway_response = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    transactions = relationship("Transaction", back_populates="payment", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="payment")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        Index("idx_payments_gateway_status", "gateway", "status"),
    )

    def __repr__(self) -> str:
        return f"<Payment {self.id} - {self.gateway.value} - {self.status.value}>"


class Transaction(Base):
    """Transaction model"""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    gateway_transaction_id = Column(String(255))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    payment = relationship("Payment", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.id} - {self.transaction_type.value}>"


class Webhook(Base):
    """Webhook model"""
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    gateway = Column(Enum(GatewayType), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    signature = Column(String(500))
    processed = Column(Boolean, default=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    payment = relationship("Payment", back_populates="webhooks")

    # Indexes
    __table_args__ = (
        Index("idx_webhooks_gateway_processed", "gateway", "processed"),
    )

    def __repr__(self) -> str:
        return f"<Webhook {self.id} - {self.gateway.value} - {self.event_type}>"


class RetryQueue(Base):
    """Retry queue model"""
    __tablename__ = "retry_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), index=True)
    last_error = Column(Text)
    status = Column(String(50), default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<RetryQueue {self.id} - {self.task_type} - {self.status}>"


class Report(Base):
    """Report model"""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_type = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Report {self.id} - {self.report_type}>"
