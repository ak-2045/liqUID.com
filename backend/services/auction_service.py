

import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.asset import RWAAsset, AssetStatus
from backend.models.loan import Loan, LoanStatus
from backend.models.borrower import Borrower
from backend.models.auction import DutchAuction, AuctionStatus
from backend.models.transaction import Transaction, TxType
from backend.models.protocol import ProtocolState
from backend.engines.liquidation_engine import LiquidationEngine


class AuctionService:
    

    @staticmethod
    async def get_auction(db: AsyncSession, auction_id: int) -> Optional[DutchAuction]:
        
        q = select(DutchAuction).where(DutchAuction.id == auction_id)
        res = await db.execute(q)
        return res.scalars().first()

    @staticmethod
    async def get_all_auctions(db: AsyncSession, status: Optional[str] = None) -> List[DutchAuction]:
        
        q = select(DutchAuction)
        if status:
            q = q.where(DutchAuction.status == AuctionStatus(status))
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def tick_active_auctions(db: AsyncSession) -> List[DutchAuction]:
        
        q = select(DutchAuction).where(DutchAuction.status == AuctionStatus.ACTIVE)
        res = await db.execute(q)
        active_auctions = res.scalars().all()

        now = datetime.now(timezone.utc)
        updated = []

        for auc in active_auctions:
            elapsed = (now - auc.started_at).total_seconds()
            
            if elapsed >= auc.duration_seconds:
                
                auc.status = AuctionStatus.EXPIRED
                auc.ended_at = now
                
                
                q_l = select(Loan).where(Loan.id == auc.loan_id)
                res_l = await db.execute(q_l)
                loan = res_l.scalars().first()
                if loan:
                    loan.status = LoanStatus.DEFAULTED
                
                q_a = select(RWAAsset).where(RWAAsset.id == auc.asset_id)
                res_a = await db.execute(q_a)
                asset = res_a.scalars().first()
                if asset:
                    asset.status = AssetStatus.BURNED
            else:
                
                decayed = auc.start_price - (auc.decay_rate * elapsed)
                auc.current_price = max(decayed, auc.reserve_price)
                
            updated.append(auc)

        await db.commit()
        return updated

    @staticmethod
    async def settle_auction(
        db: AsyncSession, auction_id: int, buyer_address: str, pay_amount: float
    ) -> DutchAuction:
        
        auc = await AuctionService.get_auction(db, auction_id)
        if not auc:
            raise ValueError(f"Auction ID {auction_id} not found.")
        
        if auc.status != AuctionStatus.ACTIVE:
            raise ValueError(f"Auction is not active: {auc.status}")

        if pay_amount < auc.current_price:
            raise ValueError(f"Offered amount {pay_amount:.2f} is below current price {auc.current_price:.2f}")

        now = datetime.now(timezone.utc)
        liq_engine = LiquidationEngine()
        distributions = liq_engine.calculate_settlement(auc.current_price, auc.outstanding_debt)

        
        auc.status = AuctionStatus.SOLD
        auc.buyer_address = buyer_address
        auc.settled_price = auc.current_price
        auc.protocol_fee = distributions["protocol_fee"]
        auc.borrower_refund = distributions["borrower_refund"]
        auc.ended_at = now

        
        q_loan = select(Loan).where(Loan.id == auc.loan_id)
        res_loan = await db.execute(q_loan)
        loan = res_loan.scalars().first()
        if loan:
            loan.status = LoanStatus.LIQUIDATED
            loan.total_repaid += distributions["debt_repaid"]
            loan.total_debt = max(0, loan.total_debt - distributions["debt_repaid"])

        
        q_asset = select(RWAAsset).where(RWAAsset.id == auc.asset_id)
        res_asset = await db.execute(q_asset)
        asset = res_asset.scalars().first()
        if asset:
            asset.owner_address = buyer_address
            asset.status = AssetStatus.MINTED
            asset.is_locked = False

        
        if loan:
            q_borrower = select(Borrower).where(Borrower.id == loan.borrower_id)
            res_borrower = await db.execute(q_borrower)
            borrower = res_borrower.scalars().first()
            if borrower:
                borrower.active_loans = max(0, borrower.active_loans - 1)
                borrower.default_count += 1
                borrower.credit_score = max(300.0, borrower.credit_score - 50.0)

        
        tx_hash = f"0xbuy_auc_{auc.id}_{int(now.timestamp())}"
        tx_buy = Transaction(
            tx_hash=tx_hash,
            tx_type=TxType.AUCTION_BUY,
            from_address=buyer_address,
            to_address="DutchAuctionContract",
            amount=auc.current_price,
            asset_id=auc.asset_id,
            loan_id=auc.loan_id,
            auction_id=auc.id,
            details=f"Buyer bought collateral NFT #{asset.token_id if asset else ''} for {auc.current_price:.2f} liqUSD",
        )
        db.add(tx_buy)

        
        tx_fee_hash = f"0xfee_{auc.id}_{int(now.timestamp())}"
        tx_fee = Transaction(
            tx_hash=tx_fee_hash,
            tx_type=TxType.FEE_COLLECTION,
            from_address="DutchAuctionContract",
            to_address="ProtocolTreasury",
            amount=distributions["protocol_fee"],
            asset_id=auc.asset_id,
            loan_id=auc.loan_id,
            auction_id=auc.id,
            details=f"Protocol collected {distributions['protocol_fee']:.2f} liqUSD liquidation fees",
        )
        db.add(tx_fee)

        
        q_state = select(ProtocolState)
        res_state = await db.execute(q_state)
        state = res_state.scalars().first()
        if not state:
            state = ProtocolState()
            db.add(state)
        
        state.total_liquidated += distributions["debt_repaid"]
        state.total_protocol_fees += distributions["protocol_fee"]
        state.recovered_capital += distributions["debt_repaid"]

        await db.commit()
        await db.refresh(auc)
        return auc
