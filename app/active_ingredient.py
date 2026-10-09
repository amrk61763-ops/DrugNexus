# -*- coding: utf-8 -*-
"""
كل حاجة متعلقة بـ"تفاصيل المادة الفعالة":
  - /active_ingredient/search?q=   اقتراحات خفيفة أثناء الكتابة (أسماء فقط)
  - /active_ingredient/{name}      كل التفاصيل + الأسماء التجارية + الـPDB structures
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import (
    Drug,
    DrugIngredient,
    Ingredient,
    IngredientDetail,
    PdbReceptor,
)
from .schemas.active_ingredient import (
    ActiveIngredientResponse,
    DrugInteraction,
    IngredientSearchResult,
    ReceptorStructure,
    TradeNameUsingIngredient,
)

router = APIRouter(
    prefix="/active_ingredient",
    tags=["Active Ingredient"],
)


def _to_int(val):
    try:
        if val is None:
            return None
        return int(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Lightweight live-suggestion endpoint - MUST be defined before "/{display_name}"
# ---------------------------------------------------------------------------
@router.get("/search", response_model=list[IngredientSearchResult])
async def search_suggest(q: str, db: AsyncSession = Depends(get_db)):
    """اقتراحات خفيفة أثناء الكتابة - الاسم والصيغة الجزيئية فقط، عشان
    تستجيب فورًا. بيحتاج حرفين على الأقل."""
    q = (q or "").strip()
    if len(q) < 2:
        return []
    result = await db.execute(
        select(
            Ingredient.pubchem_cid,
            Ingredient.display_name,
            IngredientDetail.molecular_formula,
        )
        .outerjoin(IngredientDetail, IngredientDetail.pubchem_cid == Ingredient.pubchem_cid)
        .where(Ingredient.display_name.ilike(f"%{q}%"))
        .order_by(Ingredient.display_name)
        .limit(8)
    )
    return [
        IngredientSearchResult(
            display_name=row.display_name,
            pubchem_cid=row.pubchem_cid,
            molecular_formula=row.molecular_formula,
        )
        for row in result.all()
    ]


async def _fetch_interactions(db: AsyncSession, cids: list[str]) -> dict[str, list[DrugInteraction]]:
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


@router.get("/{display_name}", response_model=ActiveIngredientResponse)
async def get_by_display_name(display_name: str, db: AsyncSession = Depends(get_db)):
    # 1. Search for the ingredient by display_name (partial, case-insensitive)
    result = await db.execute(
        select(Ingredient).where(Ingredient.display_name.ilike(f"%{display_name}%"))
    )
    ingredient = result.scalars().first()

    if ingredient is None:
        raise HTTPException(status_code=404, detail="المادة الفعالة دي مش موجودة")

    # 2. Extract the pubchem_cid from the found ingredient
    pubchem_cid = ingredient.pubchem_cid

    # 3. Use the pubchem_cid to get details
    result = await db.execute(
        select(IngredientDetail).where(IngredientDetail.pubchem_cid == pubchem_cid)
    )
    details = result.scalar_one_or_none()

    # 4. Fetch ALL drugs containing this ingredient
    result = await db.execute(
        select(Drug)
        .join(DrugIngredient, DrugIngredient.drug_id == Drug.id)
        .where(DrugIngredient.pubchem_cid == pubchem_cid)
    )
    all_drugs = result.scalars().all()

    # 4.5. التفاعلات الدوائية المسجلة ضد المادة دي
    ix_by_cid = await _fetch_interactions(db, [pubchem_cid])

    # 5. هات كل الـreceptors المرتبطة بالمادة الفعالة دي
    # pubchem_cid في pdb_receptors عمود jsonb - أحيانًا رقم مفرد وأحيانًا
    # array من أرقام. .contains() العادي بيبعت الرقم كـINTEGER من غير ما
    # يحوّله لـjsonb (وده كان بيرمي jsonb @> integer)، فبنستخدم دالة
    # to_jsonb() الصريحة من بوستجرس عشان نضمن الكاست الصح.
    cid_int = _to_int(pubchem_cid)
    receptors = []
    if cid_int is not None:
        result = await db.execute(
            select(PdbReceptor).where(
                PdbReceptor.pubchem_cid.op("@>", is_comparison=True)(func.to_jsonb(cid_int))
            )
        )
        receptors = result.scalars().all()

    pdb_structures: list[ReceptorStructure] = []

    if receptors:
        pdb_structures = [
            ReceptorStructure(
                pdb_id=r.pdb_id,
                receptor_file_name=r.receptor_file_name,
                resolution=str(getattr(r, "resolution")) if getattr(r, "resolution", None) is not None else None,
                experiment_method=getattr(r, "experiment_method", None),
                download_url=getattr(r, "receptor_blob_url", None),
            )
            for r in receptors
        ]

    # 6. Process drugs to extract the base name (prefix) and remove duplicates
    # Example: "Augmentin 1g" -> "Augmentin", "Augmentin 360ml" -> "Augmentin"
    unique_drugs_map = {}

    for drug in all_drugs:
        trade_name = drug.trade_name
        if not trade_name:
            continue

        # Split by space to get the first word (the base name/prefix)
        base_name = trade_name.split()[0]

        # Only add if we haven't seen this base name yet
        if base_name not in unique_drugs_map:
            unique_drugs_map[base_name] = {
                "trade_name": base_name,
                "manufacturer": drug.manufacturer
            }

    # Convert the map back to a list of objects for the response
    used_in_list = [
        TradeNameUsingIngredient(
            trade_name=data["trade_name"],
            manufacturer=data["manufacturer"]
        )
        for data in unique_drugs_map.values()
    ]

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
        used_in=used_in_list,
        interactions=ix_by_cid.get(pubchem_cid, []),
        pdb_structures=pdb_structures,
    )
