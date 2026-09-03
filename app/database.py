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

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# Convert to async URL if using psycopg2
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Connection pool settings for optimal performance
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,              # Number of connections to keep open
    max_overflow=40,           # Max additional connections beyond pool_size
    pool_pre_ping=True,        # Verify connections before use (handles Neon's cold starts)
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set to True for SQL debugging
    connect_args={"server_settings": {"channel_binding": "disable"}},
)

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
