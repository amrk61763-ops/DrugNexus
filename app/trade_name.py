# -*- coding: utf-8 -*-
"""
البحث بالاسم التجاري.

ملاحظة أداء مهمة: النسخة القديمة كانت بتعمل 3 كويريز منفصلة لكل دواء
(ingredients + alternatives + interactions) - يعني صفحة نتائج فيها 20 دواء
= +60 كويري، وده اللي كان بيخلي الاقتراحات اللحظية "بطيئة". هنا كل حاجة
بتتجمع في Batch واحد لكل مجموعة نتائج:
  - _batch_ingredients   : كل المواد الفعالة لكل الأدوية في كويري واحد
  - _batch_interactions  : كل التفاعلات لكل الـ cids في كويري واحد
  - _batch_alternatives  : كل البدائل في كويري واحد (array مقارنة في بايثون)
"""

import html
import json
import os
import re
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug, DrugIngredient, Ingredient
from .schemas.trade_name import (
    AlternativeDrug,
    DrugInteraction,
    IngredientSummary,
    TradeNameResponse,
    TradeNameSearchResult,
)

router = APIRouter(
    prefix="/trade_name",
    tags=["Trade Name"],
)

drug_router = APIRouter(
    tags=["Drug Pages"],
)

SITE_URL = os.getenv("SITE_URL", "https://viadrug.app").rstrip("/")


def make_slug(value: str) -> str:
    """Convert a trade name into a stable, readable ASCII URL slug."""
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "drug"


# ---------------------------------------------------------------------------
# Lightweight live-suggestion endpoint - MUST be defined before "/{trade_name}"
# ---------------------------------------------------------------------------
@router.get("/search", response_model=list[TradeNameSearchResult])
async def search_suggest(q: str, db: AsyncSession = Depends(get_db)):
    """
    اقتراحات خفيفة أثناء الكتابة - بيرجع أسماء فقط (من غير ingredients ولا
    alternatives) عشان تستجيب فورًا. بيحتاج حرفين على الأقل.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return []
    result = await db.execute(
        select(Drug.id, Drug.trade_name, Drug.manufacturer)
        .where(Drug.trade_name.ilike(f"%{q}%"))
        .order_by(Drug.trade_name)
        .limit(10)
    )
    return [
        TradeNameSearchResult(
            id=row.id,
            trade_name=row.trade_name,
            manufacturer=row.manufacturer,
        )
        for row in result.all()
    ]


# ---------------------------------------------------------------------------
# Batched helpers
# ---------------------------------------------------------------------------
async def _batch_ingredients(db: AsyncSession, drug_ids: list[int]):
    """كل مواد كل الأدوية في كويري واحد. بيرجع (خريطة drug_id -> ingredients،
    وقائمة الـ pubchem_cids الفريدة مرتبة)."""
    if not drug_ids:
        return {}, []
    result = await db.execute(
        select(DrugIngredient.drug_id, Ingredient)
        .join(Ingredient, Ingredient.pubchem_cid == DrugIngredient.pubchem_cid)
        .where(DrugIngredient.drug_id.in_(drug_ids))
        .order_by(Ingredient.pubchem_cid)
    )
    by_drug: dict[int, list[Ingredient]] = {i: [] for i in drug_ids}
    cids: set[str] = set()
    for drug_id, ingredient in result.all():
        by_drug[drug_id].append(ingredient)
        cids.add(ingredient.pubchem_cid)
    return by_drug, sorted(cids)


async def _batch_interactions(db: AsyncSession, cids: list[str]) -> dict[str, list[DrugInteraction]]:
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


async def _batch_alternatives(db: AsyncSession, drug_ids: list[int]) -> dict[int, list[AlternativeDrug]]:
    """بدائل كل الأدوية في كويري واحد: بنجيب كل الأدوية اللي عندها مادة مشتركة
    مع أي دواء من القائمة (مرشحين)، وبنجيب مجموعة كل دواء target، وبعدين
    بنقارن المصفوفتين في بايثون."""
    if not drug_ids:
        return {i: [] for i in drug_ids}

    candidates = await db.execute(
        text(
            """
            SELECT d.id AS drug_id, d.trade_name, d.manufacturer,
                   array_agg(di.pubchem_cid ORDER BY di.pubchem_cid) AS cids
            FROM drugs d
            JOIN drug_ingredients di ON di.drug_id = d.id
            WHERE di.pubchem_cid IN (SELECT pubchem_cid FROM drug_ingredients WHERE drug_id = ANY(:ids))
            GROUP BY d.id, d.trade_name, d.manufacturer
            """
        ),
        {"ids": drug_ids},
    )

    targets = await db.execute(
        text(
            """
            SELECT drug_id, array_agg(pubchem_cid ORDER BY pubchem_cid) AS cids
            FROM drug_ingredients
            WHERE drug_id = ANY(:ids)
            GROUP BY drug_id
            """
        ),
        {"ids": drug_ids},
    )
    target_map = {row.drug_id: list(row.cids) for row in targets.all()}

    by_drug: dict[int, list[AlternativeDrug]] = {i: [] for i in drug_ids}
    for row in candidates.mappings().all():
        cand_id = row["drug_id"]
        for drug_id, target_cids in target_map.items():
            if cand_id == drug_id:
                continue
            if list(row["cids"]) == target_cids:
                by_drug[drug_id].append(
                    AlternativeDrug(
                        id=cand_id,
                        trade_name=row["trade_name"],
                        manufacturer=row["manufacturer"],
                    )
                )
    return by_drug


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------
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
        result = await db.execute(
            select(Drug)
            .where(Drug.trade_name.ilike(f"%{trade_name.strip()}%"))
            .order_by(Drug.trade_name)
            .limit(20)
        )
        drugs = result.scalars().all()

        if not drugs:
            return []

        drug_ids = [d.id for d in drugs]

        # كل البيانات الإضافية في 3 كويريز batched بدل 3×N
        ing_by_drug, cids = await _batch_ingredients(db, drug_ids)
        ix_by_cid = await _batch_interactions(db, cids)
        alt_by_drug = await _batch_alternatives(db, drug_ids)

        responses = []
        for drug in drugs:
            ingredients = [
                IngredientSummary(
                    pubchem_cid=ing.pubchem_cid,
                    chembl_id=ing.chembl_id,
                    display_name=ing.display_name,
                    interactions=ix_by_cid.get(ing.pubchem_cid, []),
                )
                for ing in ing_by_drug[drug.id]
            ]
            responses.append(
                TradeNameResponse(
                    id=drug.id,
                    trade_name=drug.trade_name,
                    manufacturer=drug.manufacturer,
                    drug_class=drug.drug_class,
                    active_ingredients=ingredients,
                    alternatives=alt_by_drug[drug.id],
                )
            )

        return responses

    except HTTPException:
        raise
    except Exception as error:
        print(f"Trade name search error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search for the trade name",
        )


# ---------------------------------------------------------------------------
# Indexable server-rendered drug page
# ---------------------------------------------------------------------------
@drug_router.get(
    "/drug/{drug_id}/{slug}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def drug_page(
    drug_id: int,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Drug).where(Drug.id == drug_id))
    drug = result.scalar_one_or_none()

    if drug is None:
        raise HTTPException(status_code=404, detail="Drug not found")

    correct_slug = make_slug(drug.trade_name)
    if slug != correct_slug:
        return RedirectResponse(
            url=f"/drug/{drug.id}/{correct_slug}",
            status_code=301,
        )

    ing_by_drug, cids = await _batch_ingredients(db, [drug.id])
    ix_by_cid = await _batch_interactions(db, cids)
    alt_by_drug = await _batch_alternatives(db, [drug.id])

    ingredients = ing_by_drug.get(drug.id, [])
    alternatives = alt_by_drug.get(drug.id, [])

    title = f"{drug.trade_name} — ViaDrug"
    description = (
        f"{drug.trade_name} by {drug.manufacturer}: active ingredients, "
        f"drug class, interactions, and alternatives."
    )
    canonical = f"{SITE_URL}/drug/{drug.id}/{correct_slug}"

    structured_data = {
        "@context": "https://schema.org",
        "@type": "Drug",
        "name": drug.trade_name,
        "manufacturer": {
            "@type": "Organization",
            "name": drug.manufacturer,
        },
        "url": canonical,
    }
    json_ld = (
        json.dumps(structured_data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    ingredient_items = []
    for ingredient in ingredients:
        ingredient_url = f"/active_ingredient/{quote(ingredient.display_name, safe='')}"
        ingredient_html = (
            f'<li class="ingredient">'
            f'<a href="{html.escape(ingredient_url, quote=True)}">'
            f'{html.escape(ingredient.display_name)}'
            f'</a>'
            f'<span class="meta">PubChem CID: {html.escape(str(ingredient.pubchem_cid))}'
        )
        if ingredient.chembl_id:
            ingredient_html += f' · ChEMBL: {html.escape(ingredient.chembl_id)}'
        ingredient_html += "</span>"

        interactions = ix_by_cid.get(ingredient.pubchem_cid, [])
        if interactions:
            ingredient_html += '<div class="interaction-list"><h3>Drug interactions</h3><ul>'
            for interaction in interactions:
                pieces = []
                if interaction.interacting_drug_name:
                    pieces.append(html.escape(interaction.interacting_drug_name))
                if interaction.interacting_class_name:
                    pieces.append(html.escape(interaction.interacting_class_name))
                if interaction.interaction_type:
                    pieces.append(html.escape(interaction.interaction_type))
                if interaction.severity:
                    pieces.append(f'<strong>Severity:</strong> {html.escape(interaction.severity)}')
                if interaction.mechanism_description:
                    pieces.append(html.escape(interaction.mechanism_description))
                if interaction.interacting_drug_pubchem_cid:
                    pieces.append(
                        f'PubChem CID: {html.escape(interaction.interacting_drug_pubchem_cid)}'
                    )
                ingredient_html += f'<li>{" · ".join(pieces)}</li>'
            ingredient_html += "</ul></div>"

        ingredient_html += "</li>"
        ingredient_items.append(ingredient_html)

    alternatives_html = ""
    if alternatives:
        alternatives_html = (
            '<section><h2>Alternatives</h2><ul class="alternatives">'
            + "".join(
                f'<li><a href="/drug/{alternative.id}/{make_slug(alternative.trade_name)}">'
                f'{html.escape(alternative.trade_name)}</a>'
                f'<span class="meta"> · {html.escape(alternative.manufacturer)}</span></li>'
                for alternative in alternatives
            )
            + "</ul></section>"
        )

    html_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <script type="application/ld+json">{json_ld}</script>
  <style>
    :root {{ color-scheme: light; --bg:#fafaf9; --text:#111; --muted:#71717a; --line:#e4e4e7; --card:#fff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.6; }}
    main {{ width:min(920px,100%); margin:0 auto; padding:48px 20px 80px; }}
    a {{ color:inherit; }}
    .top {{ margin-bottom:28px; }}
    .brand {{ font-weight:800; text-decoration:none; }}
    h1 {{ margin:8px 0 12px; font-size:clamp(32px,6vw,54px); line-height:1.08; letter-spacing:-.03em; }}
    h2 {{ margin:36px 0 14px; font-size:24px; letter-spacing:-.02em; }}
    h3 {{ margin:18px 0 8px; font-size:15px; }}
    p {{ margin:8px 0; }}
    .muted,.meta {{ color:var(--muted); font-size:14px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:22px; }}
    ul {{ margin:0; padding-left:22px; }}
    li {{ margin:8px 0; }}
    .ingredient {{ margin:14px 0; }}
    .ingredient > a {{ font-weight:700; text-decoration:underline; text-underline-offset:3px; }}
    .interaction-list {{ margin-top:10px; padding:14px 16px; border-left:2px solid var(--line); }}
    .alternatives a {{ text-decoration:underline; text-underline-offset:3px; }}
    .source {{ margin-top:34px; padding-top:18px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; }}
  </style>
</head>
<body>
  <main>
    <div class="top"><a class="brand" href="/">ViaDrug</a></div>
    <article>
      <h1>{html.escape(drug.trade_name)}</h1>
      <p><strong>Manufacturer:</strong> {html.escape(drug.manufacturer)}</p>
      <p><strong>Drug class:</strong> {html.escape(drug.drug_class)}</p>

      <section>
        <h2>Active ingredients</h2>
        <div class="card">
          <ul>{"".join(ingredient_items) or '<li>No active ingredients recorded.</li>'}</ul>
        </div>
      </section>

      {alternatives_html}

      <div class="source">
        Drug information is provided for scientific and educational reference. Verify important medical decisions against the cited source databases and qualified healthcare professionals.
      </div>
    </article>
  </main>
</body>
</html>"""

    return HTMLResponse(content=html_page)
