"""Webhook API routes"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional

from app.schemas.payment import WebhookCreate, WebhookResponse
from app.models.payment import GatewayType
from app.services.webhook_service import WebhookService
from app.api.deps import get_webhook_service
from app.core.logging import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    service: WebhookService = Depends(get_webhook_service)
):
    """Handle Stripe webhook"""
    try:
        body = await request.body()
        payload = await request.json()

        webhook_data = WebhookCreate(
            gateway=GatewayType.STRIPE,
            event_type=payload.get("type", ""),
            payload=payload,
            signature=stripe_signature
        )

        webhook = await service.create_webhook(webhook_data)

        # Process webhook
        success = await service.process_webhook(
            webhook.id,
            body,
            stripe_signature or "",
            dict(request.headers)
        )

        if not success:
            logger.warning(f"Stripe webhook processing failed: {webhook.id}")

        return {"received": True, "webhook_id": str(webhook.id)}

    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    service: WebhookService = Depends(get_webhook_service)
):
    """Handle PayPal webhook"""
    try:
        body = await request.body()
        payload = await request.json()

        headers = dict(request.headers)
        signature = headers.get("paypal-transmission-sig", "")

        webhook_data = WebhookCreate(
            gateway=GatewayType.PAYPAL,
            event_type=payload.get("event_type", ""),
            payload=payload,
            signature=signature
        )

        webhook = await service.create_webhook(webhook_data)

        # Process webhook
        success = await service.process_webhook(
            webhook.id,
            body,
            signature,
            headers
        )

        if not success:
            logger.warning(f"PayPal webhook processing failed: {webhook.id}")

        return {"received": True, "webhook_id": str(webhook.id)}

    except Exception as e:
        logger.error(f"PayPal webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="x-signature"),
    service: WebhookService = Depends(get_webhook_service)
):
    """Handle Mercado Pago webhook"""
    try:
        body = await request.body()
        payload = await request.json()

        webhook_data = WebhookCreate(
            gateway=GatewayType.MERCADOPAGO,
            event_type=payload.get("type", ""),
            payload=payload,
            signature=x_signature
        )

        webhook = await service.create_webhook(webhook_data)

        # Process webhook
        success = await service.process_webhook(
            webhook.id,
            body,
            x_signature or "",
            dict(request.headers)
        )

        if not success:
            logger.warning(f"Mercado Pago webhook processing failed: {webhook.id}")

        return {"received": True, "webhook_id": str(webhook.id)}

    except Exception as e:
        logger.error(f"Mercado Pago webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pagseguro")
async def pagseguro_webhook(
    request: Request,
    service: WebhookService = Depends(get_webhook_service)
):
    """Handle PagSeguro webhook"""
    try:
        body = await request.body()
        payload = await request.json()

        webhook_data = WebhookCreate(
            gateway=GatewayType.PAGSEGURO,
            event_type="notification",
            payload=payload,
            signature=None
        )

        webhook = await service.create_webhook(webhook_data)

        # Process webhook
        success = await service.process_webhook(
            webhook.id,
            body,
            "",
            dict(request.headers)
        )

        if not success:
            logger.warning(f"PagSeguro webhook processing failed: {webhook.id}")

        return {"received": True, "webhook_id": str(webhook.id)}

    except Exception as e:
        logger.error(f"PagSeguro webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
