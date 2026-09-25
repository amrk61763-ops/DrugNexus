# -*- coding: utf-8 -*-
"""
شكل الرد (response) الخاص بـendpoint البحث بالاسم التجاري.
"""

from pydantic import BaseModel


class DrugInteraction(BaseModel):
    """صف واحد من جدول ingredient_drug_interactions - تفاعل المادة
    الفعالة دي مع دواء تاني أو مجموعة أدوية (class)."""
    interaction_type: str
    interacting_class_name: str | None
    interacting_drug_name: str | None
    interacting_drug_pubchem_cid: str | None
    severity: str | None
    mechanism_description: str | None


class IngredientSummary(BaseModel):
    """ملخص بس عن كل مادة فعالة جوه الدواء - مش كل التفاصيل (دي شغل
    active_ingredient.py المنفصل، المستخدم بيروحله لو عايز يعرف أكتر).
    بالإضافة لقائمة التفاعلات الدوائية (DDI) الخاصة بالـpubchem_cid ده
    بالظبط."""
    pubchem_cid: str
    chembl_id: str
    display_name: str
    interactions: list[DrugInteraction] = []


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
