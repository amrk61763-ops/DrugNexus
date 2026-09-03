from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Drug


router = APIRouter(
    prefix="/trade_name",
    tags=["Trade Name"],
)


@router.get("/{trade_name}")
async def search_by_trade_name(
    trade_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for a drug by its trade name.

    Example:
    GET /trade_name/aspirin
    """

    if not trade_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Trade name cannot be empty",
        )

    try:
        query = (
            select(Drug)
            .where(Drug.trade_name.ilike(f"%{trade_name.strip()}%"))
            .limit(20)
        )

        result = await db.execute(query)
        drugs = result.scalars().all()

        return [
            {
                "id": drug.id,
                "trade_name": drug.trade_name,
                "manufacturer": drug.manufacturer,
                "drug_class": drug.drug_class,
            }
            for drug in drugs
        ]

    except Exception as error:
        print(f"Trade name search error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to search for the trade name",
        )
