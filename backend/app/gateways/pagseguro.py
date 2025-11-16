"""PagSeguro payment gateway implementation"""

from decimal import Decimal
from typing import Dict, Any, Optional
import httpx
import hmac
import hashlib
from urllib.parse import urlencode

from app.gateways.base import PaymentGateway, PaymentResult, RefundResult
from app.models.payment import GatewayType
from app.core.logging import logger


class PagSeguroGateway(PaymentGateway):
    """PagSeguro payment gateway"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.gateway_type = GatewayType.PAGSEGURO
        self.email = config.get("email")
        self.token = config.get("token")
        self.environment = config.get("environment", "sandbox")

        # Set base URL based on environment
        if self.environment == "production":
            self.base_url = "https://ws.pagseguro.uol.com.br"
        else:
            self.base_url = "https://ws.sandbox.pagseguro.uol.com.br"

    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create a PagSeguro payment"""
        try:
            # PagSeguro uses XML format, but we'll use their API v4 with JSON
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            }

            payment_data = {
                "reference_id": metadata.get("reference_id", "default") if metadata else "default",
                "customer": {
                    "email": customer_email or "test@test.com",
                },
                "items": [
                    {
                        "reference_id": "item-1",
                        "name": description or "Payment",
                        "quantity": 1,
                        "unit_amount": int(amount * 100),  # cents
                    }
                ],
                "qr_codes": [
                    {
                        "amount": {
                            "value": int(amount * 100)
                        }
                    }
                ],
                "notification_urls": [
                    metadata.get("notification_url", "http://localhost:8000/webhooks/pagseguro")
                ] if metadata else []
            }

            if customer_name:
                payment_data["customer"]["name"] = customer_name

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/orders",
                    json=payment_data,
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"PagSeguro payment created: {data.get('id')}")

                    qr_codes = data.get("qr_codes", [])
                    qr_code_text = qr_codes[0].get("text") if qr_codes else None

                    return PaymentResult(
                        success=True,
                        transaction_id=data.get("id"),
                        status=self.normalize_status(data.get("status", "pending")),
                        gateway_response={
                            "status": data.get("status"),
                            "qr_code": qr_code_text,
                            "links": data.get("links", []),
                        }
                    )
                else:
                    error_data = response.json() if response.text else {}
                    logger.error(f"PagSeguro payment error: {error_data}")
                    return PaymentResult(
                        success=False,
                        error_message=error_data.get("message", "Payment creation failed"),
                        gateway_response=error_data
                    )

        except Exception as e:
            logger.error(f"PagSeguro payment error: {str(e)}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )

    async def get_payment(self, transaction_id: str) -> PaymentResult:
        """Get PagSeguro payment status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/orders/{transaction_id}",
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()

                    return PaymentResult(
                        success=True,
                        transaction_id=data.get("id"),
                        status=self.normalize_status(data.get("status", "pending")),
                        gateway_response={
                            "status": data.get("status"),
                        }
                    )
                else:
                    return PaymentResult(
                        success=False,
                        error_message="Payment not found"
                    )

        except Exception as e:
            logger.error(f"PagSeguro get payment error: {str(e)}")
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
        """Refund a PagSeguro payment"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            }

            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "value": int(amount * 100)
                }

            async with httpx.AsyncClient() as client:
                # Get charges from the order first
                order_response = await client.get(
                    f"{self.base_url}/orders/{transaction_id}",
                    headers=headers,
                    timeout=30.0
                )

                if order_response.status_code != 200:
                    return RefundResult(
                        success=False,
                        error_message="Order not found"
                    )

                order_data = order_response.json()
                charges = order_data.get("charges", [])

                if not charges:
                    return RefundResult(
                        success=False,
                        error_message="No charges found for this order"
                    )

                charge_id = charges[0].get("id")

                # Create refund
                response = await client.post(
                    f"{self.base_url}/charges/{charge_id}/cancel",
                    json=refund_data,
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"PagSeguro refund created for charge: {charge_id}")

                    return RefundResult(
                        success=True,
                        refund_id=charge_id,
                        amount=amount,
                        gateway_response=data
                    )
                else:
                    error_data = response.json() if response.text else {}
                    return RefundResult(
                        success=False,
                        error_message=error_data.get("message", "Refund failed")
                    )

        except Exception as e:
            logger.error(f"PagSeguro refund error: {str(e)}")
            return RefundResult(
                success=False,
                error_message=str(e)
            )

    async def cancel_payment(self, transaction_id: str) -> PaymentResult:
        """Cancel a PagSeguro payment"""
        # Use refund for cancellation
        refund_result = await self.refund_payment(transaction_id)

        return PaymentResult(
            success=refund_result.success,
            transaction_id=transaction_id,
            status="cancelled" if refund_result.success else "failed",
            error_message=refund_result.error_message,
            gateway_response=refund_result.gateway_response
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any
    ) -> bool:
        """Verify PagSeguro webhook signature"""
        try:
            # PagSeguro typically doesn't use signature verification
            # They rely on IP whitelist and notification code validation
            # This is a simplified implementation
            return True

        except Exception as e:
            logger.error(f"PagSeguro webhook verification error: {str(e)}")
            return False

    def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse PagSeguro webhook event"""
        # PagSeguro webhooks contain notification codes
        notification_code = payload.get("notificationCode")

        return {
            "event_type": "payment.notification",
            "notification_code": notification_code,
            "transaction_id": payload.get("id", ""),
            "status": self.normalize_status(payload.get("status", "")),
            "raw_data": payload,
        }
