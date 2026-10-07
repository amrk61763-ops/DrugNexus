# -*- coding: utf-8 -*-
"""
البحث بالاسم التجاري.

ملاحظة أداء مهمة: النسخة القديمة كانت بتعمل 3 كويريز منفصلة لكل دواء
(ingredients + alternatives + interactions) - يعني صفحة نتائج فيها 20 دواء
= +60 كويري، وده اللي كان بيخلي الاقتراحات اللحظية "بطيئة". هنا كل حاجة
بتتجمع في Batch واحد لكل مجموعة نتائج:
  - _batch_ingredients   : كل المواد الفعالة لكل الأدوية في كويري واحد
  - _batch_interactions  : كل التفاعلات لكل الـ cids في كويري واحد
  - _batch_alternatives  : كل البدائل في كويري واحد (array مقارنة في بايثون)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient
from .schemas.trade_name import (
    AlternativeDrug,
    DrugInteraction,
    IngredientSummary,
    TradeNameResponse,
    TradeNameSearchResult,
)

router = APIRouter(
    prefix="/trade_name",
    tags=["Trade Name"],
)


# ---------------------------------------------------------------------------
# Lightweight live-suggestion endpoint - MUST be defined before "/{trade_name}"
# ---------------------------------------------------------------------------
@router.get("/search", response_model=list[TradeNameSearchResult])
async def search_suggest(q: str, db: AsyncSession = Depends(get_db)):
    """
    اقتراحات خفيفة أثناء الكتابة - بيرجع أسماء فقط (من غير ingredients ولا
    alternatives) عشان تستجيب فورًا. بيحتاج حرفين على الأقل.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return []
    result = await db.execute(
        select(Drug.trade_name, Drug.manufacturer)
        .where(Drug.trade_name.ilike(f"%{q}%"))
        .order_by(Drug.trade_name)
        .limit(10)
    )
    return [
        TradeNameSearchResult(trade_name=row.trade_name, manufacturer=row.manufacturer)
        for row in result.all()
    ]


# ---------------------------------------------------------------------------
# Batched helpers
# ---------------------------------------------------------------------------
async def _batch_ingredients(db: AsyncSession, drug_ids: list[int]):
    """كل مواد كل الأدوية في كويري واحد. بيرجع (خريطة drug_id -> ingredients،
    وقائمة الـ pubchem_cids الفريدة مرتبة)."""
    if not drug_ids:
        return {}, []
    result = await db.execute(
        select(DrugIngredient.drug_id, Ingredient)
        .join(Ingredient, Ingredient.pubchem_cid == DrugIngredient.pubchem_cid)
        .where(DrugIngredient.drug_id.in_(drug_ids))
        .order_by(Ingredient.pubchem_cid)
    )
    by_drug: dict[int, list[Ingredient]] = {i: [] for i in drug_ids}
    cids: set[str] = set()
    for drug_id, ingredient in result.all():
        by_drug[drug_id].append(ingredient)
        cids.add(ingredient.pubchem_cid)
    return by_drug, sorted(cids)


async def _batch_interactions(db: AsyncSession, cids: list[str]) -> dict[str, list[DrugInteraction]]:
    """كل التفاعلات الدوائية لقائمة cids في كويري واحد.

    ملاحظة: عمود المادة الفعالة في جدول ingredient_drug_interactions اسمه
    ingredient_pubchem_cid مش pubchem_cid (ده كان سبب الخطأ
    "column pubchem_cid does not exist") - بنعمل alias بـAS pubchem_cid
    عشان الكود اللي بيقرا row["pubchem_cid"] تحت يفضل شغال من غير تعديل.
    """
    if not cids:
        return {}
    result = await db.execute(
        text(
            """
            SELECT ingredient_pubchem_cid::text AS pubchem_cid,
                   interaction_type,
                   interacting_class_name,
                   interacting_drug_name,
                   interacting_drug_pubchem_cid::text AS interacting_drug_pubchem_cid,
                   severity,
                   mechanism_description
            FROM ingredient_drug_interactions
            WHERE ingredient_pubchem_cid::text = ANY(:cids)
            """
        ),
        {"cids": cids},
    )
    by_cid: dict[str, list[DrugInteraction]] = {}
    for row in result.mappings().all():
        by_cid.setdefault(row["pubchem_cid"], []).append(
            DrugInteraction(
                interaction_type=row["interaction_type"],
                interacting_class_name=row["interacting_class_name"],
                interacting_drug_name=row["interacting_drug_name"],
                interacting_drug_pubchem_cid=row["interacting_drug_pubchem_cid"],
                severity=row["severity"],
                mechanism_description=row["mechanism_description"],
            )
        )
    return by_cid


async def _batch_alternatives(db: AsyncSession, drug_ids: list[int]) -> dict[int, list[AlternativeDrug]]:
    """بدائل كل الأدوية في كويري واحد: بنجيب كل الأدوية اللي عندها مادة مشتركة
    مع أي دواء من القائمة (مرشحين)، وبنجيب مجموعة كل دواء target، وبعدين
    بنقارن المصفوفتين في بايثون."""
    if not drug_ids:
        return {i: [] for i in drug_ids}

    candidates = await db.execute(
        text(
            """
            SELECT d.id AS drug_id, d.trade_name, d.manufacturer,
                   array_agg(di.pubchem_cid ORDER BY di.pubchem_cid) AS cids
            FROM drugs d
            JOIN drug_ingredients di ON di.drug_id = d.id
            WHERE di.pubchem_cid IN (SELECT pubchem_cid FROM drug_ingredients WHERE drug_id = ANY(:ids))
            GROUP BY d.id, d.trade_name, d.manufacturer
            """
        ),
        {"ids": drug_ids},
    )

    targets = await db.execute(
        text(
            """
            SELECT drug_id, array_agg(pubchem_cid ORDER BY pubchem_cid) AS cids
            FROM drug_ingredients
            WHERE drug_id = ANY(:ids)
            GROUP BY drug_id
            """
        ),
        {"ids": drug_ids},
    )
    target_map = {row.drug_id: list(row.cids) for row in targets.all()}

    by_drug: dict[int, list[AlternativeDrug]] = {i: [] for i in drug_ids}
    for row in candidates.mappings().all():
        cand_id = row["drug_id"]
        for drug_id, target_cids in target_map.items():
            if cand_id == drug_id:
                continue
            if list(row["cids"]) == target_cids:
                by_drug[drug_id].append(
                    AlternativeDrug(id=row["drug_id"], trade_name=row["trade_name"], manufacturer=row["manufacturer"])
                )
    return by_drug


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------
@router.get("/{trade_name}", response_model=list[TradeNameResponse])
async def search_by_trade_name(
    trade_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for drugs by trade name (partial, case-insensitive match).

    Example:
    GET /trade_name/panadol
    """

    if not trade_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Trade name cannot be empty",
        )

    try:
        result = await db.execute(
            select(Drug)
            .where(Drug.trade_name.ilike(f"%{trade_name.strip()}%"))
            .order_by(Drug.trade_name)
            .limit(20)
        )
        drugs = result.scalars().all()

        if not drugs:
            return []

        drug_ids = [d.id for d in drugs]

        # كل البيانات الإضافية في 3 كويريز batched بدل 3×N
        ing_by_drug, cids = await _batch_ingredients(db, drug_ids)
        ix_by_cid = await _batch_interactions(db, cids)
        alt_by_drug = await _batch_alternatives(db, drug_ids)

        responses = []
        for drug in drugs:
            ingredients = [
                IngredientSummary(
                    pubchem_cid=ing.pubchem_cid,
                    chembl_id=ing.chembl_id,
                    display_name=ing.display_name,
                    interactions=ix_by_cid.get(ing.pubchem_cid, []),
                )
                for ing in ing_by_drug[drug.id]
            ]
            responses.append(
                TradeNameResponse(
                    id=drug.id,
                    trade_name=drug.trade_name,
                    manufacturer=drug.manufacturer,
                    drug_class=drug.drug_class,
                    active_ingredients=ingredients,
                    alternatives=alt_by_drug[drug.id],
                )
            )

        return responses

    except HTTPException:
        raise
    except Exception as error:
        print(f"Trade name search error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search for the trade name",
        )
