"""Notification service for email"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger


class NotificationService:
    """Service for sending notifications"""

    def __init__(self):
        self.smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", "")
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        self.from_email = getattr(settings, "FROM_EMAIL", "noreply@payment-gateway.com")
        self.from_name = getattr(settings, "FROM_NAME", "Payment Gateway")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """Send email notification"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text version
            if body_text:
                part1 = MIMEText(body_text, "plain")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(body_html, "html")
            message.attach(part2)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_payment_success(
        self,
        to_email: str,
        amount: float,
        currency: str,
        transaction_id: str
    ) -> bool:
        """Send payment success notification"""
        subject = "Payment Successful"

        html_template = """
        <html>
            <body>
                <h2>Payment Successful!</h2>
                <p>Your payment has been processed successfully.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Amount: {{ amount }} {{ currency }}</li>
                    <li>Transaction ID: {{ transaction_id }}</li>
                </ul>
                <p>Thank you for your payment!</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            amount=amount,
            currency=currency,
            transaction_id=transaction_id
        )

        return await self.send_email(to_email, subject, body_html)

    async def send_payment_failed(
        self,
        to_email: str,
        amount: float,
        currency: str,
        error_message: str
    ) -> bool:
        """Send payment failed notification"""
        subject = "Payment Failed"

        html_template = """
        <html>
            <body>
                <h2>Payment Failed</h2>
                <p>Unfortunately, your payment could not be processed.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Amount: {{ amount }} {{ currency }}</li>
                    <li>Reason: {{ error_message }}</li>
                </ul>
                <p>Please try again or contact support.</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            amount=amount,
            currency=currency,
            error_message=error_message
        )

        return await self.send_email(to_email, subject, body_html)

    async def send_refund_processed(
        self,
        to_email: str,
        amount: float,
        currency: str,
        refund_id: str
    ) -> bool:
        """Send refund processed notification"""
        subject = "Refund Processed"

        html_template = """
        <html>
            <body>
                <h2>Refund Processed</h2>
                <p>Your refund has been processed successfully.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Amount: {{ amount }} {{ currency }}</li>
                    <li>Refund ID: {{ refund_id }}</li>
                </ul>
                <p>The funds should appear in your account within 5-10 business days.</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            amount=amount,
            currency=currency,
            refund_id=refund_id
        )

        return await self.send_email(to_email, subject, body_html)

    async def send_subscription_created(
        self,
        to_email: str,
        amount: float,
        currency: str,
        billing_cycle: str,
        next_billing_date: str
    ) -> bool:
        """Send subscription created notification"""
        subject = "Subscription Created"

        html_template = """
        <html>
            <body>
                <h2>Subscription Created!</h2>
                <p>Thank you for subscribing!</p>
                <p><strong>Subscription Details:</strong></p>
                <ul>
                    <li>Amount: {{ amount }} {{ currency }}</li>
                    <li>Billing Cycle: {{ billing_cycle }}</li>
                    <li>Next Billing Date: {{ next_billing_date }}</li>
                </ul>
                <p>You can manage your subscription at any time.</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            amount=amount,
            currency=currency,
            billing_cycle=billing_cycle,
            next_billing_date=next_billing_date
        )

        return await self.send_email(to_email, subject, body_html)

    async def send_subscription_cancelled(
        self,
        to_email: str,
        end_date: str
    ) -> bool:
        """Send subscription cancelled notification"""
        subject = "Subscription Cancelled"

        html_template = """
        <html>
            <body>
                <h2>Subscription Cancelled</h2>
                <p>Your subscription has been cancelled.</p>
                <p>Your subscription will remain active until: {{ end_date }}</p>
                <p>We're sorry to see you go!</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(end_date=end_date)

        return await self.send_email(to_email, subject, body_html)

    async def send_subscription_payment_failed(
        self,
        to_email: str,
        amount: float,
        currency: str,
        retry_date: str
    ) -> bool:
        """Send subscription payment failed notification"""
        subject = "Subscription Payment Failed"

        html_template = """
        <html>
            <body>
                <h2>Subscription Payment Failed</h2>
                <p>We were unable to process your subscription payment.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Amount: {{ amount }} {{ currency }}</li>
                    <li>Next Retry: {{ retry_date }}</li>
                </ul>
                <p>Please update your payment method to avoid service interruption.</p>
            </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            amount=amount,
            currency=currency,
            retry_date=retry_date
        )

        return await self.send_email(to_email, subject, body_html)
