"""PayPal payment gateway implementation"""

import paypalrestsdk
from decimal import Decimal
from typing import Dict, Any, Optional
import hmac
import hashlib

from app.gateways.base import PaymentGateway, PaymentResult, RefundResult
from app.models.payment import GatewayType
from app.core.logging import logger


class PayPalGateway(PaymentGateway):
    """PayPal payment gateway"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.gateway_type = GatewayType.PAYPAL

        # Configure PayPal SDK
        paypalrestsdk.configure({
            "mode": config.get("mode", "sandbox"),
            "client_id": config.get("client_id"),
            "client_secret": config.get("client_secret"),
        })

        self.webhook_id = config.get("webhook_id")

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create a PayPal payment"""
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": metadata.get("return_url", "http://localhost:3000/success"),
                    "cancel_url": metadata.get("cancel_url", "http://localhost:3000/cancel")
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency.upper()
                    },
                    "description": description or "Payment"
                }]
            })

            if payment.create():
                logger.info(f"PayPal payment created: {payment.id}")

                # Get approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break

                return PaymentResult(
                    success=True,
                    transaction_id=payment.id,
                    status=self.normalize_status(payment.state),
                    gateway_response={
                        "approval_url": approval_url,
                        "state": payment.state,
                    }
                )
            else:
                logger.error(f"PayPal payment error: {payment.error}")
                return PaymentResult(
                    success=False,
                    error_message=str(payment.error),
                    gateway_response={"error": payment.error}
                )

        except Exception as e:
            logger.error(f"PayPal payment error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )

    async def get_payment(self, transaction_id: str) -> PaymentResult:
        """Get PayPal payment status"""
        try:
            payment = paypalrestsdk.Payment.find(transaction_id)

            return PaymentResult(
                success=True,
                transaction_id=payment.id,
                status=self.normalize_status(payment.state),
                gateway_response={
                    "state": payment.state,
                }
            )

        except Exception as e:
            logger.error(f"PayPal get payment error: {str(e)}")
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
        """Refund a PayPal payment"""
        try:
            # Get the sale from the payment
            payment = paypalrestsdk.Payment.find(transaction_id)
            sale_id = None

            for transaction in payment.transactions:
                for related_resource in transaction.related_resources:
                    if hasattr(related_resource, 'sale'):
                        sale_id = related_resource.sale.id
                        break

            if not sale_id:
                return RefundResult(
                    success=False,
                    error_message="Sale ID not found in payment"
                )

            sale = paypalrestsdk.Sale.find(sale_id)

            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "total": str(amount),
                    "currency": payment.transactions[0].amount.currency
                }

            refund = sale.refund(refund_data)

            if refund.success():
                logger.info(f"PayPal refund created: {refund.id}")

                return RefundResult(
                    success=True,
                    refund_id=refund.id,
                    amount=Decimal(refund.amount.total) if hasattr(refund, 'amount') else amount,
                    gateway_response={
                        "state": refund.state,
                    }
                )
            else:
                return RefundResult(
                    success=False,
                    error_message=str(refund.error)
                )

        except Exception as e:
            logger.error(f"PayPal refund error: {str(e)}")
            return RefundResult(
                success=False,
                error_message=str(e)
            )

    async def cancel_payment(self, transaction_id: str) -> PaymentResult:
        """Cancel a PayPal payment (not directly supported)"""
        # PayPal doesn't have direct cancellation, this would be handled via refund
        return PaymentResult(
            success=False,
            error_message="PayPal does not support direct payment cancellation. Use refund instead."
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any
    ) -> bool:
        """Verify PayPal webhook signature"""
        try:
            # PayPal webhook verification would typically use their SDK
            # This is a simplified version
            headers = kwargs.get("headers", {})
            transmission_id = headers.get("PAYPAL-TRANSMISSION-ID")
            transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME")
            cert_url = headers.get("PAYPAL-CERT-URL")
            auth_algo = headers.get("PAYPAL-AUTH-ALGO")

            # In production, use PayPal SDK's webhook verification
            # paypalrestsdk.WebhookEvent.verify(...)

            return True  # Simplified for example

        except Exception as e:
            logger.error(f"PayPal webhook verification error: {str(e)}")
            return False

    def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse PayPal webhook event"""
        event_type = payload.get("event_type", "")
        resource = payload.get("resource", {})

        return {
            "event_type": event_type,
            "transaction_id": resource.get("id") or resource.get("parent_payment"),
            "status": self.normalize_status(resource.get("state", "")),
            "amount": Decimal(resource.get("amount", {}).get("total", "0")),
            "currency": resource.get("amount", {}).get("currency", ""),
            "raw_data": payload,
        }
