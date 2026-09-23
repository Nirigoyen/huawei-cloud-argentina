"""Dashboard API router - statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Get aggregated dashboard statistics.

    Returns:
    - Total invoices count
    - Total spending (sum of all completed invoices)
    - Average invoice amount
    - Invoices by type (A, B, C, E, M)
    - Top 5 suppliers by total amount
    - Monthly spending trend (last 12 months)
    - Status summary (processing, completed, failed counts)
    """
    return await get_dashboard_stats(db)
