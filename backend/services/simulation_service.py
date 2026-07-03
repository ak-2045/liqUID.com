

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.database import get_session_factory
from backend.models.protocol import ProtocolState
from backend.models.borrower import Borrower
from backend.models.asset import RWAAsset, AssetType, AssetStatus
from backend.models.loan import Loan, LoanStatus
from backend.models.auction import DutchAuction, AuctionStatus
from backend.services.asset_service import AssetService
from backend.services.lending_service import LendingService
from backend.services.oracle_service import OracleService
from backend.services.liquidation_service import LiquidationService
from backend.services.auction_service import AuctionService
from backend.engines.oracle_engine import OracleConfig
from backend.engines.risk_engine import RiskEngine


class SimulationService:
    

    _sim_task: Optional[asyncio.Task] = None
    _running: bool = False
    _speed: int = 10  
    _price_model: str = "gbm"
    _volatility: float = 0.02
    _drift: float = 0.0001
    _auto_repay_prob: float = 0.3

    @classmethod
    async def start_simulation(
        cls, num_loans: int, price_model: str, volatility: float, drift: float, speed: int, auto_repay_prob: float
    ):
        
        if cls._running:
            return

        cls._running = True
        cls._speed = speed
        cls._price_model = price_model
        cls._volatility = volatility
        cls._drift = drift
        cls._auto_repay_prob = auto_repay_prob

        
        oracle_eng = OracleService.get_engine()
        oracle_eng.config = OracleConfig(
            price_model=price_model,
            volatility=volatility,
            drift=drift,
        )

        session_factory = get_session_factory()
        async with session_factory() as db:
            
            await OracleService.initialize_engine_from_db(db)

            
            q = select(ProtocolState)
            res = await db.execute(q)
            state = res.scalars().first()
            if not state:
                state = ProtocolState()
                db.add(state)
            
            state.sim_running = True
            state.sim_speed = speed
            await db.commit()

        
        cls._sim_task = asyncio.create_task(cls._run_simulation_loop())

    @classmethod
    async def stop_simulation(cls):
        
        cls._running = False
        if cls._sim_task:
            cls._sim_task.cancel()
            cls._sim_task = None

        session_factory = get_session_factory()
        async with session_factory() as db:
            q = select(ProtocolState)
            res = await db.execute(q)
            state = res.scalars().first()
            if state:
                state.sim_running = False
                await db.commit()

    @classmethod
    async def _run_simulation_loop(cls):
        
        session_factory = get_session_factory()
        while cls._running:
            try:
                async with session_factory() as db:
                    
                    await OracleService.run_batch_oracle_tick(db)

                    
                    await LendingService.accrue_all_active_interest(db)

                    
                    await cls._simulate_repayment_activity(db)

                    
                    await LiquidationService.scan_and_trigger_liquidations(db)

                    
                    await AuctionService.tick_active_auctions(db)

                    
                    await cls._simulate_auction_purchases(db)

                    
                    await cls.recalculate_protocol_state(db)

                    
                    q = select(ProtocolState)
                    res = await db.execute(q)
                    state = res.scalars().first()
                    if state:
                        state.sim_tick += 1
                        await db.commit()

            except asyncio.CancelledError:
                break
            except Exception:
                
                pass

            
            sleep_time = max(0.1, 5.0 / cls._speed)
            await asyncio.sleep(sleep_time)

    @classmethod
    async def _simulate_repayment_activity(cls, db: AsyncSession):
        
        q = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
        res = await db.execute(q)
        active_loans = res.scalars().all()

        for loan in active_loans:
            if random.random() < (cls._auto_repay_prob * 0.05):
                repay_amt = round(loan.total_debt * random.uniform(0.02, 0.1), 2)
                if repay_amt > 0:
                    await LendingService.repay_loan(db, loan.id, repay_amt)

    @classmethod
    async def _simulate_auction_purchases(cls, db: AsyncSession):
        
        q = select(DutchAuction).where(DutchAuction.status == AuctionStatus.ACTIVE)
        res = await db.execute(q)
        active_auctions = res.scalars().all()

        for auc in active_auctions:
            
            elapsed_pct = (datetime.now(timezone.utc) - auc.started_at).total_seconds() / auc.duration_seconds
            buy_prob = min(0.95, elapsed_pct * 0.4)
            
            if random.random() < buy_prob:
                buyer = f"0x{random.randbytes(20).hex()}"
                try:
                    await AuctionService.settle_auction(db, auc.id, buyer, auc.current_price)
                except Exception:
                    pass

    @classmethod
    async def recalculate_protocol_state(cls, db: AsyncSession) -> ProtocolState:
        
        
        q_state = select(ProtocolState)
        res_state = await db.execute(q_state)
        state = res_state.scalars().first()
        if not state:
            state = ProtocolState()
            db.add(state)

        
        q_l = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
        res_l = await db.execute(q_l)
        active_loans = res_l.scalars().all()

        
        state.active_loans_count = len(active_loans)

        q_def = select(Loan).where(Loan.status.in_([LoanStatus.DEFAULTED, LoanStatus.LIQUIDATED]))
        res_def = await db.execute(q_def)
        state.defaulted_loans_count = len(res_def.scalars().all())

        q_auc = select(DutchAuction).where(DutchAuction.status == AuctionStatus.ACTIVE)
        res_auc = await db.execute(q_auc)
        state.active_auctions_count = len(res_auc.scalars().all())

        
        state.total_value_locked = sum(l.collateral_value for l in active_loans)
        state.total_borrowed = sum(l.total_debt for l in active_loans)

        
        if active_loans:
            state.avg_ltv_ratio = sum(l.ltv_ratio for l in active_loans) / len(active_loans)
            state.avg_health_factor = sum(min(l.health_factor, 10.0) for l in active_loans) / len(active_loans)
            state.avg_interest_rate = sum(l.interest_rate for l in active_loans) / len(active_loans)
        else:
            state.avg_ltv_ratio = 0.0
            state.avg_health_factor = 999.0
            state.avg_interest_rate = 0.0

        
        risk_eng = RiskEngine()
        loan_dicts = [
            {"loan_id": l.id, "debt": l.total_debt, "collateral_value": l.collateral_value}
            for l in active_loans
        ]
        risk_metrics = risk_eng.assess_protocol_risk(loan_dicts)
        state.risk_index = risk_metrics.risk_index
        state.protocol_health_score = risk_metrics.protocol_health_score

        
        await db.flush()
        return state

    @classmethod
    async def generate_mock_portfolio(cls, db: AsyncSession, num_loans: int):
        
        
        await db.execute(select(Loan).delete())
        await db.execute(select(RWAAsset).delete())
        await db.execute(select(Borrower).delete())
        await db.execute(select(DutchAuction).delete())
        await db.execute(select(ProtocolState).delete())
        await db.commit()

        
        state = ProtocolState(
            sim_tick=0,
            sim_running=False,
            sim_speed=cls._speed,
        )
        db.add(state)

        
        borrowers = []
        for i in range(15):
            b = Borrower(
                address=f"0x{random.randbytes(20).hex()}",
                name=f"{BORROWER_NAMES[i % len(BORROWER_NAMES)]} {i//len(BORROWER_NAMES) + 1}",
                credit_score=float(random.randint(580, 830)),
            )
            db.add(b)
            borrowers.append(b)
        await db.flush()

        
        for i in range(num_loans):
            asset_type = random.choice(ASSET_TYPES)
            val_range = VALUE_RANGES[asset_type]
            valuation = round(random.uniform(val_range[0], val_range[1]), 2)
            names = ASSET_NAMES[asset_type]
            asset_name = f"{names[i % len(names)]} #{i+1}"
            
            borrower = random.choice(borrowers)

            
            asset = RWAAsset(
                token_id=i + 1000,
                name=asset_name,
                asset_type=AssetType(asset_type),
                description=f"Simulated collateral asset {asset_name}",
                valuation=valuation,
                current_value=valuation,
                owner_address=borrower.address,
                status=AssetStatus.MINTED,
                image_url=f"https://picsum.photos/seed/asset{i}/400/300",
                location="Staging Vault",
                serial_number=f"SIM-SN-{random.randint(100000, 999999)}",
                is_locked=False,
            )
            db.add(asset)
            await db.flush()

            
            ltv = random.uniform(0.35, 0.70)
            principal = round(valuation * ltv, 2)
            
            
            loan_in = LoanCreate(
                borrower_id=borrower.id,
                asset_id=asset.id,
                principal=principal,
                interest_rate=round(random.uniform(0.04, 0.15), 4),
                maturity_days=random.choice([90, 180, 365, 730]),
            )
            try:
                await LendingService.create_loan(db, loan_in)
            except Exception:
                pass

        
        await cls.recalculate_protocol_state(db)
        await db.commit()
