import hashlib
from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.asset import RWAAsset, AssetStatus
from backend.models.loan import Loan, LoanStatus
from backend.models.auction import DutchAuction, AuctionStatus
from backend.models.transaction import Transaction, TxType
from backend.engines.liquidation_engine import LiquidationEngine
from backend.services.auction_service import AuctionService


class LiquidationService:
    @staticmethod
    async def scan_and_trigger_liquidations(db: AsyncSession) -> List[DutchAuction]:
        q = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
        res = await db.execute(q)
        active_loans = res.scalars().all()

        liq_engine = LiquidationEngine()
        created_auctions = []

        loan_dicts = [
            {
                "loan_id": l.id,
                "borrower_id": l.borrower_id,
                "asset_id": l.asset_id,
                "debt": l.total_debt,
                "collateral_value": l.collateral_value,
                "liquidation_threshold": l.liquidation_threshold,
            }
            for l in active_loans
        ]

        events = liq_engine.scan_loans(loan_dicts)

        for ev in events:
            q_l = select(Loan).where(Loan.id == ev.loan_id)
            res_l = await db.execute(q_l)
            loan = res_l.scalars().first()

            q_a = select(RWAAsset).where(RWAAsset.id == ev.asset_id)
            res_a = await db.execute(q_a)
            asset = res_a.scalars().first()

            if loan and asset and loan.status == LoanStatus.ACTIVE:
                loan.status = LoanStatus.IN_AUCTION
                asset.status = AssetStatus.IN_AUCTION

                params = liq_engine.calculate_auction_params(ev)

                auction = DutchAuction(
                    loan_id=loan.id,
                    asset_id=asset.id,
                    start_price=params["start_price"],
                    current_price=params["start_price"],
                    reserve_price=params["reserve_price"],
                    decay_rate=params["decay_rate"],
                    duration_seconds=params["duration_seconds"],
                    status=AuctionStatus.ACTIVE,
                    outstanding_debt=params["outstanding_debt"],
                    started_at=datetime.now(timezone.utc),
                )
                db.add(auction)
                await db.flush()

                tx_hash = f"0xliq_init_{loan.id}_{int(datetime.now().timestamp())}"
                tx = Transaction(
                    tx_hash=tx_hash,
                    tx_type=TxType.LIQUIDATION,
                    from_address="LiquidationEngine",
                    to_address="DutchAuctionContract",
                    amount=loan.total_debt,
                    asset_id=asset.id,
                    loan_id=loan.id,
                    auction_id=auction.id,
                    details=f"Loan #{loan.id} health factor {loan.health_factor:.3f} defaulted. Auction #{auction.id} initialized starting at {auction.start_price:.2f} liqUSD.",
                )
                db.add(tx)
                created_auctions.append(auction)

        if created_auctions:
            await db.commit()

        return created_auctions
