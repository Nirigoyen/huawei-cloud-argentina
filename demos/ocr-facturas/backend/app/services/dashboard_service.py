"""Dashboard statistics service.

Aggregates invoice data for the dashboard view.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.invoice_issuer import InvoiceIssuer
from app.models.invoice_totals import InvoiceTotals
from app.schemas.dashboard import (
    DashboardStats,
    MonthlyStats,
    SupplierStats,
)

logger = logging.getLogger(__name__)


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    """Compute aggregated dashboard statistics.

    Args:
        db: Async database session.

    Returns:
        DashboardStats with all aggregated metrics.
        Returns safe default values when the database is empty or queries fail.
    """
    # Default values for graceful degradation
    total_invoices = 0
    total_spending = Decimal("0")
    average_invoice_amount = Decimal("0")
    invoices_by_type: dict[str, int] = {}
    top_suppliers: list[SupplierStats] = []
    monthly_trend: list[MonthlyStats] = []
    status_summary: dict[str, int] = {}

    # Total invoices count
    try:
        total_result = await db.execute(select(func.count()).select_from(Invoice))
        total_invoices = total_result.scalar() or 0
    except Exception:
        logger.warning("Failed to query total invoices count, using default 0")

    # If no invoices exist, skip all join queries that depend on invoice data
    if total_invoices == 0:
        logger.info("No invoices found, returning default dashboard stats")
        return DashboardStats(
            total_invoices=0,
            total_spending=Decimal("0"),
            average_invoice_amount=Decimal("0"),
            invoices_by_type={},
            top_suppliers=[],
            monthly_trend=[],
            status_summary={},
        )

    # Total spending (sum of total_ars for completed invoices)
    try:
        spending_result = await db.execute(
            select(func.coalesce(func.sum(InvoiceTotals.total_ars), 0))
            .join(Invoice, Invoice.id == InvoiceTotals.invoice_id)
            .where(Invoice.status == "completed")
        )
        total_spending = spending_result.scalar() or Decimal("0")
    except Exception as e:
        logger.warning("Failed to query total spending, using default 0: %s", str(e))
        await db.rollback()

    # Average invoice amount
    try:
        avg_result = await db.execute(
            select(func.coalesce(func.avg(InvoiceTotals.total_ars), 0))
            .join(Invoice, Invoice.id == InvoiceTotals.invoice_id)
            .where(Invoice.status == "completed")
        )
        average_invoice_amount = avg_result.scalar() or Decimal("0")
    except Exception as e:
        logger.warning("Failed to query average invoice amount, using default 0: %s", str(e))
        await db.rollback()

    # Invoices by type
    try:
        type_result = await db.execute(
            select(Invoice.invoice_type, func.count())
            .where(Invoice.status == "completed")
            .group_by(Invoice.invoice_type)
        )
        for row in type_result:
            type_letter = row[0] or "Unknown"
            invoices_by_type[type_letter] = row[1]
    except Exception as e:
        logger.warning("Failed to query invoices by type, using empty dict: %s", str(e))
        await db.rollback()

    # Top 5 suppliers by total amount
    try:
        top_suppliers_result = await db.execute(
            select(
                InvoiceIssuer.fantasy_name,
                InvoiceIssuer.legal_name,
                InvoiceIssuer.cuit,
                func.sum(InvoiceTotals.total_ars).label("total_amount"),
                func.count().label("invoice_count"),
            )
            .join(Invoice, Invoice.id == InvoiceIssuer.invoice_id)
            .join(InvoiceTotals, InvoiceTotals.invoice_id == Invoice.id)
            .where(Invoice.status == "completed")
            .group_by(InvoiceIssuer.fantasy_name, InvoiceIssuer.legal_name, InvoiceIssuer.cuit)
            .order_by(func.sum(InvoiceTotals.total_ars).desc())
            .limit(5)
        )
        top_suppliers = [
            SupplierStats(
                fantasy_name=row[0],
                legal_name=row[1],
                cuit=row[2],
                total_amount=row[3] or Decimal("0"),
                invoice_count=row[4] or 0,
            )
            for row in top_suppliers_result
        ]
    except Exception as e:
        logger.warning("Failed to query top suppliers, using empty list: %s", str(e))
        await db.rollback()

    # Monthly trend (last 12 months)
    try:
        twelve_months_ago = date.today() - timedelta(days=365)
        # Define the month expression once and reuse it to avoid PostgreSQL
        # GROUP BY error with parameterized to_char format strings.
        # When SQLAlchemy parameterizes 'YYYY-MM' separately for SELECT, GROUP BY,
        # and ORDER BY, PostgreSQL treats them as different expressions.
        month_expr = func.to_char(Invoice.issue_date, "YYYY-MM")
        monthly_result = await db.execute(
            select(
                month_expr.label("month"),
                func.coalesce(func.sum(InvoiceTotals.total_ars), 0).label("total_amount"),
                func.count().label("invoice_count"),
            )
            .join(InvoiceTotals, InvoiceTotals.invoice_id == Invoice.id)
            .where(Invoice.status == "completed")
            .where(Invoice.issue_date >= twelve_months_ago)
            .group_by(month_expr)
            .order_by(month_expr)
        )
        monthly_trend = [
            MonthlyStats(
                month=row[0],
                total_amount=row[1] or Decimal("0"),
                invoice_count=row[2] or 0,
            )
            for row in monthly_result
        ]
    except Exception as e:
        logger.warning("Failed to query monthly trend, using empty list: %s", str(e))
        # Rollback to clear the failed transaction state in asyncpg,
        # otherwise all subsequent queries will fail with InFailedSQLTransactionError.
        await db.rollback()

    # Status summary
    try:
        status_result = await db.execute(select(Invoice.status, func.count()).group_by(Invoice.status))
        for row in status_result:
            status_summary[row[0]] = row[1]
    except Exception as e:
        logger.warning("Failed to query status summary, using empty dict: %s", str(e))
        await db.rollback()

    return DashboardStats(
        total_invoices=total_invoices,
        total_spending=total_spending,
        average_invoice_amount=average_invoice_amount,
        invoices_by_type=invoices_by_type,
        top_suppliers=top_suppliers,
        monthly_trend=monthly_trend,
        status_summary=status_summary,
    )
