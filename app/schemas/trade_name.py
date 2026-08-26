# -*- coding: utf-8 -*-
"""
شكل الرد (response) الخاص بـendpoint البحث بالاسم التجاري.
"""

from pydantic import BaseModel


class IngredientSummary(BaseModel):
    """ملخص بس عن كل مادة فعالة جوه الدواء - مش كل التفاصيل (دي شغل
    active_ingredient.py المنفصل، المستخدم بيروحله لو عايز يعرف أكتر)."""
    pubchem_cid: str
    chembl_id: str
    display_name: str


class TradeNameResponse(BaseModel):
    trade_name: str
    manufacturer: str
    drug_class: str
    active_ingredients: list[IngredientSummary]
