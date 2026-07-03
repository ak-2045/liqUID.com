import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey,
)
from backend.database import Base


class AuctionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DutchAuction(Base):
    __tablename__ = "dutch_auctions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("rwa_assets.id"), nullable=False, index=True)
    start_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    reserve_price = Column(Float, nullable=False)
    decay_rate = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=False, default=21600)
    status = Column(
        Enum(AuctionStatus), nullable=False, default=AuctionStatus.PENDING
    )
    buyer_address = Column(String(42), nullable=True)
    settled_price = Column(Float, nullable=True)
    outstanding_debt = Column(Float, nullable=False)
    protocol_fee = Column(Float, default=0.0)
    borrower_refund = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    sim_tick_start = Column(Integer, default=0)
    sim_tick_end = Column(Integer, nullable=True)
    created_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "loan_id": self.loan_id,
            "asset_id": self.asset_id,
            "start_price": self.start_price,
            "current_price": self.current_price,
            "reserve_price": self.reserve_price,
            "decay_rate": self.decay_rate,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value if self.status else None,
            "buyer_address": self.buyer_address,
            "settled_price": self.settled_price,
            "outstanding_debt": self.outstanding_debt,
            "protocol_fee": self.protocol_fee,
            "borrower_refund": self.borrower_refund,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "sim_tick_start": self.sim_tick_start,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
