from collections.abc import AsyncGenerator
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from app.config import settings

# NullPool: open a fresh connection per request, close it immediately after.
# Required for serverless environments (Vercel) where connection pools are not
# kept alive between function invocations. Also recommended by Neon for serverless.
engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
