# -*- coding: utf-8 -*-
"""
كل حاجة متعلق بـ"تفاصيل المادة الفعالة" - endpoint واحد: هات كل تفاصيل
مادة فعالة بكودها (pubchem_cid)، بالإضافة لكل الأسماء التجارية اللي
بتستخدمها.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient, IngredientDetail
from .schemas.active_ingredient import ActiveIngredientResponse, TradeNameUsingIngredient

router = APIRouter(
    prefix="/active_ingredient", tags=["active_ingredient"]
)

@router.get("/{display_name}", response_model=ActiveIngredientResponse)
def get_by_display_name(display_name: str, db: Session = Depends(get_db)):
    # 1. Search for the ingredient by display_name
    ingredient = db.execute(
        select(Ingredient).where(Ingredient.display_name == display_name)
    ).scalar_one_or_none()

    if ingredient is None:
        raise HTTPException(status_code=404, detail="المادة الفعالة دي مش موجودة")

    # 2. Extract the pubchem_cid from the found ingredient
    pubchem_cid = ingredient.pubchem_cid

    # 3. Use the pubchem_cid to get details
    details = db.execute(
        select(IngredientDetail).where(IngredientDetail.pubchem_cid == pubchem_cid)
    ).scalar_one_or_none()

    # 4. Use the pubchem_cid to find drugs using this ingredient
    used_in_drugs = db.execute(
        select(Drug)
        .join(DrugIngredient, DrugIngredient.drug_id == Drug.id)
        .where(DrugIngredient.pubchem_cid == pubchem_cid)
        .where(Drug.trade_name == display_name)
    ).scalars().all()

    return ActiveIngredientResponse(
        pubchem_cid=pubchem_cid,
        chembl_id=ingredient.chembl_id,
        display_name=ingredient.display_name,
        molecular_formula=details.molecular_formula if details else None,
        drug_indication=details.drug_indication if details else None,
        livertox_summary=details.livertox_summary if details else None,
        pharmacology=details.pharmacology if details else None,
        mesh_classification=details.mesh_classification if details else None,
        pharmacodynamics=details.pharmacodynamics if details else None,
        half_life=details.half_life if details else None,
        toxicological_info=details.toxicological_info if details else None,
        hazards_summary=details.hazards_summary if details else None,
        chembl_mechanism_of_action=details.chembl_mechanism_of_action if details else None,
        chembl_molecular_mechanism=details.chembl_molecular_mechanism if details else None,
        chembl_binding_site_comment=details.chembl_binding_site_comment if details else None,
        chembl_target_id=details.chembl_target_id if details else None,
        chembl_target_name=details.chembl_target_name if details else None,
        chembl_target_type=details.chembl_target_type if details else None,
        used_in=[
            TradeNameUsingIngredient(trade_name=d.trade_name, manufacturer=d.manufacturer)
            for d in used_in_drugs
        ],
    )
