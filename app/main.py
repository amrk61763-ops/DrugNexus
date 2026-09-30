import html
import os

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import active_ingredient, trade_name
from .database import get_db
from .models import Drug


app = FastAPI(
    title="DrugNexus API",
    description="API for searching drug information",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(trade_name.router)
app.include_router(trade_name.drug_router)
app.include_router(active_ingredient.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


@app.get("/sitemap-drugs.xml", include_in_schema=False)
async def sitemap_drugs(db: AsyncSession = Depends(get_db)):
    """Generate the complete drug sitemap from the live database."""
    result = await db.execute(
        select(Drug.id, Drug.trade_name).order_by(Drug.id)
    )
    drugs = result.all()

    site_url = os.getenv("SITE_URL", "https://viadrug.app").rstrip("/")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{html.escape(site_url + '/', quote=False)}</loc></url>",
        f"  <url><loc>{html.escape(site_url + '/data-sources/', quote=False)}</loc></url>",
        f"  <url><loc>{html.escape(site_url + '/disclaimer/', quote=False)}</loc></url>",
        f"  <url><loc>{html.escape(site_url + '/privacy/', quote=False)}</loc></url>",
        f"  <url><loc>{html.escape(site_url + '/terms/', quote=False)}</loc></url>",
        f"  <url><loc>{html.escape(site_url + '/advertising-policy/', quote=False)}</loc></url>",
    ]

    for drug_id, trade_name_value in drugs:
        slug = trade_name.make_slug(trade_name_value)
        url = f"{site_url}/drug/{drug_id}/{slug}"
        lines.append(f"  <url><loc>{html.escape(url, quote=False)}</loc></url>")

    lines.append("</urlset>")
    return Response(content="\n".join(lines), media_type="application/xml")


# Serves the frontend (index.html and friends) at "/" and any non-API path.
# StaticFiles(html=True) serves index.html for the directory itself; API
# routes registered above still resolve first because mounts are checked last.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_BASE_DIR, "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
