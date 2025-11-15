"""Report service"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, Transaction, Report, PaymentStatus, GatewayType
from app.schemas.payment import ReportCreate
from app.core.logging import logger


class ReportService:
    """Service for report generation"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(self, report_data: ReportCreate) -> Report:
        """Create a new report"""
        # Generate report data based on type
        if report_data.report_type == "payment_summary":
            data = await self._generate_payment_summary(
                report_data.start_date,
                report_data.end_date
            )
        elif report_data.report_type == "gateway_performance":
            data = await self._generate_gateway_performance(
                report_data.start_date,
                report_data.end_date
            )
        elif report_data.report_type == "transaction_volume":
            data = await self._generate_transaction_volume(
                report_data.start_date,
                report_data.end_date
            )
        else:
            data = {}

        report = Report(
            report_type=report_data.report_type,
            start_date=report_data.start_date,
            end_date=report_data.end_date,
            data=data,
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        logger.info(f"Report created: {report.id} - {report.report_type}")
        return report

    async def get_report(self, report_id: UUID) -> Optional[Report]:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """List reports"""
        result = await self.db.execute(
            select(Report)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _generate_payment_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate payment summary report"""
        # Total payments
        total_result = await self.db.execute(
            select(func.count(Payment.id))
            .where(Payment.created_at >= start_date)
            .where(Payment.created_at <= end_date)
        )
        total_payments = total_result.scalar()

        # Total amount
        amount_result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(Payment.created_at >= start_date)
            .where(Payment.created_at <= end_date)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
        )
        total_amount = amount_result.scalar() or Decimal(0)

        # Status breakdown
        status_result = await self.db.execute(
            select(
                Payment.status,
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('amount')
            )
            .where(Payment.created_at >= start_date)
            .where(Payment.created_at <= end_date)
            .group_by(Payment.status)
        )

        status_breakdown = {
            row.status.value: {
                "count": row.count,
                "amount": float(row.amount or 0)
            }
            for row in status_result
        }

        return {
            "total_payments": total_payments,
            "total_amount": float(total_amount),
            "status_breakdown": status_breakdown,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }

    async def _generate_gateway_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate gateway performance report"""
        gateway_result = await self.db.execute(
            select(
                Payment.gateway,
                func.count(Payment.id).label('total'),
                func.sum(
                    func.cast(Payment.status == PaymentStatus.SUCCEEDED, type_=func.Integer())
                ).label('succeeded'),
                func.sum(
                    func.cast(Payment.status == PaymentStatus.FAILED, type_=func.Integer())
                ).label('failed'),
                func.avg(Payment.amount).label('avg_amount'),
                func.sum(Payment.amount).label('total_amount')
            )
            .where(Payment.created_at >= start_date)
            .where(Payment.created_at <= end_date)
            .group_by(Payment.gateway)
        )

        gateway_stats = {}
        for row in gateway_result:
            success_rate = (row.succeeded / row.total * 100) if row.total > 0 else 0

            gateway_stats[row.gateway.value] = {
                "total_payments": row.total,
                "succeeded": row.succeeded or 0,
                "failed": row.failed or 0,
                "success_rate": round(success_rate, 2),
                "avg_amount": float(row.avg_amount or 0),
                "total_amount": float(row.total_amount or 0),
            }

        return {
            "gateway_performance": gateway_stats,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }

    async def _generate_transaction_volume(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate transaction volume report"""
        # Daily volume
        daily_result = await self.db.execute(
            select(
                func.date(Payment.created_at).label('date'),
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('amount')
            )
            .where(Payment.created_at >= start_date)
            .where(Payment.created_at <= end_date)
            .group_by(func.date(Payment.created_at))
            .order_by(func.date(Payment.created_at))
        )

        daily_volume = [
            {
                "date": str(row.date),
                "count": row.count,
                "amount": float(row.amount or 0)
            }
            for row in daily_result
        ]

        return {
            "daily_volume": daily_volume,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        # Today's stats
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        today_result = await self.db.execute(
            select(
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('amount')
            )
            .where(Payment.created_at >= today)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
        )
        today_stats = today_result.one()

        # Total stats
        total_result = await self.db.execute(
            select(
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('amount')
            )
            .where(Payment.status == PaymentStatus.SUCCEEDED)
        )
        total_stats = total_result.one()

        # Recent payments
        recent_result = await self.db.execute(
            select(Payment)
            .order_by(Payment.created_at.desc())
            .limit(10)
        )
        recent_payments = recent_result.scalars().all()

        return {
            "today": {
                "count": today_stats.count,
                "amount": float(today_stats.amount or 0)
            },
            "total": {
                "count": total_stats.count,
                "amount": float(total_stats.amount or 0)
            },
            "recent_payments": [
                {
                    "id": str(payment.id),
                    "amount": float(payment.amount),
                    "status": payment.status.value,
                    "gateway": payment.gateway.value,
                    "created_at": payment.created_at.isoformat()
                }
                for payment in recent_payments
            ]
        }
