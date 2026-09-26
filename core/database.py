"""Async database session and connection lifecycle management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from core.config import settings
from core.logger import logger
from core.models import Base

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for yielding an async database session in FastAPI or standalone scripts."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("db_session_rollback", error=str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Creates database tables if they do not exist."""
    async with engine.begin() as conn:
        logger.info("initializing_database_schema")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("database_schema_initialized")


async def close_db() -> None:
    """Gracefully closes database connection pool."""
    logger.info("closing_database_connections")
    await engine.dispose()
