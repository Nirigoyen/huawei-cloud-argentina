"""Initial schema - create all tables.

Revision ID: 001
Revises: None
Create Date: 2026-09-11 23:00:00.000000

Creates the following tables:
- invoices: Main invoice records with processing status and file metadata
- invoice_issuers: Invoice issuer (emisor) data (one-to-one with invoices)
- invoice_clients: Invoice client/receiver data (one-to-one with invoices)
- invoice_line_items: Invoice line items (one-to-many with invoices)
- invoice_totals: Invoice financial totals (one-to-one with invoices)
- chatbot_query_logs: Chatbot query audit log
- app_settings: Application settings and API credentials
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables with indexes, constraints, and foreign keys."""

    # =========================================================================
    # 1. invoices table
    # =========================================================================
    op.create_table(
        "invoices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(12),
            server_default="processing",
            nullable=False,
        ),
        sa.Column("invoice_type", sa.String(1), nullable=True),
        sa.Column("invoice_code", sa.String(3), nullable=True),
        sa.Column("point_of_sale", sa.String(4), nullable=True),
        sa.Column("invoice_number", sa.String(8), nullable=True),
        sa.Column("complete_number", sa.String(13), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("exchange_rate", sa.String(50), nullable=True),
        sa.Column("cae", sa.String(14), nullable=True),
        sa.Column("cae_expiry_date", sa.Date(), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("ocr_status_code", sa.Integer(), nullable=True),
        sa.Column("text_blocks_count", sa.Integer(), nullable=True),
        sa.Column(
            "validation_warnings",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name="ck_invoices_status",
        ),
        sa.CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 15728640",
            name="ck_invoices_file_size",
        ),
    )

    # Indexes for invoices
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"])
    op.create_index("ix_invoices_complete_number", "invoices", ["complete_number"])
    op.create_index("ix_invoices_invoice_type", "invoices", ["invoice_type"])

    # =========================================================================
    # 2. invoice_issuers table
    # =========================================================================
    op.create_table(
        "invoice_issuers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("fantasy_name", sa.String(200), nullable=True),
        sa.Column("legal_name", sa.String(300), nullable=True),
        sa.Column("cuit", sa.String(13), nullable=True),
        sa.Column("fiscal_condition", sa.String(100), nullable=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("locality", sa.String(100), nullable=True),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("activity_start", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("invoice_id", name="uq_invoice_issuers_invoice_id"),
    )

    # Index for invoice_issuers
    op.create_index("ix_invoice_issuers_cuit", "invoice_issuers", ["cuit"])

    # =========================================================================
    # 3. invoice_clients table
    # =========================================================================
    op.create_table(
        "invoice_clients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("legal_name", sa.String(300), nullable=True),
        sa.Column("document_type", sa.String(20), nullable=True),
        sa.Column("document_number", sa.String(20), nullable=True),
        sa.Column("fiscal_condition", sa.String(100), nullable=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("locality", sa.String(100), nullable=True),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("sale_condition", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("invoice_id", name="uq_invoice_clients_invoice_id"),
    )

    # =========================================================================
    # 4. invoice_line_items table
    # =========================================================================
    op.create_table(
        "invoice_line_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("line_order", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=True),
        sa.Column("unit", sa.String(30), nullable=True),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=True),
        sa.Column("discount", sa.Numeric(15, 2), nullable=True),
        sa.Column("subtotal_without_iva", sa.Numeric(15, 2), nullable=True),
        sa.Column("iva_rate", sa.String(10), nullable=True),
        sa.Column("total_with_iva", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "line_order > 0",
            name="ck_line_items_line_order",
        ),
    )

    # Index for invoice_line_items
    op.create_index(
        "ix_line_items_invoice_order",
        "invoice_line_items",
        ["invoice_id", "line_order"],
    )

    # =========================================================================
    # 5. invoice_totals table
    # =========================================================================
    op.create_table(
        "invoice_totals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("net_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("iva_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("iva_detail", postgresql.JSONB(), nullable=True),
        sa.Column("other_taxes", sa.Numeric(15, 2), nullable=True),
        sa.Column("total_invoice_currency", sa.Numeric(15, 2), nullable=True),
        sa.Column("total_ars", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("invoice_id", name="uq_invoice_totals_invoice_id"),
    )

    # =========================================================================
    # 6. chatbot_query_logs table
    # =========================================================================
    op.create_table(
        "chatbot_query_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("question", sa.String(1000), nullable=False),
        sa.Column("identified_intent", sa.String(50), nullable=True),
        sa.Column("query_parameters", postgresql.JSONB(), nullable=True),
        sa.Column("result_summary", sa.String(500), nullable=True),
        sa.Column("response_text", sa.String(2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index for chatbot_query_logs
    op.create_index(
        "ix_chatbot_logs_created_at",
        "chatbot_query_logs",
        ["created_at"],
    )

    # =========================================================================
    # 7. app_settings table
    # =========================================================================
    op.create_table(
        "app_settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=True),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column(
            "is_secret",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    # =========================================================================
    # 8. Seed default settings
    # =========================================================================
    op.execute(
        """
        INSERT INTO app_settings (key, value, description, is_secret) VALUES
            ('HUAWEI_IAM_USERNAME', NULL, 'Huawei Cloud IAM username', true),
            ('HUAWEI_IAM_PASSWORD', NULL, 'Huawei Cloud IAM password', true),
            ('HUAWEI_PROJECT_ID', NULL, 'Huawei Cloud project ID (Hong Kong region)', true),
            ('DIFY_API_KEY', NULL, 'Dify workflow API key', true),
            ('MAAS_API_KEY', NULL, 'Huawei MaaS API key', true),
            ('MAAS_ENDPOINT_URL', NULL, 'Huawei MaaS API endpoint URL', false),
            ('MAAS_MODEL_NAME', 'deepseek-v3', 'MaaS model name for chatbot', false)
        ON CONFLICT (key) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""

    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table("app_settings")
    op.drop_table("chatbot_query_logs")
    op.drop_table("invoice_totals")
    op.drop_table("invoice_line_items")
    op.drop_table("invoice_clients")
    op.drop_table("invoice_issuers")
    op.drop_table("invoices")
