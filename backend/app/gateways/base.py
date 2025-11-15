"""Base payment gateway interface"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from app.models.payment import GatewayType


class PaymentResult:
    """Payment result data class"""

    def __init__(
        self,
        success: bool,
        transaction_id: Optional[str] = None,
        status: str = "pending",
        error_message: Optional[str] = None,
        gateway_response: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.status = status
        self.error_message = error_message
        self.gateway_response = gateway_response or {}


class RefundResult:
    """Refund result data class"""

    def __init__(
        self,
        success: bool,
        refund_id: Optional[str] = None,
        amount: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        gateway_response: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.refund_id = refund_id
        self.amount = amount
        self.error_message = error_message
        self.gateway_response = gateway_response or {}


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gateway_type: GatewayType = GatewayType.STRIPE

    @abstractmethod
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """
        Create a payment

        Args:
            amount: Payment amount
            currency: Currency code (USD, BRL, etc)
            customer_email: Customer email
            customer_name: Customer name
            description: Payment description
            metadata: Additional metadata

        Returns:
            PaymentResult object
        """
        pass

    @abstractmethod
    async def get_payment(self, transaction_id: str) -> PaymentResult:
        """
        Get payment status

        Args:
            transaction_id: Gateway transaction ID

        Returns:
            PaymentResult object
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """
        Refund a payment

        Args:
            transaction_id: Gateway transaction ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason

        Returns:
            RefundResult object
        """
        pass

    @abstractmethod
    async def cancel_payment(self, transaction_id: str) -> PaymentResult:
        """
        Cancel a payment

        Args:
            transaction_id: Gateway transaction ID

        Returns:
            PaymentResult object
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any
    ) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            **kwargs: Additional gateway-specific parameters

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse webhook event

        Args:
            payload: Webhook payload

        Returns:
            Normalized event data
        """
        pass

    def normalize_status(self, gateway_status: str) -> str:
        """
        Normalize gateway status to internal status

        Args:
            gateway_status: Gateway-specific status

        Returns:
            Normalized status
        """
        status_map = {
            # Common mappings
            "succeeded": "succeeded",
            "success": "succeeded",
            "completed": "succeeded",
            "approved": "succeeded",
            "paid": "succeeded",

            "failed": "failed",
            "error": "failed",
            "declined": "failed",
            "rejected": "failed",

            "pending": "pending",
            "processing": "processing",
            "in_progress": "processing",

            "cancelled": "cancelled",
            "canceled": "cancelled",
            "void": "cancelled",

            "refunded": "refunded",
            "partially_refunded": "partially_refunded",
        }

        return status_map.get(gateway_status.lower(), "pending")
