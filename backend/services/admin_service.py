

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.protocol import ProtocolState
from backend.models.loan import Loan, LoanStatus
from backend.models.auction import DutchAuction, AuctionStatus
from backend.services.oracle_service import OracleService
from backend.services.simulation_service import SimulationService
from backend.config import get_settings


class AdminService:
    

    @staticmethod
    async def update_protocol_parameters(
        db: AsyncSession,
        default_interest_rate: Optional[float] = None,
        max_ltv_ratio: Optional[float] = None,
        liquidation_threshold: Optional[float] = None,
    ) -> ProtocolState:
        
        settings = get_settings()

        if default_interest_rate is not None:
            settings.default_interest_rate = default_interest_rate
        if max_ltv_ratio is not None:
            settings.max_ltv_ratio = max_ltv_ratio
        if liquidation_threshold is not None:
            settings.liquidation_threshold = liquidation_threshold

        
        state = await SimulationService.recalculate_protocol_state(db)
        await db.commit()
        return state

    @staticmethod
    async def trigger_market_scenario(db: AsyncSession, scenario: str) -> str:
        
        engine = OracleService.get_engine()
        
        if scenario == "crash":
            engine.trigger_crash(magnitude=0.40)
            await OracleService.run_batch_oracle_tick(db)
            return "Market crash scenario triggered successfully (-40% valuation drop)."
        
        elif scenario == "recovery":
            engine.trigger_recovery()
            await OracleService.run_batch_oracle_tick(db)
            return "Market recovery scenario triggered successfully (restoring valuations)."
            
        elif scenario == "rate_hike":
            
            q = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
            res = await db.execute(q)
            loans = res.scalars().all()
            for loan in loans:
                loan.interest_rate += 0.035
            await db.commit()
            return "Rate hike scenario triggered (+350bps applied to all active loans)."
            
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    @staticmethod
    async def cancel_auction(db: AsyncSession, auction_id: int) -> DutchAuction:
        
        q = select(DutchAuction).where(DutchAuction.id == auction_id)
        res = await db.execute(q)
        auc = res.scalars().first()
        if not auc:
            raise ValueError(f"Auction ID {auction_id} not found.")

        if auc.status != AuctionStatus.ACTIVE:
            raise ValueError(f"Only active auctions can be cancelled. Current status: {auc.status}")

        auc.status = AuctionStatus.CANCELLED
        
        
        q_loan = select(Loan).where(Loan.id == auc.loan_id)
        res_loan = await db.execute(q_loan)
        loan = res_loan.scalars().first()
        if loan:
            loan.status = LoanStatus.ACTIVE
            
            
            from backend.engines.risk_engine import RiskEngine
            risk = RiskEngine()
            loan.health_factor = risk.calculate_health_factor(loan.collateral_value, loan.total_debt)

        
        from backend.models.asset import RWAAsset, AssetStatus
        q_asset = select(RWAAsset).where(RWAAsset.id == auc.asset_id)
        res_asset = await db.execute(q_asset)
        asset = res_asset.scalars().first()
        if asset:
            asset.status = AssetStatus.MINTED
            asset.is_locked = False

        await db.commit()
        await db.refresh(auc)
        return auc
