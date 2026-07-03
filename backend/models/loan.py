import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean,
)
from backend.database import Base


class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    LIQUIDATED = "liquidated"
    IN_AUCTION = "in_auction"


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("rwa_assets.id"), nullable=False, index=True)
    principal = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    accrued_interest = Column(Float, default=0.0)
    total_debt = Column(Float, nullable=False)
    total_repaid = Column(Float, default=0.0)
    collateral_value = Column(Float, nullable=False)
    ltv_ratio = Column(Float, nullable=False)
    health_factor = Column(Float, nullable=False)
    liquidation_threshold = Column(Float, default=0.85)
    status = Column(
        Enum(LoanStatus), nullable=False, default=LoanStatus.ACTIVE
    )
    vault_tx_hash = Column(String(66), nullable=True)
    borrow_tx_hash = Column(String(66), nullable=True)
    maturity_date = Column(DateTime, nullable=True)
    last_interest_update = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_auto_repay = Column(Boolean, default=False)
    repayment_count = Column(Integer, default=0)
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
            "borrower_id": self.borrower_id,
            "asset_id": self.asset_id,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "accrued_interest": self.accrued_interest,
            "total_debt": self.total_debt,
            "total_repaid": self.total_repaid,
            "collateral_value": self.collateral_value,
            "ltv_ratio": self.ltv_ratio,
            "health_factor": self.health_factor,
            "liquidation_threshold": self.liquidation_threshold,
            "status": self.status.value if self.status else None,
            "last_interest_update": (
                self.last_interest_update.isoformat()
                if self.last_interest_update else None
            ),
            "repayment_count": self.repayment_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
