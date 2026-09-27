# -*- coding: utf-8 -*-
"""
شكل الرد (response) الخاص بـendpoint البحث بالاسم التجاري.
"""

from pydantic import BaseModel, Field


class DrugInteraction(BaseModel):
    """تفاعل دوائي واحد مسجل ضد مادة فعالة - نفس أعمدة جدول
    ingredient_drug_interactions في قاعدة البيانات."""
    interaction_type: str | None = None
    interacting_class_name: str | None = None
    interacting_drug_name: str | None = None
    interacting_drug_pubchem_cid: str | None = None
    severity: str | None = None
    mechanism_description: str | None = None


class IngredientSummary(BaseModel):
    """ملخص بس عن كل مادة فعالة جوه الدواء - مش كل التفاصيل (دي شغل
    active_ingredient.py المنفصل، المستخدم بيروحله لو عايز يعرف أكتر) -
    بالإضافة لكل التفاعلات الدوائية المسجلة ضد المادة دي."""
    pubchem_cid: str
    chembl_id: str | None
    display_name: str
    interactions: list[DrugInteraction] = Field(default_factory=list)


class AlternativeDrug(BaseModel):
    """دواء تاني عنده بالظبط نفس مجموعة المواد الفعالة (مش بس مادة
    مشتركة واحدة)."""
    trade_name: str
    manufacturer: str


class TradeNameResponse(BaseModel):
    trade_name: str
    manufacturer: str
    drug_class: str
    active_ingredients: list[IngredientSummary]
    alternatives: list[AlternativeDrug]


class TradeNameSearchResult(BaseModel):
    """نتيجة خفيفة لاقتراحات البحث اللحظية - من غير ingredients ولا
    alternatives عشان تكون سريعة جدًا."""
    trade_name: str
    manufacturer: str
