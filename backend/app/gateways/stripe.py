"""Stripe payment gateway implementation"""

import stripe
from decimal import Decimal
from typing import Dict, Any, Optional

from app.gateways.base import PaymentGateway, PaymentResult, RefundResult
from app.models.payment import GatewayType
from app.core.logging import logger


class StripeGateway(PaymentGateway):
    """Stripe payment gateway"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.gateway_type = GatewayType.STRIPE
        stripe.api_key = config.get("api_key")
        self.webhook_secret = config.get("webhook_secret")

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create a Stripe payment intent"""
        try:
            # Stripe expects amount in cents
            amount_cents = int(amount * 100)

            payment_intent_data = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "description": description,
                "metadata": metadata or {},
            }

            if customer_email:
                payment_intent_data["receipt_email"] = customer_email

            # Create PaymentIntent
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)

            logger.info(f"Stripe payment created: {payment_intent.id}")

            return PaymentResult(
                success=True,
                transaction_id=payment_intent.id,
                status=self.normalize_status(payment_intent.status),
                gateway_response={
                    "client_secret": payment_intent.client_secret,
                    "status": payment_intent.status,
                    "amount": payment_intent.amount,
                }
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e),
                gateway_response={"error": str(e)}
            )

    async def get_payment(self, transaction_id: str) -> PaymentResult:
        """Get Stripe payment intent status"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(transaction_id)

            return PaymentResult(
                success=True,
                transaction_id=payment_intent.id,
                status=self.normalize_status(payment_intent.status),
                gateway_response={
                    "status": payment_intent.status,
                    "amount": payment_intent.amount,
                    "currency": payment_intent.currency,
                }
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe get payment error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """Refund a Stripe payment"""
        try:
            refund_data = {
                "payment_intent": transaction_id,
            }

            if amount:
                refund_data["amount"] = int(amount * 100)

            if reason:
                refund_data["reason"] = reason

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Stripe refund created: {refund.id}")

            return RefundResult(
                success=True,
                refund_id=refund.id,
                amount=Decimal(refund.amount) / 100,
                gateway_response={
                    "status": refund.status,
                    "amount": refund.amount,
                }
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return RefundResult(
                success=False,
                error_message=str(e)
            )

    async def cancel_payment(self, transaction_id: str) -> PaymentResult:
        """Cancel a Stripe payment intent"""
        try:
            payment_intent = stripe.PaymentIntent.cancel(transaction_id)

            logger.info(f"Stripe payment cancelled: {payment_intent.id}")

            return PaymentResult(
                success=True,
                transaction_id=payment_intent.id,
                status=self.normalize_status(payment_intent.status),
                gateway_response={"status": payment_intent.status}
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe cancel error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any
    ) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return True
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {str(e)}")
            return False

    def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Stripe webhook event"""
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})

        return {
            "event_type": event_type,
            "transaction_id": data.get("id"),
            "status": self.normalize_status(data.get("status", "")),
            "amount": Decimal(data.get("amount", 0)) / 100,
            "currency": data.get("currency", ""),
            "raw_data": payload,
        }
