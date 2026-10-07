import os
import urllib.request

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_BASE_DIR, "frontend")
_STRUCT_DIR = os.path.join(_FRONTEND_DIR, "assets", "structures")
_CACHE = {"Cache-Control": "public, max-age=2592000, s-maxage=2592000"}


# Structure images, in order of preference:
# 1) a local file frontend/assets/structures/<cid>.png (made by download_structures.py)
# 2) PubChem's official PUG REST API (the old imgsrv URL now shows a browser check)
@app.get("/structure/{cid}")
def structure(cid: int):
    local = os.path.join(_STRUCT_DIR, f"{cid}.png")
    if os.path.isfile(local):
        return FileResponse(local, media_type="image/png", headers=_CACHE)

    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG"
        "?image_size=300x300"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ViaDrug/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            ctype = r.headers.get("Content-Type", "")
    except Exception:
        raise HTTPException(status_code=502, detail="PubChem unavailable")

    # PubChem may answer with an HTML "checking your browser" page instead of an image
    if not ctype.startswith("image/"):
        raise HTTPException(status_code=502, detail="PubChem returned non-image")
    return Response(content=data, media_type=ctype, headers=_CACHE)


# Serves the frontend (index.html and friends) at "/" and any non-API path.
# StaticFiles(html=True) serves index.html for the directory itself; API
# routes registered above still resolve first because mounts are checked last.
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
