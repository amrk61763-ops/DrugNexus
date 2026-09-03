# -*- coding: utf-8 -*-
"""
اتصال قاعدة البيانات (Neon PostgreSQL). ده الملف الوحيد اللي فيه تفاصيل
الاتصال - أي ملف تاني محتاج القاعدة بيستورد get_db من هنا بس.

معلومات الاتصال بتيجي من متغير بيئة DATABASE_URL - مش مكتوبة هنا مباشرة
(عشان متحطش كلمة السر في الكود اللي هيتـرفع على GitHub).

قبل التشغيل:
    pip install sqlalchemy[asyncio] asyncpg python-dotenv

اعمل ملف .env في نفس الفولدر (وحطه في .gitignore عشان مايترفعش):
    DATABASE_URL=postgresql://user:password@host/dbname
"""

import os

from dotenv import load_dotenv
from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# ------------------------------------------------------------------
# Neon connection URL -> SQLAlchemy asyncpg URL
# ------------------------------------------------------------------
# Neon/libpq connection strings can contain parameters such as
# `sslmode=require` and `channel_binding=require`. Those are libpq-style
# connection options and must not be passed through to asyncpg.connect()
# as keyword arguments.
#
# SQLAlchemy's asyncpg dialect is used below, so remove only those
# unsupported URL parameters and preserve the rest of the connection URL.
url = make_url(DATABASE_URL)

if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+asyncpg")

url = url.difference_update_query(
    ["channel_binding", "sslmode"]
)

ASYNC_DATABASE_URL = url.render_as_string(hide_password=False)

# ------------------------------------------------------------------
# Async engine
# ------------------------------------------------------------------
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base بس عشان الموديلز تعرف توصف الجداول الموجودة - مش بنستخدمها لعمل
# create_all() في أي مكان، لأن الجداول موجودة بالفعل جوه Neon
Base = declarative_base()


async def get_db():
    """Async dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
