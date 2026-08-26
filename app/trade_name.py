# -*- coding: utf-8 -*-
"""
كل حاجة متعلقة بـ"البحث بالاسم التجاري" - endpoint واحد بس دلوقتي:
هات دواء بالاسم بالظبط، ومعاه كل مواده الفعالة.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Drug, DrugIngredient, Ingredient
from schemas.trade_name import IngredientSummary, TradeNameResponse

router = APIRouter(prefix="/trade_name", tags=["trade_name"])


@router.get("/{trade_name}", response_model=TradeNameResponse)
def get_by_trade_name(trade_name: str, db: Session = Depends(get_db)):
    # الخطوة 1: هات الدواء نفسه
    drug = db.execute(
        select(Drug).where(Drug.trade_name == trade_name)
    ).scalar_one_or_none()

    if drug is None:
        raise HTTPException(status_code=404, detail="الدواء ده مش موجود في القاعدة")

    # الخطوة 2: هات كل المواد الفعالة المرتبطة بيه (JOIN صريح، مش relationship
    # مخفية - عشان يكون واضح إيه اللي بيحصل فعليًا)
    ingredients = db.execute(
        select(Ingredient)
        .join(DrugIngredient, DrugIngredient.pubchem_cid == Ingredient.pubchem_cid)
        .where(DrugIngredient.drug_id == drug.id)
    ).scalars().all()

    return TradeNameResponse(
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
    )
