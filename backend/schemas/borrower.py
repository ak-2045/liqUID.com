

from pydantic import BaseModel, Field
from typing import Optional


class BorrowerCreate(BaseModel):
    address: str = Field(..., min_length=42, max_length=42)
    name: Optional[str] = None
    credit_score: float = Field(default=700.0, ge=300, le=850)


class BorrowerResponse(BaseModel):
    id: int
    address: str
    name: Optional[str] = None
    credit_score: float
    total_borrowed: float
    total_repaid: float
    active_loans: int
    default_count: int
    total_collateral_value: float
    risk_tier: str
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
