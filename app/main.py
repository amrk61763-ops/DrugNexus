# -*- coding: utf-8 -*-
"""
نقطة الدخول - بتجمع الـrouters كلهم مع بعض. شغّله محليًا بـ:
    uvicorn main:app --reload

بعدين افتح http://127.0.0.1:8000/docs عشان تجرب الـendpoints من واجهة
تفاعلية جاهزة.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import active_ingredient, trade_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async lifespan manager for startup/shutdown events"""
    # Startup: dispose of any connections if needed
    yield
    # Shutdown: dispose of the database engine
    await engine.dispose()


app = FastAPI(
    title="DrugNexus API",
    description="Professional async API for drug information lookup",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: بيسمح للفرونت اند (على دومين مختلف زي Cloudflare Pages مثلاً)
# إنه يكلم الـAPI ده. من غيره، المتصفح بيرفض الرد حتى لو السيرفر
# نفسه اشتغل صح، وده بيظهر للمستخدم كـ"Failed to fetch".
#
# دلوقتي متفتوح لأي دومين (allow_origins=["*"]) عشان تشتغل بسرعة -
# لما يبقى عندك دومين نهائي للفرونت اند، غيّرها لـ:
#   allow_origins=["https://your-frontend-domain.com"]
# عشان الأمان (مش أي موقع في الدنيا يقدر يستدعي الـAPI بتاعك).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(trade_name.router)
app.include_router(active_ingredient.router)


@app.get("/")
async def root():
    return {"status": "شغال", "docs": "/docs"}
