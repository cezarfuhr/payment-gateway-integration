"""Mercado Pago payment gateway implementation"""

import mercadopago
from decimal import Decimal
from typing import Dict, Any, Optional
import hmac
import hashlib

from app.gateways.base import PaymentGateway, PaymentResult, RefundResult
from app.models.payment import GatewayType
from app.core.logging import logger


class MercadoPagoGateway(PaymentGateway):
    """Mercado Pago payment gateway"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.gateway_type = GatewayType.MERCADOPAGO
        self.sdk = mercadopago.SDK(config.get("access_token"))
        self.webhook_secret = config.get("webhook_secret")
        self.public_key = config.get("public_key")

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create a Mercado Pago payment"""
        try:
            payment_data = {
                "transaction_amount": float(amount),
                "description": description or "Payment",
                "payment_method_id": metadata.get("payment_method_id", "pix") if metadata else "pix",
                "payer": {
                    "email": customer_email or "test@test.com",
                }
            }

            if customer_name:
                payment_data["payer"]["first_name"] = customer_name

            # Additional metadata
            if metadata:
                payment_data["metadata"] = metadata

            payment_response = self.sdk.payment().create(payment_data)
            payment = payment_response["response"]

            if payment_response["status"] in [200, 201]:
                logger.info(f"Mercado Pago payment created: {payment.get('id')}")

                return PaymentResult(
                    success=True,
                    transaction_id=str(payment.get("id")),
                    status=self.normalize_status(payment.get("status")),
                    gateway_response={
                        "status": payment.get("status"),
                        "status_detail": payment.get("status_detail"),
                        "qr_code": payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code"),
                        "qr_code_base64": payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64"),
                    }
                )
            else:
                logger.error(f"Mercado Pago payment error: {payment}")
                return PaymentResult(
                    success=False,
                    error_message=payment.get("message", "Unknown error"),
                    gateway_response=payment
                )

        except Exception as e:
            logger.error(f"Mercado Pago payment error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )

    async def get_payment(self, transaction_id: str) -> PaymentResult:
        """Get Mercado Pago payment status"""
        try:
            payment_response = self.sdk.payment().get(transaction_id)
            payment = payment_response["response"]

            if payment_response["status"] == 200:
                return PaymentResult(
                    success=True,
                    transaction_id=str(payment.get("id")),
                    status=self.normalize_status(payment.get("status")),
                    gateway_response={
                        "status": payment.get("status"),
                        "status_detail": payment.get("status_detail"),
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=payment.get("message", "Payment not found")
                )

        except Exception as e:
            logger.error(f"Mercado Pago get payment error: {str(e)}")
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
        """Refund a Mercado Pago payment"""
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = float(amount)

            refund_response = self.sdk.refund().create(transaction_id, refund_data)
            refund = refund_response["response"]

            if refund_response["status"] in [200, 201]:
                logger.info(f"Mercado Pago refund created: {refund.get('id')}")

                return RefundResult(
                    success=True,
                    refund_id=str(refund.get("id")),
                    amount=Decimal(refund.get("amount", 0)),
                    gateway_response={
                        "status": refund.get("status"),
                    }
                )
            else:
                return RefundResult(
                    success=False,
                    error_message=refund.get("message", "Refund failed")
                )

        except Exception as e:
            logger.error(f"Mercado Pago refund error: {str(e)}")
            return RefundResult(
                success=False,
                error_message=str(e)
            )

    async def cancel_payment(self, transaction_id: str) -> PaymentResult:
        """Cancel a Mercado Pago payment"""
        try:
            cancel_response = self.sdk.payment().cancel(transaction_id)
            payment = cancel_response["response"]

            if cancel_response["status"] == 200:
                logger.info(f"Mercado Pago payment cancelled: {transaction_id}")

                return PaymentResult(
                    success=True,
                    transaction_id=transaction_id,
                    status=self.normalize_status(payment.get("status")),
                    gateway_response={"status": payment.get("status")}
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=payment.get("message", "Cancellation failed")
                )

        except Exception as e:
            logger.error(f"Mercado Pago cancel error: {str(e)}")
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
        """Verify Mercado Pago webhook signature"""
        try:
            # Mercado Pago uses x-signature header
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Mercado Pago webhook verification error: {str(e)}")
            return False

    def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Mercado Pago webhook event"""
        event_type = payload.get("type", "") or payload.get("action", "")
        data = payload.get("data", {})

        return {
            "event_type": event_type,
            "transaction_id": str(data.get("id", "")),
            "status": self.normalize_status(payload.get("status", "")),
            "raw_data": payload,
        }
