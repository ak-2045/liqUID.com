

from pydantic import BaseModel, Field
from typing import Optional


class OraclePriceResponse(BaseModel):
    asset_id: int
    price: float
    previous_price: Optional[float] = None
    delta_pct: float
    price_model: str
    volatility: float
    timestamp: Optional[str] = None

    model_config = {"from_attributes": True}


class OracleUpdateRequest(BaseModel):
    asset_id: int
    price: float = Field(..., gt=0)
    model: str = "manual"


class OracleConfigRequest(BaseModel):
    price_model: str = "gbm"
    volatility: float = Field(default=0.02, ge=0, le=1)
    drift: float = Field(default=0.0, ge=-1, le=1)
    crash_probability: float = Field(default=0.01, ge=0, le=1)
    crash_magnitude: float = Field(default=0.3, ge=0, le=0.9)
