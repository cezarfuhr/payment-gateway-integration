"""Rate limiting middleware"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.core.redis import redis_client


def get_identifier(request: Request) -> str:
    """Get identifier for rate limiting"""
    # Try to get API key from header
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"api_key:{api_key}"

    # Try to get user from auth
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    storage_uri=f"redis://redis:6379",
    default_limits=["100/minute"],
)


# Rate limit configurations for different endpoints
rate_limits = {
    # Auth endpoints - more restrictive
    "auth_login": "5/minute",
    "auth_register": "3/minute",

    # Payment endpoints - moderate
    "payment_create": "10/minute",
    "payment_list": "60/minute",

    # Webhook endpoints - high throughput
    "webhook": "1000/minute",

    # Reports - moderate
    "report_create": "10/minute",
    "report_list": "30/minute",
}
