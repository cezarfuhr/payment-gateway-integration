"""Retry service for failed operations"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import RetryQueue
from app.core.logging import logger
from app.core.redis import redis_client


class RetryService:
    """Service for retry queue operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        max_attempts: int = 3,
        backoff_seconds: int = 60
    ) -> RetryQueue:
        """Add a task to retry queue"""
        next_retry = datetime.utcnow() + timedelta(seconds=backoff_seconds)

        task = RetryQueue(
            task_type=task_type,
            payload=payload,
            max_attempts=max_attempts,
            next_retry_at=next_retry,
            status="pending",
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Also add to Redis for worker processing
        self._queue_in_redis(task)

        logger.info(f"Task enqueued: {task.id} - {task_type}")
        return task

    async def get_pending_tasks(self) -> List[RetryQueue]:
        """Get all pending tasks ready for retry"""
        now = datetime.utcnow()

        result = await self.db.execute(
            select(RetryQueue)
            .where(RetryQueue.status == "pending")
            .where(RetryQueue.attempts < RetryQueue.max_attempts)
            .where(RetryQueue.next_retry_at <= now)
        )

        return list(result.scalars().all())

    async def mark_success(self, task_id: UUID) -> Optional[RetryQueue]:
        """Mark a task as successful"""
        task = await self.get_task(task_id)

        if not task:
            return None

        task.status = "completed"
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(f"Task completed: {task_id}")
        return task

    async def mark_failure(
        self,
        task_id: UUID,
        error_message: str,
        backoff_seconds: int = 60
    ) -> Optional[RetryQueue]:
        """Mark a task as failed and schedule retry"""
        task = await self.get_task(task_id)

        if not task:
            return None

        task.attempts += 1
        task.last_error = error_message

        if task.attempts >= task.max_attempts:
            task.status = "failed"
            logger.error(f"Task failed after {task.attempts} attempts: {task_id}")
        else:
            # Calculate exponential backoff
            backoff = backoff_seconds * (2 ** task.attempts)
            task.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff)
            task.status = "pending"

            # Re-queue in Redis
            self._queue_in_redis(task)

            logger.warning(
                f"Task retry scheduled: {task_id} - "
                f"Attempt {task.attempts}/{task.max_attempts}"
            )

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task(self, task_id: UUID) -> Optional[RetryQueue]:
        """Get task by ID"""
        result = await self.db.execute(
            select(RetryQueue).where(RetryQueue.id == task_id)
        )
        return result.scalar_one_or_none()

    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """Clean up old completed or failed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(RetryQueue)
            .where(RetryQueue.status.in_(["completed", "failed"]))
            .where(RetryQueue.created_at < cutoff_date)
        )

        tasks = result.scalars().all()
        count = len(tasks)

        for task in tasks:
            await self.db.delete(task)

        await self.db.commit()

        logger.info(f"Cleaned up {count} old tasks")
        return count

    def _queue_in_redis(self, task: RetryQueue) -> None:
        """Queue task in Redis for worker processing"""
        try:
            task_data = {
                "id": str(task.id),
                "task_type": task.task_type,
                "payload": task.payload,
                "next_retry_at": task.next_retry_at.isoformat(),
            }

            # Use Redis sorted set with score as timestamp
            score = task.next_retry_at.timestamp()
            redis_client.zadd(
                "retry_queue",
                {str(task.id): score}
            )

            # Store task data
            redis_client.hset(
                f"task:{task.id}",
                mapping={
                    "data": str(task_data)
                }
            )

            redis_client.expire(f"task:{task.id}", 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Redis queue error: {str(e)}")
