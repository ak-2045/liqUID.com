

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database import get_db
from backend.services.admin_service import AdminService
from backend.schemas.protocol import ProtocolStateResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/parameters", response_model=ProtocolStateResponse)
async def update_parameters(
    default_interest_rate: Optional[float] = None,
    max_ltv_ratio: Optional[float] = None,
    liquidation_threshold: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    
    try:
        updated_state = await AdminService.update_protocol_parameters(
            db, default_interest_rate, max_ltv_ratio, liquidation_threshold
        )
        return updated_state
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter update failed: {str(e)}"
        )


@router.post("/auctions/{auction_id}/cancel")
async def cancel_auction(auction_id: int, db: AsyncSession = Depends(get_db)):
    
    try:
        cancelled = await AdminService.cancel_auction(db, auction_id)
        return {"status": "success", "message": f"Auction {auction_id} cancelled.", "auction": cancelled.to_dict()}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel auction: {str(e)}"
        )
