"""
Database configuration and initialization
"""

import asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    # Validate a pooled connection before handing it out - Postgres briefly
    # stalls under the post-reboot I/O storm (see wait_for_database below),
    # and a long-lived pool can otherwise hand back a connection that went
    # stale during that window.
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def _check_database_connection() -> None:
    """Open a throwaway connection and run ``SELECT 1``. Raises on failure.

    Factored out so ``wait_for_database`` has a single seam to exercise
    (and for tests to substitute).
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def wait_for_database(
    max_attempts: int = 30,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> None:
    """Block until the database accepts a connection, or raise.

    On the deployment target (~27 containers cold-starting together on an
    HDD-backed host after a reboot), Postgres is regularly not ready for
    tens of seconds to minutes while it does crash-recovery fsync. Without
    this gate, init_db()'s first query raises, the container exits, and
    Docker's ``restart: unless-stopped`` just crash-loops against the same
    closed window - adding I/O/CPU load that slows Postgres's own recovery
    further. See HANDOFF.md's BA-13 entries and baselayer's identical fix
    (commit 8bf204d) for the fleet-wide history of this failure.

    Retries with capped exponential backoff. With the defaults the
    worst-case total wait is ~4.5 min (1+2+4+8, then 10s flat), comfortably
    longer than any observed storm; after that it gives up so a genuinely
    misconfigured DATABASE_URL still fails loudly instead of hanging
    forever.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await _check_database_connection()
            if attempt > 1:
                logger.info(f"Database ready after {attempt} attempts")
            return
        except Exception as exc:  # noqa: BLE001 - any connect failure is retryable here
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                f"Database not ready (attempt {attempt}/{max_attempts}), "
                f"retrying in {delay:.1f}s: {exc}"
            )
            await asyncio.sleep(delay)

    raise RuntimeError(f"database not reachable after {max_attempts} attempts") from last_exc


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered
            from app.models import task, job, queue, worker
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
