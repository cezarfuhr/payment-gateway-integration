"""Worker for processing async tasks from Redis queue"""

import asyncio
import time
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.services.retry_service import RetryService
from app.services.webhook_service import WebhookService


class Worker:
    """Background worker for processing tasks"""

    def __init__(self):
        self.running = False

    async def process_retry_queue(self):
        """Process retry queue tasks"""
        async with AsyncSessionLocal() as db:
            retry_service = RetryService(db)

            # Get pending tasks
            tasks = await retry_service.get_pending_tasks()

            for task in tasks:
                logger.info(f"Processing task: {task.id} - {task.task_type}")

                try:
                    # Process task based on type
                    if task.task_type == "webhook_retry":
                        await self.process_webhook_retry(task, db)
                    elif task.task_type == "payment_sync":
                        await self.process_payment_sync(task, db)
                    else:
                        logger.warning(f"Unknown task type: {task.task_type}")

                    # Mark as success
                    await retry_service.mark_success(task.id)

                except Exception as e:
                    logger.error(f"Task processing error: {str(e)}")
                    await retry_service.mark_failure(
                        task.id,
                        str(e),
                        settings.RETRY_BACKOFF_SECONDS
                    )

    async def process_webhook_retry(self, task, db):
        """Process webhook retry task"""
        webhook_service = WebhookService(db)
        webhook_id = task.payload.get("webhook_id")

        if webhook_id:
            # Retry webhook processing
            await webhook_service.retry_failed_webhooks()

    async def process_payment_sync(self, task, db):
        """Process payment sync task"""
        from app.services.payment_service import PaymentService

        payment_service = PaymentService(db)
        payment_id = task.payload.get("payment_id")

        if payment_id:
            await payment_service.sync_payment_status(payment_id)

    async def cleanup_tasks(self):
        """Clean up old completed tasks"""
        async with AsyncSessionLocal() as db:
            retry_service = RetryService(db)
            count = await retry_service.cleanup_old_tasks(days=30)
            logger.info(f"Cleaned up {count} old tasks")

    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info("Worker started")

        while self.running:
            try:
                # Process retry queue
                await self.process_retry_queue()

                # Cleanup old tasks (once per hour)
                if int(time.time()) % 3600 < 60:
                    await self.cleanup_tasks()

                # Sleep before next iteration
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(60)

        logger.info("Worker stopped")

    def stop(self):
        """Stop the worker"""
        self.running = False


# Main entry point
async def main():
    """Main function"""
    worker = Worker()

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
