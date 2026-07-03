

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.database import get_db
from backend.schemas.auction import AuctionResponse, AuctionBuyRequest
from backend.services.auction_service import AuctionService

router = APIRouter(prefix="/auctions", tags=["Auctions"])


@router.get("/", response_model=List[AuctionResponse])
async def list_auctions(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    
    return await AuctionService.get_all_auctions(db, status)


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(auction_id: int, db: AsyncSession = Depends(get_db)):
    
    auc = await AuctionService.get_auction(db, auction_id)
    if not auc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction ID {auction_id} not found."
        )
    return auc


@router.post("/buy", response_model=AuctionResponse)
async def purchase_collateral(payload: AuctionBuyRequest, db: AsyncSession = Depends(get_db)):
    
    try:
        settled_auction = await AuctionService.settle_auction(
            db, payload.auction_id, payload.buyer_address, payload.max_price
        )
        return settled_auction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auction buy transaction failed: {str(e)}"
        )
