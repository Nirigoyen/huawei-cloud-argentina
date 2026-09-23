"""Chatbot intent definitions and parameterized SQL query templates.

Each intent maps to a pre-defined, read-only SQL query template
with parameterized slots. The LLM identifies the user's intent
and extracts parameters, which are then substituted into the
corresponding template for safe execution.
"""

from pydantic import BaseModel


class IntentDefinition(BaseModel):
    """Definition of a single chatbot intent."""

    name: str
    description: str
    parameter_names: list[str]
    sql_template: str
    response_template: str
    example_questions: list[str]


# =============================================================================
# Intent Definitions
# =============================================================================

INTENT_DEFINITIONS: dict[str, IntentDefinition] = {
    "total_spending": IntentDefinition(
        name="total_spending",
        description="Gasto total en un período de tiempo",
        parameter_names=["start_date", "end_date"],
        sql_template="""
            SELECT COALESCE(SUM(it.total_ars), 0) as total
            FROM invoices i
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            AND i.issue_date >= :start_date
            AND i.issue_date <= :end_date
        """,
        response_template="Total spending from {start_date} to {end_date}: ARS {total}",
        example_questions=[
            "¿Cuánto gastamos este mes?",
            "¿Cuál es el gasto total de este año?",
            "¿Gasto total del mes pasado?",
        ],
    ),
    "top_suppliers": IntentDefinition(
        name="top_suppliers",
        description="Top N proveedores por monto total",
        parameter_names=["limit"],
        sql_template="""
            SELECT iss.fantasy_name, iss.legal_name, iss.cuit,
                   SUM(it.total_ars) as total_amount
            FROM invoices i
            JOIN invoice_issuers iss ON iss.invoice_id = i.id
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            GROUP BY iss.fantasy_name, iss.legal_name, iss.cuit
            ORDER BY total_amount DESC
            LIMIT :limit
        """,
        response_template="Top {limit} suppliers by total amount",
        example_questions=[
            "¿Quiénes son nuestros top 5 proveedores?",
            "Muéstrame los proveedores más utilizados",
        ],
    ),
    "supplier_spending": IntentDefinition(
        name="supplier_spending",
        description="Gasto para un proveedor específico en un período",
        parameter_names=["supplier_name", "start_date", "end_date"],
        sql_template="""
            SELECT COALESCE(SUM(it.total_ars), 0) as total
            FROM invoices i
            JOIN invoice_issuers iss ON iss.invoice_id = i.id
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            AND (iss.fantasy_name ILIKE :supplier_pattern
                 OR iss.legal_name ILIKE :supplier_pattern)
            AND i.issue_date >= :start_date
            AND i.issue_date <= :end_date
        """,
        response_template="Spending for supplier '{supplier_name}' from {start_date} to {end_date}: ARS {total}",
        example_questions=[
            "¿Cuánto le pagamos al Proveedor X este año?",
            "¿Cuánto gastamos en Acme Corp el mes pasado?",
        ],
    ),
    "invoices_above_amount": IntentDefinition(
        name="invoices_above_amount",
        description="Facturas que superan un monto umbral",
        parameter_names=["amount"],
        sql_template="""
            SELECT i.id, i.complete_number, i.issue_date,
                   iss.fantasy_name, it.total_ars
            FROM invoices i
            JOIN invoice_issuers iss ON iss.invoice_id = i.id
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            AND it.total_ars >= :amount
            ORDER BY it.total_ars DESC
            LIMIT 50
        """,
        response_template="Invoices above ARS {amount}",
        example_questions=[
            "Mostrar facturas mayores a $1.000.000",
            "¿Qué facturas superan los 500.000 pesos?",
        ],
    ),
    "most_recent_invoice": IntentDefinition(
        name="most_recent_invoice",
        description="Detalles de la factura más reciente",
        parameter_names=[],
        sql_template="""
            SELECT i.id, i.complete_number, i.issue_date, i.invoice_type,
                   i.currency, i.cae,
                   iss.fantasy_name as issuer_name, iss.cuit as issuer_cuit,
                   it.total_ars, it.net_amount, it.iva_amount
            FROM invoices i
            JOIN invoice_issuers iss ON iss.invoice_id = i.id
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            ORDER BY i.issue_date DESC NULLS LAST
            LIMIT 1
        """,
        response_template="Most recent invoice",
        example_questions=[
            "¿Cuál fue la última factura que recibimos?",
            "Muéstrame la factura más reciente",
        ],
    ),
    "iva_total": IntentDefinition(
        name="iva_total",
        description="Total de IVA pagado en un período",
        parameter_names=["start_date", "end_date"],
        sql_template="""
            SELECT COALESCE(SUM(it.iva_amount), 0) as total_iva
            FROM invoices i
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            AND i.issue_date >= :start_date
            AND i.issue_date <= :end_date
        """,
        response_template="Total IVA from {start_date} to {end_date}: ARS {total_iva}",
        example_questions=[
            "¿Cuánto IVA pagamos este trimestre?",
            "¿Total de IVA este mes?",
        ],
    ),
    "spending_by_month": IntentDefinition(
        name="spending_by_month",
        description="Desglose mensual de gastos en un período",
        parameter_names=["start_date", "end_date"],
        sql_template="""
            SELECT TO_CHAR(i.issue_date, 'YYYY-MM') as month,
                   COALESCE(SUM(it.total_ars), 0) as total_amount,
                   COUNT(*) as invoice_count
            FROM invoices i
            JOIN invoice_totals it ON it.invoice_id = i.id
            WHERE i.status = 'completed'
            AND i.issue_date >= :start_date
            AND i.issue_date <= :end_date
            GROUP BY TO_CHAR(i.issue_date, 'YYYY-MM')
            ORDER BY month
        """,
        response_template="Monthly spending from {start_date} to {end_date}",
        example_questions=[
            "Muéstrame el gasto por mes de este año",
            "Desglose mensual de los últimos 6 meses",
        ],
    ),
    "invoice_count": IntentDefinition(
        name="invoice_count",
        description="Cantidad de facturas en un período",
        parameter_names=["start_date", "end_date"],
        sql_template="""
            SELECT COUNT(*) as count
            FROM invoices
            WHERE status = 'completed'
            AND issue_date >= :start_date
            AND issue_date <= :end_date
        """,
        response_template="Number of invoices from {start_date} to {end_date}: {count}",
        example_questions=[
            "¿Cuántas facturas recibimos este mes?",
            "¿Cantidad de facturas de este año?",
        ],
    ),
}


# =============================================================================
# Table/Column whitelist for query execution safety
# =============================================================================

ALLOWED_TABLES: set[str] = {
    "invoices",
    "invoice_issuers",
    "invoice_clients",
    "invoice_line_items",
    "invoice_totals",
}

DENIED_TABLES: set[str] = {
    "chatbot_query_logs",
    "app_settings",
    "alembic_version",
}


def get_intent_names() -> list[str]:
    """Get list of all valid intent names."""
    return list(INTENT_DEFINITIONS.keys())


def get_intent_descriptions_for_prompt() -> str:
    """Generate a formatted list of intents for the LLM system prompt."""
    lines = []
    for idx, (name, intent) in enumerate(INTENT_DEFINITIONS.items(), 1):
        params = ", ".join(intent.parameter_names) if intent.parameter_names else "none"
        lines.append(f"{idx}. {name} - {intent.description}. Parameters: {params}")
    return "\n".join(lines)
