

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.database import get_db
from backend.schemas.loan import LoanCreate, LoanResponse, RepayRequest, LoanHealthResponse
from backend.services.lending_service import LendingService
from backend.engines.risk_engine import RiskEngine

router = APIRouter(prefix="/loans", tags=["Lending"])


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def borrow_against_collateral(loan: LoanCreate, db: AsyncSession = Depends(get_db)):
    
    try:
        new_loan = await LendingService.create_loan(db, loan)
        return new_loan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lending pool transaction failed: {str(e)}"
        )


@router.get("/", response_model=List[LoanResponse])
async def list_loans(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    
    return await LendingService.get_all_loans(db, status)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    
    loan = await LendingService.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan ID {loan_id} not found."
        )
    return loan


@router.post("/repay", response_model=LoanResponse)
async def repay_loan(payload: RepayRequest, db: AsyncSession = Depends(get_db)):
    
    try:
        loan, surplus = await LendingService.repay_loan(db, payload.loan_id, payload.amount)
        
        return loan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repayment settlement failed: {str(e)}"
        )


@router.get("/{loan_id}/health", response_model=LoanHealthResponse)
async def get_loan_health(loan_id: int, db: AsyncSession = Depends(get_db)):
    
    loan = await LendingService.accrue_loan_interest(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan ID {loan_id} not found."
        )

    risk = RiskEngine(loan.liquidation_threshold)
    risk_metrics = risk.assess_loan_risk(loan.id, loan.total_debt, loan.collateral_value)
    
    
    distance = max(0.0, loan.health_factor - 1.0)
    
    
    liq_price = risk.calculate_liquidation_price(loan.total_debt, 1.0, loan.liquidation_threshold)

    return LoanHealthResponse(
        loan_id=loan.id,
        ltv_ratio=loan.ltv_ratio,
        health_factor=loan.health_factor,
        collateral_value=loan.collateral_value,
        total_debt=loan.total_debt,
        liquidation_price=round(liq_price, 2),
        is_healthy=risk_metrics.is_healthy,
        distance_to_liquidation=round(distance, 4),
    )
