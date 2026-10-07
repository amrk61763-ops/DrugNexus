import os
import urllib.request

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import active_ingredient, trade_name


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
app.include_router(active_ingredient.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


# Proxies PubChem structure images through our own domain so the browser
# never has to hit PubChem directly (avoids CSP / referrer / throttling issues).
@app.get("/structure/{cid}")
def structure(cid: int):
    url = f"https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid={cid}&t=l"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ViaDrug/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            ctype = r.headers.get("Content-Type", "image/png")
    except Exception:
        raise HTTPException(status_code=502, detail="PubChem unavailable")
    return Response(
        content=data,
        media_type=ctype,
        headers={"Cache-Control": "public, max-age=2592000, s-maxage=2592000"},
    )


# Serves the frontend (index.html and friends) at "/" and any non-API path.
# StaticFiles(html=True) serves index.html for the directory itself; API
# routes registered above still resolve first because mounts are checked last.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_BASE_DIR, "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
