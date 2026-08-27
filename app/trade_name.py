# -*- coding: utf-8 -*-
"""
كل حاجة متعلقة بـ"البحث بالاسم التجاري":
  - بحث جزئي، غير حساس لحالة الأحرف
  - لكل نتيجة: مواده الفعالة + بدائل (أدوية تانية بنفس المجموعة بالظبط)

ملحوظة أداء مهمة: _find_exact_alternatives كانت بتعمل استعلام منفصل
لكل "مرشح بديل" (N+1 pattern) - شغال بسرعة على SQLite محلي، لكن على
Neon الحقيقي كل استعلام رحلة شبكة كاملة، فلو مادة فعالة موجودة في
100 دواء، كانت بتعمل 100 رحلة شبكة بالتتابع = دقايق انتظار، وأحيانًا
Vercel بيقفل الطلب بعد 10 ثواني (خطة مجانية) فيظهر "Failed to fetch".
الحل: استعلام SQL واحد بـGROUP BY/HAVING بدل اللوب - نفس النتيجة
المنطقية بالظبط، لكن رحلتين شبكة بس مهما كان عدد المرشحين.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Drug, DrugIngredient, Ingredient
from schemas.trade_name import AlternativeDrug, IngredientSummary, TradeNameResponse

router = APIRouter(prefix="/trade_name", tags=["trade_name"])

MAX_RESULTS = 20


def _find_exact_alternatives(
    db: Session, drug_id: int, ingredient_cids: set[str]
) -> list[AlternativeDrug]:
    """يلاقي أدوية تانية عندها بالظبط نفس مجموعة المواد الفعالة -
    استعلام واحد بدل استعلام لكل مرشح."""

    if not ingredient_cids:
        return []

    target_count = len(ingredient_cids)

    # لكل دواء تاني: كام مادة من مواده بتتقاطع مع مجموعتنا المستهدفة
    matching = (
        select(
            DrugIngredient.drug_id.label("drug_id"),
            func.count().label("matching_count"),
        )
        .where(DrugIngredient.pubchem_cid.in_(ingredient_cids))
        .where(DrugIngredient.drug_id != drug_id)
        .group_by(DrugIngredient.drug_id)
        .subquery()
    )

    # إجمالي عدد مواد كل دواء (عشان نستبعد اللي عنده مواد زيادة عن
    # المطلوب - يعني تقاطع بس مش تطابق كامل)
    totals = (
        select(
            DrugIngredient.drug_id.label("drug_id"),
            func.count().label("total_count"),
        )
        .group_by(DrugIngredient.drug_id)
        .subquery()
    )

    exact_match_ids = db.execute(
        select(matching.c.drug_id)
        .join(totals, totals.c.drug_id == matching.c.drug_id)
        .where(matching.c.matching_count == target_count)
        .where(totals.c.total_count == target_count)
    ).scalars().all()

    if not exact_match_ids:
        return []

    alt_drugs = db.execute(
        select(Drug).where(Drug.id.in_(exact_match_ids))
    ).scalars().all()

    return [
        AlternativeDrug(trade_name=d.trade_name, manufacturer=d.manufacturer)
        for d in alt_drugs
    ]


@router.get("/{trade_name}", response_model=list[TradeNameResponse])
def search_by_trade_name(trade_name: str, db: Session = Depends(get_db)):
    drugs = db.execute(
        select(Drug)
        .where(Drug.trade_name.ilike(f"%{trade_name}%"))
        .limit(MAX_RESULTS)
    ).scalars().all()

    results = []
    for drug in drugs:
        ingredients = db.execute(
            select(Ingredient)
            .join(DrugIngredient, DrugIngredient.pubchem_cid == Ingredient.pubchem_cid)
            .where(DrugIngredient.drug_id == drug.id)
        ).scalars().all()

        ingredient_cids = {i.pubchem_cid for i in ingredients}
        alternatives = _find_exact_alternatives(db, drug.id, ingredient_cids)

        results.append(TradeNameResponse(
            trade_name=drug.trade_name,
            manufacturer=drug.manufacturer,
            drug_class=drug.drug_class,
            active_ingredients=[
                IngredientSummary(
                    pubchem_cid=i.pubchem_cid,
                    chembl_id=i.chembl_id,
                    display_name=i.display_name,
                )
                for i in ingredients
            ],
            alternatives=alternatives,
        ))

    return results
