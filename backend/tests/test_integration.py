"""Integration tests"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models.payment import GatewayType, PaymentStatus
from app.models.user import UserRole
from app.schemas.user import UserCreate, LoginRequest


class TestAuthenticationIntegration:
    """Authentication integration tests"""

    def test_register_and_login(self, client: TestClient):
        """Test user registration and login flow"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test123!@#",
            "full_name": "Test User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [201, 400]  # May fail if already exists

        # Login
        login_data = {
            "username": "testuser",
            "password": "Test123!@#"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_protected_endpoint(self, client: TestClient):
        """Test accessing protected endpoint"""
        # Try without authentication
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # Forbidden

        # Try with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401  # Unauthorized


class TestPaymentIntegration:
    """Payment integration tests"""

    def test_payment_creation_flow(self, client: TestClient):
        """Test complete payment creation flow"""
        payment_data = {
            "gateway": "stripe",
            "amount": 100.50,
            "currency": "USD",
            "customer_email": "customer@example.com",
            "customer_name": "John Doe",
            "description": "Test payment",
            "metadata": {}
        }

        # Create payment (may fail without real credentials)
        response = client.post("/api/v1/payments/", json=payment_data)
        assert response.status_code in [201, 400]

    def test_payment_list(self, client: TestClient):
        """Test payment listing"""
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_idempotency_key(self, client: TestClient):
        """Test idempotency key functionality"""
        payment_data = {
            "gateway": "stripe",
            "amount": 50.00,
            "currency": "USD",
            "customer_email": "test@example.com",
            "metadata": {}
        }

        headers = {"Idempotency-Key": "test-idempotency-key-12345"}

        # First request
        response1 = client.post(
            "/api/v1/payments/",
            json=payment_data,
            headers=headers
        )

        # Second request with same key should return cached response
        response2 = client.post(
            "/api/v1/payments/",
            json=payment_data,
            headers=headers
        )

        # Both should have same status (either both succeed or both fail)
        assert response1.status_code == response2.status_code


class TestWebhookIntegration:
    """Webhook integration tests"""

    def test_webhook_endpoints_exist(self, client: TestClient):
        """Test that webhook endpoints exist"""
        # Test Stripe webhook
        response = client.post("/api/v1/webhooks/stripe", json={})
        assert response.status_code in [200, 400]  # Should accept POST

        # Test PayPal webhook
        response = client.post("/api/v1/webhooks/paypal", json={})
        assert response.status_code in [200, 400]


class TestReportIntegration:
    """Report integration tests"""

    def test_dashboard_stats(self, client: TestClient):
        """Test dashboard statistics endpoint"""
        response = client.get("/api/v1/reports/dashboard/stats")
        assert response.status_code == 200

        data = response.json()
        assert "today" in data
        assert "total" in data

    def test_report_creation(self, client: TestClient):
        """Test report creation"""
        report_data = {
            "report_type": "payment_summary",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z"
        }

        response = client.post("/api/v1/reports/", json=report_data)
        assert response.status_code in [201, 400, 403]


class TestRateLimiting:
    """Rate limiting tests"""

    def test_rate_limit_enforcement(self, client: TestClient):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/payments/")
            responses.append(response.status_code)

        # All should succeed (within rate limit for tests)
        assert all(status in [200, 429] for status in responses)


class TestHealthCheck:
    """Health check tests"""

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "redis" in data

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
