"""Main FastAPI application"""

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.database import async_engine
from app.core.redis import async_redis_client
from app.api.routes import payments, webhooks, reports, auth
from app.schemas.payment import HealthCheck
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.rate_limit import limiter
from app import __version__

# Initialize Sentry
if hasattr(settings, "SENTRY_DSN") and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.API_ENVIRONMENT,
        traces_sample_rate=0.1 if settings.API_ENVIRONMENT == "production" else 1.0,
    )

# Create FastAPI app
app = FastAPI(
    title="Payment Gateway Integration API",
    description="Unified payment gateway integration with multiple providers",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middlewares
app.state.limiter = limiter

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idempotency middleware
app.add_middleware(IdempotencyMiddleware)


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Payment Gateway Integration API...")
    logger.info(f"Environment: {settings.API_ENVIRONMENT}")
    logger.info(f"Version: {__version__}")

    # Test database connection
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    # Test Redis connection
    try:
        await async_redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Payment Gateway Integration API...")

    # Close database connections
    await async_engine.dispose()

    # Close Redis connection
    await async_redis_client.close()

    logger.info("Shutdown complete")


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    # Check database
    db_status = "healthy"
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    # Check Redis
    redis_status = "healthy"
    try:
        await async_redis_client.ping()
    except Exception:
        redis_status = "unhealthy"

    return HealthCheck(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        version=__version__,
        database=db_status,
        redis=redis_status,
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Payment Gateway Integration API",
        "version": __version__,
        "status": "operational",
        "docs": "/docs",
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_ENVIRONMENT == "development",
    )
