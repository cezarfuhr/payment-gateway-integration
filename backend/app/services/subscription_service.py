"""Subscription service for recurring payments"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import (
    Subscription,
    SubscriptionPayment,
    BillingCycle,
    SubscriptionStatus
)
from app.models.payment import GatewayType
from app.services.payment_service import PaymentService
from app.services.notification_service import NotificationService
from app.schemas.payment import PaymentCreate
from app.core.logging import logger


class SubscriptionService:
    """Service for subscription operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)
        self.notification_service = NotificationService()

    async def create_subscription(
        self,
        customer_email: str,
        customer_name: Optional[str],
        amount: Decimal,
        currency: str,
        billing_cycle: BillingCycle,
        gateway: GatewayType,
        description: Optional[str] = None,
        trial_days: int = 0,
        metadata: Optional[dict] = None
    ) -> Subscription:
        """Create a new subscription"""

        # Calculate next billing date
        next_billing_date = self._calculate_next_billing_date(
            datetime.utcnow(),
            billing_cycle,
            trial_days
        )

        trial_end_date = None
        if trial_days > 0:
            trial_end_date = datetime.utcnow() + timedelta(days=trial_days)

        subscription = Subscription(
            customer_email=customer_email,
            customer_name=customer_name,
            amount=amount,
            currency=currency,
            billing_cycle=billing_cycle,
            gateway=gateway.value,
            description=description,
            next_billing_date=next_billing_date,
            trial_end_date=trial_end_date,
            metadata=metadata or {},
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        # Send notification
        await self.notification_service.send_subscription_created(
            customer_email,
            float(amount),
            currency,
            billing_cycle.value,
            next_billing_date.strftime("%Y-%m-%d")
        )

        logger.info(f"Subscription created: {subscription.id}")
        return subscription

    async def get_subscription(self, subscription_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def cancel_subscription(
        self,
        subscription_id: UUID,
        cancel_immediately: bool = False,
        cancellation_reason: Optional[str] = None
    ) -> Optional[Subscription]:
        """Cancel a subscription"""
        subscription = await self.get_subscription(subscription_id)

        if not subscription:
            return None

        if cancel_immediately:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.end_date = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True
            subscription.cancellation_reason = cancellation_reason

        await self.db.commit()
        await self.db.refresh(subscription)

        # Send notification
        end_date = subscription.end_date or subscription.next_billing_date
        await self.notification_service.send_subscription_cancelled(
            subscription.customer_email,
            end_date.strftime("%Y-%m-%d")
        )

        logger.info(f"Subscription cancelled: {subscription_id}")
        return subscription

    async def process_due_subscriptions(self) -> int:
        """Process subscriptions that are due for billing"""
        now = datetime.utcnow()

        result = await self.db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.next_billing_date <= now
            )
        )
        subscriptions = result.scalars().all()

        processed = 0
        for subscription in subscriptions:
            try:
                await self._process_subscription_payment(subscription)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process subscription {subscription.id}: {e}")

        return processed

    async def _process_subscription_payment(
        self,
        subscription: Subscription
    ) -> bool:
        """Process a subscription payment"""
        billing_period_start = subscription.next_billing_date
        billing_period_end = self._calculate_next_billing_date(
            billing_period_start,
            BillingCycle(subscription.billing_cycle)
        )

        # Create subscription payment record
        sub_payment = SubscriptionPayment(
            subscription_id=subscription.id,
            amount=subscription.amount,
            status="pending",
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            attempt_count=0
        )

        self.db.add(sub_payment)
        await self.db.commit()

        try:
            # Create payment
            payment_data = PaymentCreate(
                gateway=GatewayType(subscription.gateway),
                amount=subscription.amount,
                currency=subscription.currency,
                customer_email=subscription.customer_email,
                customer_name=subscription.customer_name,
                description=f"Subscription payment - {subscription.description}",
                metadata={
                    "subscription_id": str(subscription.id),
                    "billing_period_start": billing_period_start.isoformat(),
                    "billing_period_end": billing_period_end.isoformat()
                }
            )

            payment = await self.payment_service.create_payment(payment_data)

            # Update subscription payment
            sub_payment.payment_id = payment.id
            sub_payment.status = payment.status.value
            sub_payment.attempt_count += 1
            sub_payment.last_attempt_at = datetime.utcnow()

            if payment.status.value == "succeeded":
                sub_payment.paid_at = datetime.utcnow()
                subscription.next_billing_date = billing_period_end

                # Check if should cancel at period end
                if subscription.cancel_at_period_end:
                    subscription.status = SubscriptionStatus.CANCELLED
                    subscription.cancelled_at = datetime.utcnow()
                    subscription.end_date = datetime.utcnow()

            else:
                subscription.status = SubscriptionStatus.PAST_DUE

                # Send payment failed notification
                await self.notification_service.send_subscription_payment_failed(
                    subscription.customer_email,
                    float(subscription.amount),
                    subscription.currency,
                    (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
                )

            await self.db.commit()

            logger.info(f"Subscription payment processed: {subscription.id}")
            return True

        except Exception as e:
            logger.error(f"Subscription payment failed: {e}")
            sub_payment.status = "failed"
            sub_payment.attempt_count += 1
            subscription.status = SubscriptionStatus.PAST_DUE
            await self.db.commit()
            return False

    def _calculate_next_billing_date(
        self,
        current_date: datetime,
        billing_cycle: BillingCycle,
        trial_days: int = 0
    ) -> datetime:
        """Calculate next billing date based on cycle"""
        if trial_days > 0:
            return current_date + timedelta(days=trial_days)

        if billing_cycle == BillingCycle.DAILY:
            return current_date + timedelta(days=1)
        elif billing_cycle == BillingCycle.WEEKLY:
            return current_date + timedelta(weeks=1)
        elif billing_cycle == BillingCycle.MONTHLY:
            return current_date + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            return current_date + timedelta(days=90)
        elif billing_cycle == BillingCycle.YEARLY:
            return current_date + timedelta(days=365)

        return current_date + timedelta(days=30)
