import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, Text, Boolean,
)
from backend.database import Base


class AssetType(str, enum.Enum):
    REAL_ESTATE = "real_estate"
    GOLD = "gold"
    VEHICLE = "vehicle"
    INVOICE = "invoice"
    LAND = "land"
    MACHINERY = "machinery"
    ARTWORK = "artwork"
    WAREHOUSE_RECEIPT = "warehouse_receipt"
    BOND = "bond"


class AssetStatus(str, enum.Enum):
    PENDING = "pending"
    MINTED = "minted"
    COLLATERALIZED = "collateralized"
    IN_AUCTION = "in_auction"
    SOLD = "sold"
    BURNED = "burned"


class RWAAsset(Base):
    __tablename__ = "rwa_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_id = Column(Integer, unique=True, nullable=True, index=True)
    name = Column(String(256), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    valuation = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    metadata_uri = Column(String(512), nullable=True)
    ipfs_hash = Column(String(128), nullable=True)
    owner_address = Column(String(42), nullable=False, index=True)
    mint_tx_hash = Column(String(66), nullable=True)
    status = Column(
        Enum(AssetStatus), nullable=False, default=AssetStatus.PENDING
    )
    image_url = Column(String(512), nullable=True)
    location = Column(String(256), nullable=True)
    serial_number = Column(String(128), nullable=True)
    appraiser = Column(String(256), nullable=True)
    appraisal_date = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, default=False)
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
            "token_id": self.token_id,
            "name": self.name,
            "asset_type": self.asset_type.value if self.asset_type else None,
            "description": self.description,
            "valuation": self.valuation,
            "current_value": self.current_value,
            "metadata_uri": self.metadata_uri,
            "ipfs_hash": self.ipfs_hash,
            "owner_address": self.owner_address,
            "mint_tx_hash": self.mint_tx_hash,
            "status": self.status.value if self.status else None,
            "image_url": self.image_url,
            "location": self.location,
            "serial_number": self.serial_number,
            "is_locked": self.is_locked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
