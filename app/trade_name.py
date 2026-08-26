# -*- coding: utf-8 -*-
"""
كل حاجة متعلقة بـ"البحث بالاسم التجاري":
  - بحث جزئي، غير حساس لحالة الأحرف (مش لازم تكتب الاسم والجرعة كاملين)
  - لكل نتيجة: مواده الفعالة + بدائل (أدوية تانية بنفس المجموعة بالظبط)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Drug, DrugIngredient, Ingredient
from schemas.trade_name import AlternativeDrug, IngredientSummary, TradeNameResponse

router = APIRouter(prefix="/trade_name", tags=["trade_name"])

MAX_RESULTS = 20


def _find_exact_alternatives(
    db: Session, drug_id: int, ingredient_cids: set[str]
) -> list[AlternativeDrug]:
    """يلاقي أدوية تانية عندها بالظبط نفس مجموعة المواد الفعالة - مش بس
    مادة مشتركة واحدة. لو Augmentin فيه [Amoxicillin+Clavulanic Acid]،
    بديله الصح لازم يحتوي الاتنين بالظبط، مش Amoxicillin لوحدها.

    ملحوظة أداء: بنعمل استعلام واحد لكل "مرشح" (candidate) - مقبول تمامًا
    على حجم قاعدتنا الحالي (آلاف الصفوف، كل استعلام أقل من 1ms). لو
    القاعدة كبرت لملايين الصفوف يومًا ما، ده يستاهل يتحول لاستعلام SQL
    واحد بـGROUP BY/HAVING بدل اللوب."""

    if not ingredient_cids:
        return []

    # مرشحين أوليين: أي دواء بيشارك مادة واحدة على الأقل
    candidate_ids = db.execute(
        select(DrugIngredient.drug_id)
        .where(DrugIngredient.pubchem_cid.in_(ingredient_cids))
        .where(DrugIngredient.drug_id != drug_id)
        .distinct()
    ).scalars().all()

    exact_match_ids = []
    for cand_id in candidate_ids:
        cand_cids = set(db.execute(
            select(DrugIngredient.pubchem_cid).where(DrugIngredient.drug_id == cand_id)
        ).scalars().all())
        if cand_cids == ingredient_cids:  # مطابقة تامة للمجموعة، مش تقاطع بس
            exact_match_ids.append(cand_id)

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
    # ILIKE = بحث نصي غير حساس لحالة الأحرف في Postgres، و% حوالين
    # الكلمة = مش لازم الاسم كامل، أي جزء منه كافي
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
