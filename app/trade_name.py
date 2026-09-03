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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient
from .schemas.trade_name import AlternativeDrug, IngredientSummary, TradeNameResponse

@router.get("/{trade_name}", response_model=list[TradeNameResponse])
async def search_by_trade_name(
    trade_name: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(Drug)
            .where(Drug.trade_name.ilike(f"%{trade_name}%"))
            .limit(MAX_RESULTS)
        )

        drugs = result.scalars().all()
        results = []

        for drug in drugs:
            result = await db.execute(
                select(Ingredient)
                .join(
                    DrugIngredient,
                    DrugIngredient.pubchem_cid == Ingredient.pubchem_cid,
                )
                .where(DrugIngredient.drug_id == drug.id)
            )

            ingredients = result.scalars().all()
            ingredient_cids = {i.pubchem_cid for i in ingredients}

            alternatives = await _find_exact_alternatives(
                db,
                drug.id,
                ingredient_cids,
            )

            results.append(
                TradeNameResponse(
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
                )
            )

        return results

    except Exception as error:
        print(f"trade_name API error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Database request failed",
        )

