import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.asset import RWAAsset, AssetType, AssetStatus
from backend.models.borrower import Borrower
from backend.models.transaction import Transaction, TxType
from backend.schemas.asset import AssetCreate
from backend.utils.ipfs_client import upload_metadata_to_ipfs


class AssetService:
    @staticmethod
    async def create_asset(db: AsyncSession, asset_in: AssetCreate) -> RWAAsset:
        asset = RWAAsset(
            name=asset_in.name,
            asset_type=AssetType(asset_in.asset_type),
            description=asset_in.description,
            valuation=asset_in.valuation,
            current_value=asset_in.valuation,
            owner_address=asset_in.owner_address,
            status=AssetStatus.PENDING,
            image_url=asset_in.image_url or "https://picsum.photos/400/300",
            location=asset_in.location,
            serial_number=asset_in.serial_number or f"SN-{uuid.uuid4().hex[:8].upper()}",
            appraiser=asset_in.appraiser or "liqUID Appraisals Ltd",
            appraisal_date=datetime.now(timezone.utc),
            is_locked=False,
        )
        db.add(asset)
        await db.flush()

        q = select(Borrower).where(Borrower.address == asset_in.owner_address)
        res = await db.execute(q)
        borrower = res.scalars().first()
        if not borrower:
            borrower = Borrower(
                address=asset_in.owner_address,
                name=f"Borrower {asset_in.owner_address[:6]}",
                total_collateral_value=asset.valuation,
            )
            db.add(borrower)
        else:
            borrower.total_collateral_value += asset.valuation

        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def get_asset(db: AsyncSession, asset_id: int) -> Optional[RWAAsset]:
        q = select(RWAAsset).where(RWAAsset.id == asset_id)
        res = await db.execute(q)
        return res.scalars().first()

    @staticmethod
    async def get_all_assets(
        db: AsyncSession, owner: Optional[str] = None, status: Optional[str] = None
    ) -> List[RWAAsset]:
        q = select(RWAAsset)
        if owner:
            q = q.where(RWAAsset.owner_address == owner)
        if status:
            q = q.where(RWAAsset.status == AssetStatus(status))
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def tokenize_asset(db: AsyncSession, asset_id: int) -> RWAAsset:
        asset = await AssetService.get_asset(db, asset_id)
        if not asset:
            raise ValueError(f"Asset with ID {asset_id} not found.")

        if asset.status != AssetStatus.PENDING:
            raise ValueError(f"Asset is already in state: {asset.status}")

        metadata = {
            "name": asset.name,
            "description": asset.description or f"liqUID tokenized RWA: {asset.name}",
            "image": asset.image_url,
            "attributes": [
                {"trait_type": "Asset Type", "value": asset.asset_type.value},
                {"trait_type": "Valuation", "value": asset.valuation, "display_type": "number"},
                {"trait_type": "Location", "value": asset.location or "Global"},
                {"trait_type": "Serial Number", "value": asset.serial_number},
            ]
        }

        ipfs_hash, metadata_uri = await upload_metadata_to_ipfs(metadata)

        simulated_token_id = int(hashlib.sha256(f"token_{asset.id}".encode()).hexdigest(), 16) % 1000000
        simulated_tx = f"0x{hashlib.sha256(f'tx_mint_{asset.id}'.encode()).hexdigest()}"

        asset.token_id = simulated_token_id
        asset.ipfs_hash = ipfs_hash
        asset.metadata_uri = metadata_uri
        asset.mint_tx_hash = simulated_tx
        asset.status = AssetStatus.MINTED

        tx = Transaction(
            tx_hash=simulated_tx,
            tx_type=TxType.MINT,
            from_address="0x0000000000000000000000000000000000000000",
            to_address=asset.owner_address,
            amount=asset.valuation,
            asset_id=asset.id,
            details=f"Tokenized asset '{asset.name}' as NFT token #{simulated_token_id}",
        )
        db.add(tx)
        await db.commit()
        await db.refresh(asset)
        return asset
