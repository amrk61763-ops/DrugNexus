# -*- coding: utf-8 -*-
"""
صفحة مخصصة لكل دواء:  /drug/{id}/{slug}   (مثال: /drug/123/panadol-500mg)

- بتتعمل Server-side (HTML كامل جوّه الرد) عشان جوجل يشوف المحتوى مباشرة.
- نفس تصميم index.html (القالب في drug_template.py).
- /sitemap.xml ديناميكي: الصفحات الثابتة + كل دواء في الداتابيز.
"""

import html
import json
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .drug_template import TEMPLATE
from .models import Drug
from .trade_name import _batch_ingredients, _batch_interactions

router = APIRouter(tags=["Drug Page"])

SITE = "https://viadrug.app"
MAX_INTERACTIONS = 150  # حد أقصى للتفاعلات المعروضة في الصفحة (الباقي في البحث)
CACHE = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"

STATIC_URLS = [
    ("/", "1.0", "weekly"),
    ("/data-sources/", "0.5", None),
    ("/disclaimer/", "0.4", None),
    ("/privacy/", "0.3", None),
    ("/terms/", "0.3", None),
    ("/advertising-policy/", "0.3", None),
]


def make_slug(value) -> str:
    """لازم يفضل مطابق لـ drugSlug() في index.html."""
    s = unicodedata.normalize("NFKD", str(value or ""))
    s = re.sub(r"[\u0300-\u036f]", "", s).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "drug"


def drug_path(drug_id: int, trade_name: str) -> str:
    return f"/drug/{drug_id}/{make_slug(trade_name)}"


e = html.escape
SEV_STRONG = ("contra", "major", "severe")


def _sev_rank(sev):
    s = (sev or "").lower()
    return 0 if any(k in s for k in SEV_STRONG) else (1 if s else 2)


def _render(title, desc, canon, robots, jsonld, body):
    page = TEMPLATE
    for key, val in {
        "{{TITLE}}": e(title), "{{DESC}}": e(desc), "{{CANON}}": e(canon),
        "{{ROBOTS}}": robots, "{{JSONLD}}": jsonld, "{{BODY}}": body,
    }.items():
        page = page.replace(key, val)
    return page


async def _alternatives(db: AsyncSession, drug_id: int):
    """نفس منطق trade_name.py (نفس مجموعة المواد بالظبط) لكن بيرجع id كمان."""
    target = await db.execute(
        text("SELECT array_agg(pubchem_cid ORDER BY pubchem_cid) FROM drug_ingredients WHERE drug_id = :id"),
        {"id": drug_id},
    )
    target_cids = list(target.scalar() or [])
    if not target_cids:
        return []
    rows = await db.execute(
        text(
            """
            SELECT d.id, d.trade_name, d.manufacturer,
                   array_agg(di.pubchem_cid ORDER BY di.pubchem_cid) AS cids
            FROM drugs d
            JOIN drug_ingredients di ON di.drug_id = d.id
            WHERE d.id <> :id AND d.id IN (
                SELECT drug_id FROM drug_ingredients
                WHERE pubchem_cid IN (SELECT pubchem_cid FROM drug_ingredients WHERE drug_id = :id)
            )
            GROUP BY d.id, d.trade_name, d.manufacturer
            ORDER BY d.trade_name
            """
        ),
        {"id": drug_id},
    )
    return [r for r in rows.mappings().all() if list(r["cids"]) == target_cids]


CHIP = "font-mono text-xs px-3.5 py-1.5 rounded-full "
LABEL = "font-mono text-[11px] uppercase tracking-[0.2em] text-mute dark:text-[#9C9CA3]"
LINK = "underline underline-offset-4 decoration-hair dark:decoration-dhair hover:decoration-ink dark:hover:decoration-snow transition-colors"


def _ingredient_card(i, ing):
    cid = e(str(ing.pubchem_cid))
    n_ix = len(ing.interactions or [])
    return f"""
        <div class="grid grid-cols-1 sm:grid-cols-5 gap-8 border border-hair dark:border-dhair rounded-3xl p-6 sm:p-8">
          <div class="sm:col-span-3 flex flex-col justify-between gap-6">
            <div>
              <div class="flex items-center gap-3"><span class="font-mono text-xs text-faint dark:text-[#8E8E96]">{i:02d}</span>
                <h3 class="text-xl font-bold tracking-tight">{e(ing.display_name)}</h3></div>
              <dl class="mt-4 space-y-2 text-sm font-mono">
                <div class="flex justify-between border-b border-hair dark:border-dhair pb-2"><dt class="text-mute dark:text-[#9C9CA3] text-xs pt-0.5">PubChem CID</dt>
                  <dd><a href="https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" target="_blank" rel="noopener" class="{LINK}">{cid} ↗</a></dd></div>
                <div class="flex justify-between"><dt class="text-mute dark:text-[#9C9CA3] text-xs pt-0.5">ChEMBL ID</dt><dd>{e(ing.chembl_id or '—')}</dd></div>
                <div class="flex justify-between"><dt class="text-mute dark:text-[#9C9CA3] text-xs pt-0.5">Recorded interactions</dt><dd>{n_ix}</dd></div>
              </dl>
            </div>
            <a href="/?type=ingredient&amp;q={e(ing.display_name)}" class="self-start inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold bg-ink dark:bg-snow text-paper dark:text-coal hover:opacity-75 transition-opacity">Know more <span aria-hidden="true">→</span></a>
          </div>
          <div class="sm:col-span-2">
            <div class="border border-hair dark:border-dhair rounded-2xl p-3 h-40 flex items-center justify-center overflow-hidden bg-white">
              <img src="https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid={cid}&amp;t=l" alt="Chemical structure of {e(ing.display_name)}" class="max-h-full w-auto object-contain" loading="lazy" /></div>
            <p class="mt-2 text-[11px] font-mono text-mute dark:text-[#9C9CA3] text-center">Source: PubChem</p>
          </div>
        </div>"""


def _interactions_block(items):
    if not items:
        return '<p class="text-sm text-mute dark:text-[#9C9CA3] border border-hair dark:border-dhair rounded-2xl p-5">No known interactions recorded for the ingredients of this product.</p>'
    total = len(items)
    items = sorted(items, key=lambda x: _sev_rank(x[1].severity))[:MAX_INTERACTIONS]
    lis = []
    for ing_name, ix in items:
        strong = _sev_rank(ix.severity) == 0
        sev_cls = "bg-ink dark:bg-snow text-paper dark:text-coal" if strong else "border border-hair dark:border-dhair text-mute dark:text-[#9C9CA3]"
        other = ix.interacting_drug_name or ix.interacting_class_name or ""
        mech = f'<p class="mt-1.5 text-sm text-mute dark:text-[#9C9CA3] leading-relaxed">{e(ix.mechanism_description)}</p>' if ix.mechanism_description else ""
        lis.append(f"""
          <li class="px-6 sm:px-8 py-5 bg-paper dark:bg-coal">
            <div class="flex flex-wrap items-center gap-2.5">
              <span class="font-mono text-[10px] uppercase tracking-[0.15em] px-2.5 py-1 rounded-full border border-hair dark:border-dhair text-mute dark:text-[#9C9CA3]">{e(ing_name)}</span>
              <span class="font-mono text-[10px] uppercase tracking-[0.15em] px-2.5 py-1 rounded-full {sev_cls}">{e(ix.severity or 'unknown')}</span>
              <span class="font-mono text-[10px] uppercase tracking-[0.15em] px-2.5 py-1 rounded-full border border-hair dark:border-dhair text-mute dark:text-[#9C9CA3]">{e(ix.interaction_type or '')}</span>
            </div>
            <p class="mt-3 text-sm font-semibold">{e(ing_name)} <span class="text-mute dark:text-[#9C9CA3] font-normal">×</span> {e(other)}</p>{mech}
          </li>""")
    more = f'<p class="px-6 sm:px-8 py-3 text-xs font-mono text-mute dark:text-[#9C9CA3] border-t border-hair dark:border-dhair">Showing {len(items)} of {total} — most severe first.</p>' if total > len(items) else ""
    return f"""
        <section class="border border-hair dark:border-dhair rounded-3xl overflow-hidden" aria-labelledby="ddi">
          <div class="px-6 sm:px-8 py-5 flex items-center justify-between border-b border-hair dark:border-dhair ddi-head">
            <h2 id="ddi" class="{LABEL}">Drug Interactions</h2>
            <span class="font-mono text-[11px] px-2.5 py-1 rounded-full bg-ink dark:bg-snow text-paper dark:text-coal">{total} pairs</span></div>
          <ul class="grid sm:grid-cols-2 gap-px bg-hair dark:bg-dhair max-h-[560px] overflow-y-auto thin-scroll">{''.join(lis)}</ul>{more}
        </section>"""


def _alternatives_block(alts):
    if not alts:
        return '<p class="text-sm text-mute dark:text-[#9C9CA3]">No alternatives with the exact same ingredient set.</p>'
    groups: dict[str, list] = {}
    for a in alts:
        key = (re.split(r"[\s\-]+", (a["trade_name"] or "").strip())[0]) or "Other"
        groups.setdefault(key, []).append(a)
    out = []
    for key in sorted(groups):
        rows = "".join(
            f'<a href="{drug_path(a["id"], a["trade_name"])}" class="block p-4 hover:bg-zinc-100 dark:hover:bg-white/[0.06] transition-colors">'
            f'<span class="font-semibold text-sm block truncate">{e(a["trade_name"])}</span>'
            f'<span class="mt-0.5 text-xs text-mute dark:text-[#9C9CA3] block truncate">{e(a["manufacturer"] or "Unknown manufacturer")}</span></a>'
            for a in groups[key]
        )
        n = len(groups[key])
        out.append(f"""
        <details class="border border-hair dark:border-dhair rounded-2xl overflow-hidden mb-2.5 last:mb-0">
          <summary class="p-4 flex items-center justify-between gap-3 hover:bg-zinc-100/20 dark:hover:bg-white/[0.06] transition-colors">
            <span class="min-w-0"><span class="font-bold text-sm block truncate">{e(key)}</span>
              <span class="block mt-0.5 text-xs text-mute dark:text-[#9C9CA3]">{n} {'variant' if n == 1 else 'variants'}</span></span>
            <svg class="chev w-4 h-4 shrink-0 transition-transform text-mute dark:text-[#9C9CA3]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 9l-7 7-7-7"/></svg>
          </summary>
          <div class="border-t border-hair dark:border-dhair divide-y divide-hair dark:divide-dhair">{rows}</div>
        </details>""")
    return "".join(out)


@router.get("/drug/{drug_id}/{slug}", response_class=HTMLResponse)
@router.get("/drug/{drug_id}", response_class=HTMLResponse)
async def drug_page(drug_id: int, slug: str | None = None, db: AsyncSession = Depends(get_db)):
    drug = await db.get(Drug, drug_id)
    if drug is None:
        body = f"""<div class="py-24 text-center">
          <p class="{LABEL} mb-5">404 — Not found</p>
          <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tightest">We couldn't find this drug.</h1>
          <a href="/#search" class="mt-8 inline-flex text-[13px] font-semibold border-b border-ink dark:border-snow pb-0.5">Search the database →</a></div>"""
        return HTMLResponse(_render("Drug not found — ViaDrug", "This drug page does not exist.", SITE + "/", "noindex", "{}", body), status_code=404)

    canonical_path = drug_path(drug.id, drug.trade_name)
    if slug != make_slug(drug.trade_name):
        return RedirectResponse(canonical_path, status_code=301)

    ing_by_drug, cids = await _batch_ingredients(db, [drug.id])
    ingredients = ing_by_drug.get(drug.id, [])
    ix_by_cid = await _batch_interactions(db, cids)
    for ing in ingredients:
        ing.interactions = ix_by_cid.get(ing.pubchem_cid, [])
    alts = await _alternatives(db, drug.id)

    names = [i.display_name for i in ingredients]
    names_txt = ", ".join(names) if names else "not recorded"
    all_ix = [(i.display_name, ix) for i in ingredients for ix in i.interactions]
    canon = SITE + canonical_path

    title = f"{drug.trade_name} — Active Ingredient, Alternatives & Interactions | ViaDrug"
    desc = (f"{drug.trade_name} by {drug.manufacturer or 'unknown manufacturer'} ({drug.drug_class or 'drug'}). "
            f"Active ingredient: {names_txt}. {len(alts)} alternatives and {len(all_ix)} recorded interactions.")[:300]

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Drug",
        "name": drug.trade_name,
        "url": canon,
        "description": desc,
        "drugClass": drug.drug_class,
        "activeIngredient": names_txt if names else None,
        "manufacturer": {"@type": "Organization", "name": drug.manufacturer} if drug.manufacturer else None,
        "isPartOf": {"@type": "WebSite", "name": "ViaDrug", "url": SITE + "/"},
    }, ensure_ascii=False).replace("</", "<\\/")

    cards = "".join(_ingredient_card(n, ing) for n, ing in enumerate(ingredients, 1)) or \
        '<p class="text-sm text-mute dark:text-[#9C9CA3] border border-hair dark:border-dhair rounded-2xl p-5">Active ingredient breakdown is not available for this product.</p>'

    body = f"""
    <nav aria-label="Breadcrumb" class="mb-8 font-mono text-[11px] uppercase tracking-[0.2em] text-mute dark:text-[#9C9CA3]">
      <a href="/" class="hover:text-ink dark:hover:text-snow">ViaDrug</a> <span class="mx-2">/</span>
      <a href="/#search" class="hover:text-ink dark:hover:text-snow">Trade names</a> <span class="mx-2">/</span>
      <span class="text-ink dark:text-snow">{e(drug.trade_name)}</span></nav>
    <div class="grid grid-cols-1 lg:grid-cols-10 gap-8 items-start">
      <article class="lg:col-span-7 border border-hair dark:border-dhair rounded-3xl overflow-hidden">
        <header class="p-8 sm:p-10 border-b border-hair dark:border-dhair">
          <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tightest">{e(drug.trade_name)}</h1>
          <div class="mt-5 flex flex-wrap items-center gap-2">
            <span class="{CHIP}border border-hair dark:border-dhair">{e(drug.manufacturer or '—')}</span>
            <span class="{CHIP}bg-ink dark:bg-snow text-paper dark:text-coal">{e(drug.drug_class or '—')}</span>
            <span class="{CHIP}border border-hair dark:border-dhair text-mute dark:text-[#9C9CA3]">PubChem-grounded · {len(ingredients)} active ingredient(s)</span>
          </div>
        </header>
        <div class="p-8 sm:p-10 grid gap-8">
          <h2 class="{LABEL}">Active Ingredients ({len(ingredients)})</h2>{cards}
          {_interactions_block(all_ix)}
        </div>
      </article>
      <aside class="lg:col-span-3">
        <div class="border border-hair dark:border-dhair rounded-3xl p-6 max-h-[70vh] flex flex-col overflow-hidden">
          <h2 class="{LABEL} mb-5 shrink-0">Alternative Drugs ({len(alts)})</h2>
          <div class="flex-1 min-h-0 overflow-y-auto thin-scroll pr-1">{_alternatives_block(alts)}</div>
        </div>
      </aside>
    </div>"""

    return HTMLResponse(_render(title, desc, canon, "index, follow, max-image-preview:large", jsonld, body),
                        headers={"Cache-Control": CACHE})


@router.get("/sitemap.xml")
async def sitemap(db: AsyncSession = Depends(get_db)):
    today = date.today().isoformat()
    urls = []
    for path, prio, freq in STATIC_URLS:
        cf = f"<changefreq>{freq}</changefreq>" if freq else ""
        urls.append(f"<url><loc>{SITE}{path}</loc><lastmod>{today}</lastmod>{cf}<priority>{prio}</priority></url>")
    rows = await db.execute(select(Drug.id, Drug.trade_name).order_by(Drug.id).limit(49_000))
    for did, name in rows.all():
        urls.append(f"<url><loc>{SITE}{e(drug_path(did, name))}</loc><lastmod>{today}</lastmod><priority>0.6</priority></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>")
    return Response(xml, media_type="application/xml", headers={"Cache-Control": CACHE})
