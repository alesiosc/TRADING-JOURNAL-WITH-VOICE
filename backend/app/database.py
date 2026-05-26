"""
Database setup with both synchronous (fast CRUD) and async (aiosqlite) support.

Uses SQLAlchemy with SQLite as the primary database.
Async engine is available for endpoints that benefit from non-blocking IO.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings


# ---------------------------------------------------------------------------
# Synchronous engine (used by most CRUD routers)
# ---------------------------------------------------------------------------
SYNC_DATABASE_URL = settings.DATABASE_URL

# Convert sync URL to async URL for aiosqlite
# sqlite:///./trading_journal.db -> sqlite+aiosqlite:///./trading_journal.db
ASYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine = create_engine(
    SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Async engine (for long-running queries, AI calls, etc.)
# ---------------------------------------------------------------------------
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency that yields a synchronous database session.
    Used by most CRUD routers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    FastAPI dependency that yields an async database session.
    Used by endpoints that benefit from non-blocking IO (AI, imports, etc.).
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
