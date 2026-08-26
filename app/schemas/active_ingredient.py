# -*- coding: utf-8 -*-
"""
شكل الرد (response) الخاص بـendpoint تفاصيل المادة الفعالة - كل الحقول
اللي جبناها من PubChem و ChEMBL (جدول ingredient_details).
"""

from pydantic import BaseModel


class ActiveIngredientResponse(BaseModel):
    pubchem_cid: str
    chembl_id: str
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
