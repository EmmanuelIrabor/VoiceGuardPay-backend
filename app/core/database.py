

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.APP_DATABASE_URL,
    echo=False,
    pool_pre_ping=True, 
    pool_size=5,
    max_overflow=0,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class all SQLAlchemy models inherit from."""
    pass


async def get_db():
    """FastAPI dependency — yields a DB session, closes it after the request."""
    async with AsyncSessionLocal() as session:
        yield session
