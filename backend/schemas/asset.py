

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    asset_type: str = Field(..., description="One of: real_estate, gold, vehicle, invoice, land, machinery, artwork, warehouse_receipt, bond")
    description: Optional[str] = None
    valuation: float = Field(..., gt=0)
    owner_address: str = Field(..., min_length=42, max_length=42)
    image_url: Optional[str] = None
    location: Optional[str] = None
    serial_number: Optional[str] = None
    appraiser: Optional[str] = None


class AssetResponse(BaseModel):
    id: int
    token_id: Optional[int] = None
    name: str
    asset_type: str
    description: Optional[str] = None
    valuation: float
    current_value: float
    metadata_uri: Optional[str] = None
    ipfs_hash: Optional[str] = None
    owner_address: str
    mint_tx_hash: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    location: Optional[str] = None
    is_locked: bool = False
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AssetMintRequest(BaseModel):
    asset_id: int


class AssetMetadata(BaseModel):
    name: str
    description: str
    image: str
    external_url: str = "https://liquid.com"
    attributes: list = []
