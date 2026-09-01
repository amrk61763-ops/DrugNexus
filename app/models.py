# -*- coding: utf-8 -*-
"""
موديلز SQLAlchemy بتوصف الجداول اللي already موجودة في Neon (اتعملت
بسكريبت الهجرة قبل كده) - الملف ده مبيعملش أي جدول جديد، هو بس "خريطة"
بايثون للجداول الموجودة عشان نقدر نستعلم منها بشكل نوعي (typed).

لو حبيت تتأكد إن الجداول موجودة فعلاً وموصوفة صح، تقدر تشغّل الملف ده
مباشرة (python3 models.py) وهيطبعلك أسماء الأعمدة اللي قرأها.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_name: Mapped[str] = mapped_column()
    manufacturer: Mapped[str] = mapped_column()
    drug_class: Mapped[str] = mapped_column()


class Ingredient(Base):
    __tablename__ = "ingredients"

    pubchem_cid: Mapped[str] = mapped_column(primary_key=True)
    chembl_id: Mapped[str] = mapped_column()
    display_name: Mapped[str] = mapped_column()


class DrugIngredient(Base):
    """جدول الربط - مفيش عمود id مستقل في القاعدة نفسها، فبنقول لـSQLAlchemy
    إن (drug_id + pubchem_cid) مع بعض هم المفتاح الأساسي (composite key) -
    ده وصف بس، مش تعديل على الجدول الحقيقي."""
    __tablename__ = "drug_ingredients"

    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), primary_key=True)
    pubchem_cid: Mapped[str] = mapped_column(ForeignKey("ingredients.pubchem_cid"), primary_key=True)


class IngredientDetail(Base):
    __tablename__ = "ingredient_details"

    pubchem_cid: Mapped[str] = mapped_column(ForeignKey("ingredients.pubchem_cid"), primary_key=True)
    molecular_formula: Mapped[str | None] = mapped_column()
    drug_indication: Mapped[str | None] = mapped_column()
    livertox_summary: Mapped[str | None] = mapped_column()
    pharmacology: Mapped[str | None] = mapped_column()
    mesh_classification: Mapped[str | None] = mapped_column()
    pharmacodynamics: Mapped[str | None] = mapped_column()
    half_life: Mapped[str | None] = mapped_column()
    toxicological_info: Mapped[str | None] = mapped_column()
    hazards_summary: Mapped[str | None] = mapped_column()
    chembl_mechanism_of_action: Mapped[str | None] = mapped_column()
    chembl_molecular_mechanism: Mapped[str | None] = mapped_column()
    chembl_binding_site_comment: Mapped[str | None] = mapped_column()
    chembl_target_id: Mapped[str | None] = mapped_column()
    chembl_target_name: Mapped[str | None] = mapped_column()
    chembl_target_type: Mapped[str | None] = mapped_column()

class PdbReceptor(Base):
    __tablename__ = "pdb_receptors"

    pdb_id: Mapped[str] = mapped_column(primary_key=True)
    pubchem_cid: Mapped[str] = mapped_column("pubchem_cid")  # Remove the "pubchem_cids" string    receptor_file_name: Mapped[str] = mapped_column()
    receptor_blob_pathname: Mapped[str] = mapped_column()
    receptor_blob_url: Mapped[str | None] = mapped_column()


class PdbLigand(Base):
    """مفيش id مستقل - زي DrugIngredient، بنستخدم (pdb_id + ligand_file_name)
    مع بعض كـprimary key وصفي بس (composite key)."""
    __tablename__ = "pdb_ligands"

    pdb_id: Mapped[str] = mapped_column(ForeignKey("pdb_receptors.pdb_id"), primary_key=True)
    ligand_file_name: Mapped[str] = mapped_column(primary_key=True)
    ligand_blob_pathname: Mapped[str] = mapped_column()
    ligand_blob_url: Mapped[str | None] = mapped_column()


if __name__ == "__main__":
    # تشغيل الملف مباشرة (مش عن طريق FastAPI) بيوريك إن الوصف اتقرا صح
    for model in (Drug, Ingredient, DrugIngredient, IngredientDetail):
        cols = [c.name for c in model.__table__.columns]
        print(f"{model.__tablename__}: {cols}")
