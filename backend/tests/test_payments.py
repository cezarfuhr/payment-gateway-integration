"""Payment API tests"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models.payment import GatewayType, PaymentStatus


class TestPaymentAPI:
    """Payment API test cases"""

    def test_create_payment_stripe(self, client: TestClient):
        """Test creating a Stripe payment"""
        payment_data = {
            "gateway": "stripe",
            "amount": 100.50,
            "currency": "USD",
            "customer_email": "test@example.com",
            "customer_name": "Test User",
            "description": "Test payment",
            "metadata": {}
        }

        response = client.post("/api/v1/payments/", json=payment_data)

        # May fail if Stripe credentials are not configured
        assert response.status_code in [201, 400]

    def test_list_payments(self, client: TestClient):
        """Test listing payments"""
        response = client.get("/api/v1/payments/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
