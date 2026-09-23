"""AppSettings SQLAlchemy ORM model.

Stores application settings and API credentials in the database.
For the MVP, credentials are stored as plain text. In a future
version, they should be encrypted at rest.

Note: Per the security design, the primary credential storage is
environment variables / .env file. This table serves as a backup
and for the Settings UI to display masked credential status.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AppSettings(UUIDPrimaryKeyMixin, Base):
    """ORM model for the app_settings table.

    Stores application configuration key-value pairs, primarily
    for API credentials. Each row represents a single setting.

    Attributes:
        id: UUID primary key (server-generated).
        key: Unique setting key (e.g., 'HUAWEI_IAM_USERNAME').
        value: Setting value (plain text for MVP, encrypted in future).
        description: Human-readable description of the setting.
        is_secret: Whether the value should be masked in API responses.
        created_at: Timestamp when the setting was created.
        updated_at: Timestamp when the setting was last updated.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        doc="Unique setting key (e.g., HUAWEI_IAM_USERNAME)",
    )
    value: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Setting value (plain text for MVP)",
    )
    description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        doc="Human-readable description of the setting",
    )
    is_secret: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="true",
        doc="Whether the value should be masked in API responses",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the setting was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the setting was last updated",
    )

    def __repr__(self) -> str:
        masked_value = "••••••••" if self.is_secret and self.value else self.value
        return f"<AppSettings(key='{self.key}', value='{masked_value}')>"
