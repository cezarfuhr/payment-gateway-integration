"""Idempotency middleware"""

import json
from datetime import datetime, timedelta
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import AsyncSessionLocal
from app.models.idempotency import IdempotencyKey
from app.core.logging import logger


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to handle idempotency keys"""

    # Methods that should use idempotency
    IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}

    # Paths that require idempotency
    IDEMPOTENT_PATHS = {
        "/api/v1/payments/",
        "/api/v1/payments/refunds",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with idempotency check"""

        # Check if request should use idempotency
        if not self._should_check_idempotency(request):
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            # For critical endpoints, require idempotency key
            if request.url.path in self.IDEMPOTENT_PATHS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Idempotency-Key header is required for this endpoint"
                )
            return await call_next(request)

        # Check for existing request with this key
        async with AsyncSessionLocal() as db:
            existing = await self._get_existing_request(db, idempotency_key)

            if existing:
                # Return cached response
                logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
                return Response(
                    content=json.dumps(existing.response_body),
                    status_code=existing.response_status,
                    media_type="application/json"
                )

            # Process new request
            request_body = await self._get_request_body(request)

            # Call next middleware
            response = await call_next(request)

            # Cache response
            if 200 <= response.status_code < 300:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                await self._cache_response(
                    db,
                    idempotency_key,
                    request,
                    request_body,
                    response.status_code,
                    json.loads(response_body.decode()) if response_body else {}
                )

                # Return response
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            return response

    def _should_check_idempotency(self, request: Request) -> bool:
        """Check if request should use idempotency"""
        return (
            request.method in self.IDEMPOTENT_METHODS and
            any(path in request.url.path for path in self.IDEMPOTENT_PATHS)
        )

    async def _get_existing_request(
        self,
        db,
        idempotency_key: str
    ) -> IdempotencyKey | None:
        """Get existing request by idempotency key"""
        result = await db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key,
                IdempotencyKey.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()

    async def _get_request_body(self, request: Request) -> dict:
        """Get request body as dict"""
        try:
            body = await request.body()
            return json.loads(body.decode()) if body else {}
        except:
            return {}

    async def _cache_response(
        self,
        db,
        idempotency_key: str,
        request: Request,
        request_body: dict,
        status_code: int,
        response_body: dict
    ):
        """Cache response for idempotency key"""
        try:
            # Expire after 24 hours
            expires_at = datetime.utcnow() + timedelta(hours=24)

            idempotency_record = IdempotencyKey(
                key=idempotency_key,
                request_path=request.url.path,
                request_method=request.method,
                request_body=request_body,
                response_status=status_code,
                response_body=response_body,
                expires_at=expires_at
            )

            db.add(idempotency_record)
            await db.commit()

            logger.info(f"Cached response for idempotency key: {idempotency_key}")

        except Exception as e:
            logger.error(f"Failed to cache idempotency response: {e}")
            # Don't fail the request if caching fails
            pass
