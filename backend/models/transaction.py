import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from backend.database import Base


class TxType(str, enum.Enum):
    MINT = "mint"
    DEPOSIT_COLLATERAL = "deposit_collateral"
    WITHDRAW_COLLATERAL = "withdraw_collateral"
    BORROW = "borrow"
    REPAY = "repay"
    LIQUIDATION = "liquidation"
    AUCTION_CREATE = "auction_create"
    AUCTION_BUY = "auction_buy"
    AUCTION_CANCEL = "auction_cancel"
    ORACLE_UPDATE = "oracle_update"
    FEE_COLLECTION = "fee_collection"
    TRANSFER = "transfer"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    tx_type = Column(Enum(TxType), nullable=False, index=True)
    from_address = Column(String(42), nullable=True)
    to_address = Column(String(42), nullable=True)
    amount = Column(Float, default=0.0)
    asset_id = Column(Integer, nullable=True)
    loan_id = Column(Integer, nullable=True)
    auction_id = Column(Integer, nullable=True)
    gas_used = Column(Integer, default=0)
    block_number = Column(Integer, default=0)
    details = Column(Text, nullable=True)
    sim_tick = Column(Integer, default=0)
    timestamp = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "tx_hash": self.tx_hash,
            "tx_type": self.tx_type.value if self.tx_type else None,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "asset_id": self.asset_id,
            "loan_id": self.loan_id,
            "auction_id": self.auction_id,
            "block_number": self.block_number,
            "sim_tick": self.sim_tick,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
