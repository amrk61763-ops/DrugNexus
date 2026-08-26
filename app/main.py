# -*- coding: utf-8 -*-
"""
نقطة الدخول - بتجمع الـrouters كلهم مع بعض. شغّله بـ:
    uvicorn main:app --reload

بعدين افتح http://127.0.0.1:8000/docs عشان تجرب الـendpoints من واجهة
تفاعلية جاهزة (FastAPI بيبنيها لوحده من الـPydantic models).
"""

from fastapi import FastAPI

import active_ingredient, trade_name

app = FastAPI(title="DrugNexus API")

app.include_router(trade_name.router)
app.include_router(active_ingredient.router)


@app.get("/")
def root():
    return {"status": "شغال", "docs": "/docs"}
