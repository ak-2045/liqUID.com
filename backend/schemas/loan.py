

from pydantic import BaseModel, Field
from typing import Optional


class LoanCreate(BaseModel):
    borrower_id: int
    asset_id: int
    principal: float = Field(..., gt=0)
    interest_rate: Optional[float] = None
    maturity_days: int = Field(default=365, gt=0)


class LoanResponse(BaseModel):
    id: int
    borrower_id: int
    asset_id: int
    principal: float
    interest_rate: float
    accrued_interest: float
    total_debt: float
    total_repaid: float
    collateral_value: float
    ltv_ratio: float
    health_factor: float
    liquidation_threshold: float
    status: str
    repayment_count: int
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class RepayRequest(BaseModel):
    loan_id: int
    amount: float = Field(..., gt=0)


class LoanHealthResponse(BaseModel):
    loan_id: int
    ltv_ratio: float
    health_factor: float
    collateral_value: float
    total_debt: float
    liquidation_price: float
    is_healthy: bool
    distance_to_liquidation: float
