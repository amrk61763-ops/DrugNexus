# -*- coding: utf-8 -*-
"""
كل حاجة متعلقة بـ"تفاصيل المادة الفعالة" - endpoint واحد: هات كل تفاصيل
مادة فعالة بكودها (pubchem_cid)، بالإضافة لكل الأسماء التجارية اللي
بتستخدمها.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient, IngredientDetail, PdbLigand, PdbReceptor
from .schemas.active_ingredient import (
    ActiveIngredientResponse,
    LigandFile,
    ReceptorStructure,
    TradeNameUsingIngredient,
)

router = APIRouter(
    prefix="/active_ingredient", tags=["active_ingredient"]
)


def _to_int(val):
    try:
        if val is None:
            return None
        return int(val)
    except (TypeError, ValueError):
        return None


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

    # 4.5. هات كل الـreceptors المرتبطة بالمادة الفعالة دي
    result = await db.execute(
        select(PdbReceptor).where(PdbReceptor.pubchem_cid == pubchem_cid)
    )
    receptors = result.scalars().all()

    pdb_structures: list[ReceptorStructure] = []

    if receptors:
        receptor_pdb_ids = [r.pdb_id for r in receptors]

        # استعلام واحد لكل الـligands بتوع كل الـreceptors مع بعض
        # (بدل استعلام منفصل لكل receptor - نفس فلسفة trade_name.py)
        result = await db.execute(
            select(PdbLigand).where(PdbLigand.pdb_id.in_(receptor_pdb_ids))
        )
        all_ligands = result.scalars().all()

        ligands_by_pdb_id: dict[str, list[PdbLigand]] = {}
        for lig in all_ligands:
            ligands_by_pdb_id.setdefault(lig.pdb_id, []).append(lig)

    pdb_structures = [
        ReceptorStructure(
            pdb_id=r.pdb_id,
            receptor_file_name=r.receptor_file_name,
            resolution=str(getattr(r, "resolution")) if getattr(r, "resolution", None) is not None else None,
            experiment_method=getattr(r, "experiment_method", None),
            download_url=getattr(r, "receptor_blob_url", None),
            ligands=[
                LigandFile(
                    ligand_file_name=l.ligand_file_name,
                    resolution=str(getattr(l, "resolution")) if getattr(l, "resolution", None) is not None else None,
                    rsr=_to_int(getattr(l, "rsr", None)),
                    rscc=_to_int(getattr(l, "rscc", None)),
                    atom_count=_to_int(getattr(l, "atom_count", None)),
                    download_url=getattr(l, "ligand_blob_url", None),
                )
                for l in ligands_by_pdb_id.get(r.pdb_id, [])
            ],
        )
        for r in receptors
    ]

    # 5. Process drugs to extract the base name (prefix) and remove duplicates
    # Example: "Augmentin 1g" -> "Augmentin", "Augmentin 360ml" -> "Augmentin"
    # We use a dictionary to store unique base names and keep the first occurrence's manufacturer
    unique_drugs_map = {}

    for drug in all_drugs:
        trade_name = drug.trade_name
        if not trade_name:
            continue
            
        # Split by space to get the first word (the base name/prefix)
        # e.g., "Augmentin 1g" -> ["Augmentin", "1g"] -> "Augmentin"
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
        pdb_structures=pdb_structures,
    )
