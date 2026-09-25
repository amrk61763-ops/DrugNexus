# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient, IngredientDrugInteraction
from .schemas.trade_name import (
    AlternativeDrug,
    DrugInteraction,
    IngredientSummary,
    TradeNameResponse,
)


router = APIRouter(
    prefix="/trade_name",
    tags=["Trade Name"],
)


async def _get_active_ingredients(db: AsyncSession, drug_id: int) -> list[IngredientSummary]:
    result = await db.execute(
        select(Ingredient)
        .join(DrugIngredient, DrugIngredient.pubchem_cid == Ingredient.pubchem_cid)
        .where(DrugIngredient.drug_id == drug_id)
        .order_by(Ingredient.pubchem_cid)
    )
    ingredients = result.scalars().all()

    if not ingredients:
        return []

    # استعلام واحد لكل الـDDI بتاعة كل المواد الفعالة في الدواء ده مع
    # بعض (بدل استعلام منفصل لكل مادة فعالة - نفس فلسفة active_ingredient.py
    # مع الـligands)
    cids = [ing.pubchem_cid for ing in ingredients]
    result = await db.execute(
        select(IngredientDrugInteraction)
        .where(IngredientDrugInteraction.ingredient_pubchem_cid.in_(cids))
        .order_by(IngredientDrugInteraction.id)
    )
    interactions_by_cid: dict[str, list[IngredientDrugInteraction]] = {}
    for row in result.scalars().all():
        interactions_by_cid.setdefault(row.ingredient_pubchem_cid, []).append(row)

    return [
        IngredientSummary(
            pubchem_cid=ing.pubchem_cid,
            chembl_id=ing.chembl_id,
            display_name=ing.display_name,
            interactions=[
                DrugInteraction(
                    interaction_type=ddi.interaction_type,
                    interacting_class_name=ddi.interacting_class_name,
                    interacting_drug_name=ddi.interacting_drug_name,
                    interacting_drug_pubchem_cid=ddi.interacting_drug_pubchem_cid,
                    severity=ddi.severity,
                    mechanism_description=ddi.mechanism_description,
                )
                for ddi in interactions_by_cid.get(ing.pubchem_cid, [])
            ],
        )
        for ing in ingredients
    ]


async def _get_alternatives(db: AsyncSession, drug_id: int) -> list[AlternativeDrug]:
    """أدوية تانية عندها *بالظبط* نفس مجموعة المواد الفعالة (مش بس مادة
    مشتركة واحدة) - بنقارن المجموعتين كاملين مرة واحدة في الداتابيز
    باستخدام array_agg + HAVING بدل ما نلف على كل دواء بكويري منفصل."""
    result = await db.execute(
        text(
            """
            WITH target AS (
                SELECT array_agg(pubchem_cid ORDER BY pubchem_cid) AS cids
                FROM drug_ingredients
                WHERE drug_id = :drug_id
            )
            SELECT d.trade_name, d.manufacturer
            FROM drugs d
            JOIN drug_ingredients di ON di.drug_id = d.id
            WHERE d.id != :drug_id
            GROUP BY d.id, d.trade_name, d.manufacturer
            HAVING array_agg(di.pubchem_cid ORDER BY di.pubchem_cid) = (SELECT cids FROM target)
            """
        ),
        {"drug_id": drug_id},
    )
    return [
        AlternativeDrug(trade_name=row.trade_name, manufacturer=row.manufacturer)
        for row in result.mappings().all()
    ]


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
        query = (
            select(Drug)
            .where(Drug.trade_name.ilike(f"%{trade_name.strip()}%"))
            .order_by(Drug.trade_name)
            .limit(20)
        )
        result = await db.execute(query)
        drugs = result.scalars().all()

        responses = []
        for drug in drugs:
            active_ingredients = await _get_active_ingredients(db, drug.id)
            alternatives = await _get_alternatives(db, drug.id)

            responses.append(
                TradeNameResponse(
                    trade_name=drug.trade_name,
                    manufacturer=drug.manufacturer,
                    drug_class=drug.drug_class,
                    active_ingredients=active_ingredients,
                    alternatives=alternatives,
                )
            )

        return responses

    except Exception as error:
        print(f"Trade name search error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to search for the trade name",
        )
