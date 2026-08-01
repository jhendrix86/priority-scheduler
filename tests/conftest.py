"""
Shared pytest fixtures: boots the real app against an isolated in-memory
SQLite database so every test exercises the real routers, the real
SchedulerEngine, and real SQLAlchemy models end to end.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import StaticPool

import app.database as database_module

# Swap in an isolated in-memory DB before app.main (and therefore every
# router/model module) is imported.
database_module.engine = database_module.create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
database_module.AsyncSessionLocal = database_module.async_sessionmaker(
    database_module.engine, class_=database_module.AsyncSession, expire_on_commit=False
)

from app.main import app  # noqa: E402  (must import after the engine swap above)


@pytest_asyncio.fixture
async def client():
    """A fresh database schema and a live ASGI test client for each test."""
    async with database_module.engine.begin() as conn:
        await conn.run_sync(database_module.Base.metadata.drop_all)

    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
