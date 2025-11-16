"""Report API routes"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.payment import ReportCreate, ReportResponse
from app.services.report_service import ReportService
from app.api.deps import get_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report: ReportCreate,
    service: ReportService = Depends(get_report_service)
):
    """Create a new report"""
    try:
        result = await service.create_report(report)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    service: ReportService = Depends(get_report_service)
):
    """List reports"""
    reports = await service.list_reports(skip, limit)
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service)
):
    """Get report by ID"""
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    return report


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    service: ReportService = Depends(get_report_service)
):
    """Get dashboard statistics"""
    stats = await service.get_dashboard_stats()
    return stats
