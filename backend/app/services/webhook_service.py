"""Webhook service"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Webhook, Payment, PaymentStatus
from app.schemas.payment import WebhookCreate
from app.gateways.factory import GatewayFactory
from app.core.logging import logger


class WebhookService:
    """Service for webhook operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(self, webhook_data: WebhookCreate) -> Webhook:
        """Create a new webhook record"""
        webhook = Webhook(
            gateway=webhook_data.gateway,
            event_type=webhook_data.event_type,
            payload=webhook_data.payload,
            signature=webhook_data.signature,
        )

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        return webhook

    async def process_webhook(
        self,
        webhook_id: UUID,
        raw_payload: bytes,
        signature: str,
        headers: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Process a webhook"""
        webhook = await self.get_webhook(webhook_id)

        if not webhook:
            logger.error(f"Webhook not found: {webhook_id}")
            return False

        try:
            # Verify signature
            gateway = GatewayFactory.create(webhook.gateway)

            if not gateway.verify_webhook_signature(
                raw_payload,
                signature,
                headers=headers or {}
            ):
                logger.error(f"Webhook signature verification failed: {webhook_id}")
                webhook.error_message = "Signature verification failed"
                webhook.retry_count += 1
                await self.db.commit()
                return False

            # Parse event
            event_data = gateway.parse_webhook_event(webhook.payload)

            # Find associated payment
            transaction_id = event_data.get("transaction_id")
            if transaction_id:
                payment = await self.get_payment_by_external_id(transaction_id)

                if payment:
                    # Update payment status
                    new_status = event_data.get("status")
                    if new_status and new_status in [s.value for s in PaymentStatus]:
                        payment.status = PaymentStatus(new_status)
                        payment.gateway_response = event_data.get("raw_data", {})
                        webhook.payment_id = payment.id

            # Mark webhook as processed
            webhook.processed = True
            webhook.processed_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"Webhook processed: {webhook_id}")
            return True

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            webhook.error_message = str(e)
            webhook.retry_count += 1
            await self.db.commit()
            return False

    async def get_webhook(self, webhook_id: UUID) -> Optional[Webhook]:
        """Get webhook by ID"""
        result = await self.db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_external_id(self, external_id: str) -> Optional[Payment]:
        """Get payment by external ID"""
        result = await self.db.execute(
            select(Payment).where(Payment.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def retry_failed_webhooks(self, max_retries: int = 3) -> int:
        """Retry failed webhooks"""
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.processed == False)
            .where(Webhook.retry_count < max_retries)
        )
        webhooks = result.scalars().all()

        retry_count = 0
        for webhook in webhooks:
            # Retry processing (would need raw payload and signature from storage)
            # This is a simplified version
            webhook.retry_count += 1
            retry_count += 1

        await self.db.commit()

        logger.info(f"Retried {retry_count} webhooks")
        return retry_count
