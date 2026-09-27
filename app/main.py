import os

from fastapi import FastAPI
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


# Serves the frontend (index.html and friends) at "/" and any non-API path.
# StaticFiles(html=True) serves index.html for the directory itself; API
# routes registered above still resolve first because mounts are checked last.
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
