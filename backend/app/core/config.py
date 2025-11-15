"""Application configuration"""

from typing import List
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_SECRET_KEY: str = Field(...)
    API_ENVIRONMENT: str = Field(default="development")

    # Database
    DATABASE_URL: PostgresDsn = Field(...)

    # Redis
    REDIS_URL: RedisDsn = Field(...)

    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from string"""
        return [origin.strip() for origin in v.split(",")]

    # Stripe
    STRIPE_API_KEY: str = Field(...)
    STRIPE_WEBHOOK_SECRET: str = Field(...)
    STRIPE_PUBLISHABLE_KEY: str = Field(...)

    # PayPal
    PAYPAL_CLIENT_ID: str = Field(...)
    PAYPAL_CLIENT_SECRET: str = Field(...)
    PAYPAL_MODE: str = Field(default="sandbox")
    PAYPAL_WEBHOOK_ID: str = Field(...)

    # Mercado Pago
    MERCADOPAGO_ACCESS_TOKEN: str = Field(...)
    MERCADOPAGO_PUBLIC_KEY: str = Field(...)
    MERCADOPAGO_WEBHOOK_SECRET: str = Field(...)

    # PagSeguro
    PAGSEGURO_EMAIL: str = Field(...)
    PAGSEGURO_TOKEN: str = Field(...)
    PAGSEGURO_ENVIRONMENT: str = Field(default="sandbox")

    # Security
    ENCRYPTION_KEY: str = Field(...)
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # Retry Configuration
    MAX_RETRY_ATTEMPTS: int = Field(default=3)
    RETRY_BACKOFF_SECONDS: int = Field(default=60)


# Global settings instance
settings = Settings()
