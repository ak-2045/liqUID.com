

from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.asset import RWAAsset
from backend.models.oracle import OraclePrice, PriceModel
from backend.models.loan import Loan, LoanStatus
from backend.models.transaction import Transaction, TxType
from backend.engines.oracle_engine import OracleEngine, OracleConfig
from backend.engines.risk_engine import RiskEngine
from backend.config import get_settings


class OracleService:
    

    _engine: Optional[OracleEngine] = None

    @classmethod
    def get_engine(cls, config: Optional[OracleConfig] = None) -> OracleEngine:
        
        if cls._engine is None:
            cls._engine = OracleEngine(config)
        return cls._engine

    @staticmethod
    async def update_asset_price(
        db: AsyncSession, asset_id: int, new_price: float, model: str = "manual"
    ) -> OraclePrice:
        
        q_asset = select(RWAAsset).where(RWAAsset.id == asset_id)
        res_asset = await db.execute(q_asset)
        asset = res_asset.scalars().first()
        if not asset:
            raise ValueError(f"Asset ID {asset_id} not found.")

        old_price = asset.current_value
        asset.current_value = new_price
        delta = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0

        
        hist = OraclePrice(
            asset_id=asset.id,
            price=new_price,
            previous_price=old_price,
            delta_pct=delta,
            price_model=PriceModel(model),
            volatility=0.0,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(hist)

        
        engine = OracleService.get_engine()
        if asset.id in engine.asset_states:
            engine.set_manual_price(asset.id, new_price)

        
        q_loans = select(Loan).where(
            Loan.asset_id == asset.id,
            Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.IN_AUCTION])
        )
        res_loans = await db.execute(q_loans)
        loans = res_loans.scalars().all()
        
        risk_eng = RiskEngine()
        for loan in loans:
            loan.collateral_value = new_price
            loan.ltv_ratio = risk_eng.calculate_ltv(loan.total_debt, new_price)
            loan.health_factor = risk_eng.calculate_health_factor(
                new_price, loan.total_debt, loan.liquidation_threshold
            )

        
        tx_hash = f"0xupdate_price_{asset.id}_{int(datetime.now().timestamp())}"
        tx = Transaction(
            tx_hash=tx_hash,
            tx_type=TxType.ORACLE_UPDATE,
            details=f"Oracle update for asset '{asset.name}': {old_price:.2f} -> {new_price:.2f} ({delta:+.2f}%)",
            amount=new_price,
            asset_id=asset.id,
        )
        db.add(tx)
        
        await db.commit()
        return hist

    @staticmethod
    async def initialize_engine_from_db(db: AsyncSession):
        
        q = select(RWAAsset)
        res = await db.execute(q)
        assets = res.scalars().all()
        
        engine = OracleService.get_engine()
        for asset in assets:
            if asset.id not in engine.asset_states:
                engine.register_asset(asset.id, asset.valuation, asset.asset_type.value)
                
                engine.asset_states[asset.id].current_price = asset.current_value

    @staticmethod
    async def get_price_history(db: AsyncSession, asset_id: int, limit: int = 100) -> List[OraclePrice]:
        
        q = select(OraclePrice).where(OraclePrice.asset_id == asset_id).order_by(OraclePrice.timestamp.desc()).limit(limit)
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def run_batch_oracle_tick(db: AsyncSession) -> Dict[int, float]:
        
        engine = OracleService.get_engine()
        updates = engine.update_prices()  
        
        results = {}
        risk_eng = RiskEngine()

        for asset_id, (new_price, old_price, delta) in updates.items():
            
            q_asset = select(RWAAsset).where(RWAAsset.id == asset_id)
            res_asset = await db.execute(q_asset)
            asset = res_asset.scalars().first()
            if asset:
                asset.current_value = new_price
                
                
                hist = OraclePrice(
                    asset_id=asset.id,
                    price=new_price,
                    previous_price=old_price,
                    delta_pct=delta,
                    price_model=PriceModel(engine.config.price_model),
                    volatility=engine.get_volatility(asset.id),
                    timestamp=datetime.now(timezone.utc),
                    sim_tick=engine.tick,
                )
                db.add(hist)

                
                q_loans = select(Loan).where(
                    Loan.asset_id == asset.id,
                    Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.IN_AUCTION])
                )
                res_loans = await db.execute(q_loans)
                loans = res_loans.scalars().all()
                for loan in loans:
                    loan.collateral_value = new_price
                    loan.ltv_ratio = risk_eng.calculate_ltv(loan.total_debt, new_price)
                    loan.health_factor = risk_eng.calculate_health_factor(
                        new_price, loan.total_debt, loan.liquidation_threshold
                    )
                
                results[asset_id] = new_price

        await db.commit()
        return results
