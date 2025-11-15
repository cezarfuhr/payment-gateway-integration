"""Payment schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.payment import PaymentStatus, GatewayType, TransactionType


# Payment Schemas
class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", max_length=3)
    customer_email: Optional[EmailStr] = None
    customer_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentCreate(PaymentBase):
    """Create payment schema"""
    gateway: GatewayType = Field(..., description="Payment gateway to use")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code"""
        return v.upper()


class PaymentUpdate(BaseModel):
    """Update payment schema"""
    status: Optional[PaymentStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(PaymentBase):
    """Payment response schema"""
    id: UUID
    external_id: str
    gateway: GatewayType
    status: PaymentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Transaction Schemas
class TransactionBase(BaseModel):
    """Base transaction schema"""
    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionCreate(TransactionBase):
    """Create transaction schema"""
    payment_id: UUID


class TransactionResponse(TransactionBase):
    """Transaction response schema"""
    id: UUID
    payment_id: UUID
    status: PaymentStatus
    gateway_transaction_id: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Webhook Schemas
class WebhookBase(BaseModel):
    """Base webhook schema"""
    gateway: GatewayType
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None


class WebhookCreate(WebhookBase):
    """Create webhook schema"""
    pass


class WebhookResponse(WebhookBase):
    """Webhook response schema"""
    id: UUID
    processed: bool
    payment_id: Optional[UUID] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# Report Schemas
class ReportCreate(BaseModel):
    """Create report schema"""
    report_type: str = Field(..., max_length=100)
    start_date: datetime
    end_date: datetime

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """Validate end date is after start date"""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class ReportResponse(BaseModel):
    """Report response schema"""
    id: UUID
    report_type: str
    start_date: datetime
    end_date: datetime
    data: Dict[str, Any]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Refund Schema
class RefundCreate(BaseModel):
    """Create refund schema"""
    payment_id: UUID
    amount: Optional[Decimal] = Field(None, gt=0, description="Amount to refund (partial or full)")
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    """Refund response schema"""
    id: UUID
    payment_id: UUID
    amount: Decimal
    status: PaymentStatus
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# Health Check Schema
class HealthCheck(BaseModel):
    """Health check schema"""
    status: str
    version: str
    database: str
    redis: str
