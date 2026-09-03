# -*- coding: utf-8 -*-
"""
شكل الرد (response) الخاص بـendpoint تفاصيل المادة الفعالة - كل الحقول
اللي جبناها من PubChem و ChEMBL (جدول ingredient_details)، بالإضافة لقائمة
الأسماء التجارية اللي بتستخدم المادة دي.
"""

from pydantic import BaseModel


class TradeNameUsingIngredient(BaseModel):
    trade_name: str
    manufacturer: str | None


class LigandFile(BaseModel):
    ligand_file_name: str
    resolution: str | None
    rsr: int | None
    rscc: int | None
    atom_count: int | None
    download_url: str | None


class ReceptorStructure(BaseModel):
    pdb_id: str
    receptor_file_name: str
    resolution: str | None
    experiment_method: str | None
    download_url: str | None
    ligands: list[LigandFile]


class ActiveIngredientResponse(BaseModel):
    pubchem_cid: str
    chembl_id: str | None
    display_name: str

    molecular_formula: str | None
    drug_indication: str | None
    livertox_summary: str | None
    pharmacology: str | None
    mesh_classification: str | None
    pharmacodynamics: str | None
    half_life: str | None
    toxicological_info: str | None
    hazards_summary: str | None

    chembl_mechanism_of_action: str | None
    chembl_molecular_mechanism: str | None
    chembl_binding_site_comment: str | None
    chembl_target_id: str | None
    chembl_target_name: str | None
    chembl_target_type: str | None

    used_in: list[TradeNameUsingIngredient]
    pdb_structures: list[ReceptorStructure]
