

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.database import get_db
from backend.schemas.asset import AssetCreate, AssetResponse, AssetMintRequest
from backend.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def register_asset(asset: AssetCreate, db: AsyncSession = Depends(get_db)):
    
    try:
        new_asset = await AssetService.create_asset(db, asset)
        return new_asset
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register asset: {str(e)}"
        )


@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    owner: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    
    return await AssetService.get_all_assets(db, owner, status)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    
    asset = await AssetService.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset ID {asset_id} not found."
        )
    return asset


@router.post("/tokenize", response_model=AssetResponse)
async def tokenize_asset(payload: AssetMintRequest, db: AsyncSession = Depends(get_db)):
    
    try:
        asset = await AssetService.tokenize_asset(db, payload.asset_id)
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tokenization failed: {str(e)}"
        )
