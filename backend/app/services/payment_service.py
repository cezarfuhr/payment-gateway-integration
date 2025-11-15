"""Payment service"""

from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, Transaction, PaymentStatus, TransactionType
from app.schemas.payment import PaymentCreate, PaymentUpdate, RefundCreate
from app.gateways.factory import GatewayFactory
from app.core.logging import logger
from app.core.security import sanitize_sensitive_data


class PaymentService:
    """Service for payment operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment"""
        try:
            # Get gateway
            gateway = GatewayFactory.create(payment_data.gateway)

            # Create payment in gateway
            result = await gateway.create_payment(
                amount=payment_data.amount,
                currency=payment_data.currency,
                customer_email=payment_data.customer_email,
                customer_name=payment_data.customer_name,
                description=payment_data.description,
                metadata=payment_data.metadata,
            )

            if not result.success:
                logger.error(f"Gateway payment creation failed: {result.error_message}")
                raise Exception(result.error_message)

            # Create payment in database
            payment = Payment(
                external_id=result.transaction_id,
                gateway=payment_data.gateway,
                amount=payment_data.amount,
                currency=payment_data.currency,
                status=PaymentStatus(result.status),
                customer_email=payment_data.customer_email,
                customer_name=payment_data.customer_name,
                description=payment_data.description,
                metadata=payment_data.metadata,
                gateway_response=sanitize_sensitive_data(result.gateway_response),
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            # Create initial transaction
            transaction = Transaction(
                payment_id=payment.id,
                transaction_type=TransactionType.PAYMENT,
                amount=payment_data.amount,
                status=PaymentStatus(result.status),
                gateway_transaction_id=result.transaction_id,
                metadata=payment_data.metadata,
            )

            self.db.add(transaction)
            await self.db.commit()

            logger.info(f"Payment created: {payment.id}")
            return payment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Payment creation error: {str(e)}")
            raise

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_external_id(self, external_id: str) -> Optional[Payment]:
        """Get payment by external ID"""
        result = await self.db.execute(
            select(Payment).where(Payment.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def list_payments(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[PaymentStatus] = None
    ) -> List[Payment]:
        """List payments with pagination"""
        query = select(Payment)

        if status:
            query = query.where(Payment.status == status)

        query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_payment(
        self,
        payment_id: UUID,
        payment_update: PaymentUpdate
    ) -> Optional[Payment]:
        """Update payment"""
        payment = await self.get_payment(payment_id)

        if not payment:
            return None

        update_data = payment_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(payment, key, value)

        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Payment updated: {payment_id}")
        return payment

    async def sync_payment_status(self, payment_id: UUID) -> Optional[Payment]:
        """Sync payment status with gateway"""
        payment = await self.get_payment(payment_id)

        if not payment:
            return None

        try:
            gateway = GatewayFactory.create(payment.gateway)
            result = await gateway.get_payment(payment.external_id)

            if result.success:
                payment.status = PaymentStatus(result.status)
                payment.gateway_response = sanitize_sensitive_data(result.gateway_response)

                await self.db.commit()
                await self.db.refresh(payment)

                logger.info(f"Payment status synced: {payment_id}")

            return payment

        except Exception as e:
            logger.error(f"Payment sync error: {str(e)}")
            return payment

    async def refund_payment(
        self,
        refund_data: RefundCreate
    ) -> Transaction:
        """Refund a payment"""
        payment = await self.get_payment(refund_data.payment_id)

        if not payment:
            raise Exception("Payment not found")

        if payment.status not in [PaymentStatus.SUCCEEDED]:
            raise Exception(f"Cannot refund payment with status: {payment.status}")

        try:
            gateway = GatewayFactory.create(payment.gateway)

            # Determine refund amount
            refund_amount = refund_data.amount or payment.amount

            # Create refund in gateway
            result = await gateway.refund_payment(
                transaction_id=payment.external_id,
                amount=refund_amount,
                reason=refund_data.reason,
            )

            if not result.success:
                raise Exception(result.error_message)

            # Update payment status
            if refund_amount >= payment.amount:
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED

            # Create refund transaction
            transaction = Transaction(
                payment_id=payment.id,
                transaction_type=TransactionType.REFUND,
                amount=refund_amount,
                status=PaymentStatus.SUCCEEDED,
                gateway_transaction_id=result.refund_id,
                metadata={"reason": refund_data.reason} if refund_data.reason else {},
            )

            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)

            logger.info(f"Refund created for payment: {payment.id}")
            return transaction

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Refund error: {str(e)}")
            raise

    async def cancel_payment(self, payment_id: UUID) -> Optional[Payment]:
        """Cancel a payment"""
        payment = await self.get_payment(payment_id)

        if not payment:
            return None

        if payment.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise Exception(f"Cannot cancel payment with status: {payment.status}")

        try:
            gateway = GatewayFactory.create(payment.gateway)
            result = await gateway.cancel_payment(payment.external_id)

            if result.success:
                payment.status = PaymentStatus.CANCELLED
                await self.db.commit()
                await self.db.refresh(payment)

                logger.info(f"Payment cancelled: {payment_id}")

            return payment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Payment cancellation error: {str(e)}")
            raise
