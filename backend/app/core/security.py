"""Security utilities"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption
cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode()[:44].ljust(44, b'='))


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        return None


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    encrypted = cipher_suite.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    decrypted = cipher_suite.decrypt(encrypted_data.encode())
    return decrypted.decode()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.__dict__[algorithm]
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def mask_card_number(card_number: str) -> str:
    """Mask credit card number for PCI compliance"""
    if len(card_number) < 4:
        return "****"

    return "*" * (len(card_number) - 4) + card_number[-4:]


def sanitize_sensitive_data(data: dict) -> dict:
    """Remove sensitive data from dict for logging"""
    sensitive_fields = {
        "card_number",
        "cvv",
        "password",
        "token",
        "secret",
        "api_key",
        "access_token"
    }

    sanitized = {}
    for key, value in data.items():
        if any(field in key.lower() for field in sensitive_fields):
            if "card" in key.lower():
                sanitized[key] = mask_card_number(str(value))
            else:
                sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        else:
            sanitized[key] = value

    return sanitized
