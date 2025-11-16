"""API dependencies"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.payment_service import PaymentService
from app.services.webhook_service import WebhookService
from app.services.retry_service import RetryService
from app.services.report_service import ReportService


async def get_payment_service(
    db: AsyncSession = Depends(get_db)
) -> PaymentService:
    """Get payment service dependency"""
    return PaymentService(db)


async def get_webhook_service(
    db: AsyncSession = Depends(get_db)
) -> WebhookService:
    """Get webhook service dependency"""
    return WebhookService(db)


async def get_retry_service(
    db: AsyncSession = Depends(get_db)
) -> RetryService:
    """Get retry service dependency"""
    return RetryService(db)


async def get_report_service(
    db: AsyncSession = Depends(get_db)
) -> ReportService:
    """Get report service dependency"""
    return ReportService(db)
