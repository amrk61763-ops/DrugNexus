import os
import ssl
from dotenv import load_dotenv
from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing. "
        "Add it in Vercel Project Settings."
    )

url = make_url(DATABASE_URL)

if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+asyncpg")

# asyncpg does not accept these libpq parameters directly — SSL is instead
# enforced explicitly below via connect_args, with full certificate
# verification against the system's trusted CA bundle.
url = url.difference_update_query(
    ["sslmode", "channel_binding"]
)

ASYNC_DATABASE_URL = url.render_as_string(hide_password=False)

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=2,
    max_overflow=3,
    echo=False,
    connect_args={"ssl": ssl_context},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
