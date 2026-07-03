

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.database import get_db
from backend.schemas.oracle import OraclePriceResponse, OracleUpdateRequest, OracleConfigRequest
from backend.services.oracle_service import OracleService
from backend.engines.oracle_engine import OracleConfig

router = APIRouter(prefix="/oracle", tags=["Oracle"])


@router.post("/update", response_model=OraclePriceResponse)
async def update_oracle_price(payload: OracleUpdateRequest, db: AsyncSession = Depends(get_db)):
    
    try:
        price_log = await OracleService.update_asset_price(
            db, payload.asset_id, payload.price, payload.model
        )
        return price_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oracle write failed: {str(e)}"
        )


@router.post("/config", status_code=status.HTTP_200_OK)
async def configure_oracle_engine(payload: OracleConfigRequest):
    
    try:
        engine = OracleService.get_engine()
        engine.config = OracleConfig(
            price_model=payload.price_model,
            volatility=payload.volatility,
            drift=payload.drift,
            crash_probability=payload.crash_probability,
            crash_magnitude=payload.crash_magnitude,
        )
        return {"status": "success", "message": f"Oracle model updated to {payload.price_model}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to adjust oracle configuration: {str(e)}"
        )


@router.get("/history/{asset_id}", response_model=List[OraclePriceResponse])
async def get_price_history(asset_id: int, limit: int = 100, db: AsyncSession = Depends(get_db)):
    
    return await OracleService.get_price_history(db, asset_id, limit)
