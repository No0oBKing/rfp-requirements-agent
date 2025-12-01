from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Convert sync URL to async
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_database_url, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Schema is managed by Alembic; no runtime DDL here."""
    return

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
