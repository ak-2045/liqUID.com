from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database import Base


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(42), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=True)
    credit_score = Column(Float, default=700.0)
    total_borrowed = Column(Float, default=0.0)
    total_repaid = Column(Float, default=0.0)
    active_loans = Column(Integer, default=0)
    default_count = Column(Integer, default=0)
    total_collateral_value = Column(Float, default=0.0)
    risk_tier = Column(String(20), default="standard")
    created_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "address": self.address,
            "name": self.name,
            "credit_score": self.credit_score,
            "total_borrowed": self.total_borrowed,
            "total_repaid": self.total_repaid,
            "active_loans": self.active_loans,
            "default_count": self.default_count,
            "total_collateral_value": self.total_collateral_value,
            "risk_tier": self.risk_tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
