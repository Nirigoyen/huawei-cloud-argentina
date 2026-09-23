"""Async SQLAlchemy database engine and session management.

Provides:
- Async engine for the main application database
- Async session factory for CRUD operations
- get_db dependency for FastAPI route injection
- init_db function for application startup
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# Module-level engine and session factory (initialized lazily)
_engine = None
_async_session_factory = None


def _get_engine():
    """Get or create the async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine


def _get_session_factory():
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Automatically handles commit/rollback/close based on exception state.

    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_chatbot_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read-only chatbot database session.

    Uses a separate connection configured for the chatbot_readonly user
    with statement_timeout set to prevent long-running queries.
    """
    settings = get_settings()
    chatbot_engine = create_async_engine(
        settings.chatbot_database_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    chatbot_session_factory = async_sessionmaker(
        chatbot_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with chatbot_session_factory() as session:
        try:
            # Set statement timeout for chatbot queries (5 seconds)
            timeout = settings.chatbot_query_timeout_seconds
            await session.execute(__import__("sqlalchemy").text(f"SET statement_timeout = '{timeout}s'"))
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await chatbot_engine.dispose()


async def init_db() -> None:
    """Initialize the database connection.

    Called during application startup to verify connectivity
    and warm up the connection pool.
    """
    engine = _get_engine()
    async with engine.connect() as conn:
        # Simple connectivity check
        from sqlalchemy import text

        await conn.execute(text("SELECT 1"))
    # Dispose to release the test connection
    # The pool will create new connections as needed


async def close_db() -> None:
    """Close the database engine and dispose of all connections.

    Called during application shutdown.
    """
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
