

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any

from backend.database import get_db
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    
    return await AnalyticsService.get_dashboard_summary(db)


@router.get("/collateral-distribution", response_model=List[Dict[str, Any]])
async def get_collateral_distribution(db: AsyncSession = Depends(get_db)):
    
    return await AnalyticsService.get_collateral_distribution(db)


@router.get("/borrower-segmentation", response_model=List[Dict[str, Any]])
async def get_borrower_segmentation(db: AsyncSession = Depends(get_db)):
    
    return await AnalyticsService.get_borrower_segmentation(db)


@router.get("/oracle-trends", response_model=List[Dict[str, Any]])
async def get_oracle_trends(limit: int = 500, db: AsyncSession = Depends(get_db)):
    
    return await AnalyticsService.get_historical_oracle_trends(db, limit)


@router.get("/risk-breakdown", response_model=Dict[str, int])
async def get_risk_breakdown(db: AsyncSession = Depends(get_db)):
    
    return await AnalyticsService.get_loan_risk_breakdown(db)
