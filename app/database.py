# -*- coding: utf-8 -*-
"""
اتصال قاعدة البيانات (Neon PostgreSQL). ده الملف الوحيد اللي فيه تفاصيل
الاتصال - أي ملف تاني محتاج القاعدة بيستورد get_db من هنا بس.

معلومات الاتصال بتيجي من متغير بيئة DATABASE_URL - مش مكتوبة هنا مباشرة
(عشان متحطش كلمة السر في الكود اللي هيترفع على GitHub).

قبل التشغيل:
    pip install sqlalchemy psycopg2-binary python-dotenv

اعمل ملف .env في نفس الفولدر (وحطه في .gitignore عشان مايترفعش):
    DATABASE_URL=postgresql://user:password@host/dbname
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Optional runtime introspection
import inspect

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# Convert to async URL if using asyncpg
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# defensive hotfix: strip unexpected 'channel_binding' kwarg before asyncpg.connect runs
try:
    import asyncpg
    _asyncpg_connect_orig = asyncpg.connect

    async def _asyncpg_connect_wrapper(*args, **kwargs):
        # remove whatever is causing the TypeError if present
        kwargs.pop("channel_binding", None)
        # some callers might accidentally pass server_settings flattened; try to protect against that too
        if "server_settings" in kwargs and isinstance(kwargs["server_settings"], dict):
            # make sure we don't pass unexpected nested items as top-level kwargs
            kwargs["server_settings"] = {
                k: v for k, v in kwargs["server_settings"].items()
                if k != "channel_binding"
            }
        return await _asyncpg_connect_orig(*args, **kwargs)

    asyncpg.connect = _asyncpg_connect_wrapper
except Exception:
    # if asyncpg isn't importable at startup (rare), skip the hotfix
    pass

# Build connect_args conditionally so we don't pass unsupported kwargs to asyncpg.connect
connect_args = {}
try:
    # Import asyncpg only if available in the runtime. If it's not present,
    # we keep connect_args empty to avoid import-time failures in environments
    # that don't have asyncpg installed (some test or build environments).
    import asyncpg

    sig = inspect.signature(asyncpg.connect)
    # asyncpg.connect accepts server_settings in some versions; only add it when supported
    if "server_settings" in sig.parameters:
        connect_args = {"server_settings": {"channel_binding": "disable"}}
except Exception:
    # If anything goes wrong (module missing or signature unexpected), don't pass connect args
    connect_args = {}

# Connection pool settings for optimal performance
engine_kwargs = dict(
    pool_size=20,              # Number of connections to keep open
    max_overflow=40,           # Max additional connections beyond pool_size
    pool_pre_ping=True,        # Verify connections before use (handles Neon's cold starts)
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set to True for SQL debugging
)

# Only include connect_args if non-empty
if connect_args:
    engine = create_async_engine(ASYNC_DATABASE_URL, **engine_kwargs, connect_args=connect_args)
else:
    engine = create_async_engine(ASYNC_DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base بس عشان الموديلز تعرف توصف الجداول الموجودة - مش بنستخدمها لعمل
# create_all() في أي مكان، لأن الجداول موجودة بالفعل جوه Neon
Base = declarative_base()


async def get_db():
    """Async dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
