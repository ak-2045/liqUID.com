from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean
from backend.database import Base


class ProtocolState(Base):
    __tablename__ = "protocol_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_value_locked = Column(Float, default=0.0)
    total_borrowed = Column(Float, default=0.0)
    total_repaid = Column(Float, default=0.0)
    total_liquidated = Column(Float, default=0.0)
    total_protocol_fees = Column(Float, default=0.0)
    active_loans_count = Column(Integer, default=0)
    defaulted_loans_count = Column(Integer, default=0)
    active_auctions_count = Column(Integer, default=0)
    total_assets_minted = Column(Integer, default=0)
    total_borrowers = Column(Integer, default=0)
    avg_ltv_ratio = Column(Float, default=0.0)
    avg_health_factor = Column(Float, default=0.0)
    avg_interest_rate = Column(Float, default=0.0)
    utilization_rate = Column(Float, default=0.0)
    auction_success_rate = Column(Float, default=0.0)
    recovered_capital = Column(Float, default=0.0)
    protocol_health_score = Column(Float, default=100.0)
    risk_index = Column(Float, default=0.0)
    sim_tick = Column(Integer, default=0)
    sim_running = Column(Boolean, default=False)
    sim_speed = Column(Integer, default=10)
    last_updated = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "total_value_locked": self.total_value_locked,
            "total_borrowed": self.total_borrowed,
            "total_repaid": self.total_repaid,
            "total_liquidated": self.total_liquidated,
            "total_protocol_fees": self.total_protocol_fees,
            "active_loans_count": self.active_loans_count,
            "defaulted_loans_count": self.defaulted_loans_count,
            "active_auctions_count": self.active_auctions_count,
            "total_assets_minted": self.total_assets_minted,
            "total_borrowers": self.total_borrowers,
            "avg_ltv_ratio": self.avg_ltv_ratio,
            "avg_health_factor": self.avg_health_factor,
            "avg_interest_rate": self.avg_interest_rate,
            "utilization_rate": self.utilization_rate,
            "auction_success_rate": self.auction_success_rate,
            "recovered_capital": self.recovered_capital,
            "protocol_health_score": self.protocol_health_score,
            "risk_index": self.risk_index,
            "sim_tick": self.sim_tick,
            "sim_running": self.sim_running,
            "sim_speed": self.sim_speed,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }
