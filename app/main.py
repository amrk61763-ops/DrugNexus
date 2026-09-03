from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import active_ingredient, trade_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    try:
        await engine.dispose()
    except Exception as error:
        print(f"Database shutdown error: {error}")


app = FastAPI(
    title="DrugNexus API",
    description="Professional async API for drug information lookup",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(trade_name.router)
app.include_router(active_ingredient.router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "DrugNexus API",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
