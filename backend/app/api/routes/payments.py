"""Payment API routes"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    RefundCreate,
    RefundResponse,
    TransactionResponse,
)
from app.models.payment import PaymentStatus
from app.services.payment_service import PaymentService
from app.api.deps import get_payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    service: PaymentService = Depends(get_payment_service)
):
    """Create a new payment"""
    try:
        result = await service.create_payment(payment)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[PaymentStatus] = None,
    service: PaymentService = Depends(get_payment_service)
):
    """List payments"""
    payments = await service.list_payments(skip, limit, status_filter)
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service)
):
    """Get payment by ID"""
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    payment_update: PaymentUpdate,
    service: PaymentService = Depends(get_payment_service)
):
    """Update payment"""
    payment = await service.update_payment(payment_id, payment_update)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.post("/{payment_id}/sync", response_model=PaymentResponse)
async def sync_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service)
):
    """Sync payment status with gateway"""
    payment = await service.sync_payment_status(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.post("/refunds", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    refund: RefundCreate,
    service: PaymentService = Depends(get_payment_service)
):
    """Create a refund"""
    try:
        result = await service.refund_payment(refund)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service)
):
    """Cancel a payment"""
    try:
        payment = await service.cancel_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
