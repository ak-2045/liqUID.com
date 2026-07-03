

from pydantic import BaseModel, Field
from typing import Optional


class AuctionResponse(BaseModel):
    id: int
    loan_id: int
    asset_id: int
    start_price: float
    current_price: float
    reserve_price: float
    decay_rate: float
    duration_seconds: int
    status: str
    buyer_address: Optional[str] = None
    settled_price: Optional[float] = None
    outstanding_debt: float
    protocol_fee: float
    borrower_refund: float
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AuctionBuyRequest(BaseModel):
    auction_id: int
    buyer_address: str = Field(..., min_length=42, max_length=42)
    max_price: float = Field(..., gt=0)
