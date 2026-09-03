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


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        }


# Serves frontend/index.html at "/", and frontend/trade_name.html,
# frontend/active_ingrediant.html at their matching paths. Vercel's FastAPI
# framework preset provides this — API routes above still resolve first.
app.frontend("/", directory="frontend")