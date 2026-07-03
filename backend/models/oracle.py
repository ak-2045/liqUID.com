import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from backend.database import Base


class PriceModel(str, enum.Enum):
    RANDOM_WALK = "random_walk"
    GBM = "gbm"
    MARKET_CRASH = "market_crash"
    SEASONAL = "seasonal"
    ECONOMIC_CYCLE = "economic_cycle"
    MANUAL = "manual"
    RECOVERY = "recovery"


class OraclePrice(Base):
    __tablename__ = "oracle_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("rwa_assets.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    previous_price = Column(Float, nullable=True)
    delta_pct = Column(Float, default=0.0)
    price_model = Column(Enum(PriceModel), nullable=False, default=PriceModel.GBM)
    volatility = Column(Float, default=0.0)
    confidence = Column(Float, default=1.0)
    sim_tick = Column(Integer, default=0)
    timestamp = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "price": self.price,
            "previous_price": self.previous_price,
            "delta_pct": self.delta_pct,
            "price_model": self.price_model.value if self.price_model else None,
            "volatility": self.volatility,
            "confidence": self.confidence,
            "sim_tick": self.sim_tick,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
