from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "DrugNexus API is running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }
