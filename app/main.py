from pathlib import Path

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


# API routes must be registered before the frontend catch-all mount.
app.include_router(trade_name.router)
app.include_router(active_ingredient.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Serve the frontend from the same FastAPI app. Using an absolute path makes
# this work regardless of the directory from which Uvicorn/Vercel starts.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)
