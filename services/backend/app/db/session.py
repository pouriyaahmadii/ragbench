from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import Settings

def create_engine(settings: Settings):
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.LOG_LEVEL == "DEBUG",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

def create_session_factory(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

# Global instances (initialized in main.py lifespan)
engine = None
async_session_maker = None

async def init_db(settings: Settings):
    global engine, async_session_maker
    engine = create_engine(settings)
    async_session_maker = create_session_factory(engine)

async def close_db():
    global engine
    if engine:
        await engine.dispose()

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session