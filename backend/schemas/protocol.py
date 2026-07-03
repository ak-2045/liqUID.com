

from pydantic import BaseModel, Field
from typing import Optional


class ProtocolStateResponse(BaseModel):
    total_value_locked: float
    total_borrowed: float
    total_repaid: float
    total_liquidated: float
    total_protocol_fees: float
    active_loans_count: int
    defaulted_loans_count: int
    active_auctions_count: int
    total_assets_minted: int
    total_borrowers: int
    avg_ltv_ratio: float
    avg_health_factor: float
    avg_interest_rate: float
    utilization_rate: float
    auction_success_rate: float
    recovered_capital: float
    protocol_health_score: float
    risk_index: float
    sim_tick: int
    sim_running: bool
    sim_speed: int

    model_config = {"from_attributes": True}


class SimulationConfig(BaseModel):
    num_loans: int = Field(default=100, ge=1, le=5000)
    price_model: str = "gbm"
    volatility: float = Field(default=0.02, ge=0, le=1.0)
    drift: float = Field(default=0.0, ge=-0.5, le=0.5)
    speed: int = Field(default=10, ge=1, le=100)
    crash_probability: float = Field(default=0.01, ge=0, le=1)
    auto_repay_probability: float = Field(default=0.3, ge=0, le=1)
    market_scenario: str = Field(default="normal")


class SimulationCommand(BaseModel):
    action: str = Field(..., description="start, pause, resume, step, reset, crash, recover, rate_hike")
    params: Optional[dict] = None
