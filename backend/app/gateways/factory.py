"""Payment gateway factory"""

from typing import Dict, Any
from app.gateways.base import PaymentGateway
from app.gateways.stripe import StripeGateway
from app.gateways.paypal import PayPalGateway
from app.gateways.mercadopago import MercadoPagoGateway
from app.gateways.pagseguro import PagSeguroGateway
from app.models.payment import GatewayType
from app.core.config import settings


class GatewayFactory:
    """Factory for creating payment gateway instances"""

    @staticmethod
    def create(gateway_type: GatewayType) -> PaymentGateway:
        """
        Create a payment gateway instance

        Args:
            gateway_type: Type of gateway to create

        Returns:
            PaymentGateway instance

        Raises:
            ValueError: If gateway type is not supported
        """
        gateway_configs = {
            GatewayType.STRIPE: {
                "api_key": settings.STRIPE_API_KEY,
                "webhook_secret": settings.STRIPE_WEBHOOK_SECRET,
                "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            },
            GatewayType.PAYPAL: {
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET,
                "mode": settings.PAYPAL_MODE,
                "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            },
            GatewayType.MERCADOPAGO: {
                "access_token": settings.MERCADOPAGO_ACCESS_TOKEN,
                "public_key": settings.MERCADOPAGO_PUBLIC_KEY,
                "webhook_secret": settings.MERCADOPAGO_WEBHOOK_SECRET,
            },
            GatewayType.PAGSEGURO: {
                "email": settings.PAGSEGURO_EMAIL,
                "token": settings.PAGSEGURO_TOKEN,
                "environment": settings.PAGSEGURO_ENVIRONMENT,
            },
        }

        gateway_classes = {
            GatewayType.STRIPE: StripeGateway,
            GatewayType.PAYPAL: PayPalGateway,
            GatewayType.MERCADOPAGO: MercadoPagoGateway,
            GatewayType.PAGSEGURO: PagSeguroGateway,
        }

        if gateway_type not in gateway_classes:
            raise ValueError(f"Unsupported gateway type: {gateway_type}")

        gateway_class = gateway_classes[gateway_type]
        config = gateway_configs[gateway_type]

        return gateway_class(config)

    @staticmethod
    def get_all_gateways() -> Dict[GatewayType, PaymentGateway]:
        """
        Get instances of all payment gateways

        Returns:
            Dictionary mapping gateway types to instances
        """
        return {
            gateway_type: GatewayFactory.create(gateway_type)
            for gateway_type in GatewayType
        }
