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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base بس عشان الموديلز تعرف توصف الجداول الموجودة - مش بنستخدمها لعمل
# create_all() في أي مكان، لأن الجداول موجودة بالفعل جوه Neon
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
