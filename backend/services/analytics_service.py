from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.models.protocol import ProtocolState
from backend.models.asset import RWAAsset, AssetType, AssetStatus
from backend.models.loan import Loan, LoanStatus
from backend.models.borrower import Borrower
from backend.models.auction import DutchAuction, AuctionStatus
from backend.models.oracle import OraclePrice
from backend.models.transaction import Transaction


class AnalyticsService:
    @staticmethod
    async def get_protocol_metrics(db: AsyncSession) -> Dict[str, Any]:
        q = select(ProtocolState)
        res = await db.execute(q)
        state = res.scalars().first()
        if not state:
            return {}
        return state.to_dict()

    @staticmethod
    async def get_dashboard_summary(db: AsyncSession) -> Dict[str, Any]:
        q_state = select(ProtocolState)
        res_state = await db.execute(q_state)
        state = res_state.scalars().first()

        metrics = state.to_dict() if state else {
            "total_value_locked": 0.0,
            "total_borrowed": 0.0,
            "total_repaid": 0.0,
            "total_protocol_fees": 0.0,
            "active_loans_count": 0,
            "active_auctions_count": 0,
            "protocol_health_score": 100.0,
            "risk_index": 0.0,
        }

        q_all_auc = select(func.count(DutchAuction.id))
        res_all_auc = await db.execute(q_all_auc)
        total_auctions = res_all_auc.scalar() or 0

        q_sold_auc = select(func.count(DutchAuction.id)).where(DutchAuction.status == AuctionStatus.SOLD)
        res_sold_auc = await db.execute(q_sold_auc)
        sold_auctions = res_sold_auc.scalar() or 0

        metrics["auction_success_rate"] = (
            (sold_auctions / total_auctions) if total_auctions > 0 else 1.0
        )

        return metrics

    @staticmethod
    async def get_collateral_distribution(db: AsyncSession) -> List[Dict[str, Any]]:
        q = select(
            RWAAsset.asset_type,
            func.count(RWAAsset.id).label("count"),
            func.sum(RWAAsset.current_value).label("value")
        ).group_by(RWAAsset.asset_type)
        res = await db.execute(q)
        
        data = []
        for row in res.all():
            data.append({
                "asset_type": row[0].value if row[0] else "unknown",
                "count": row[1],
                "value": float(row[2] or 0.0),
            })
        return data

    @staticmethod
    async def get_borrower_segmentation(db: AsyncSession) -> List[Dict[str, Any]]:
        q = select(Borrower)
        res = await db.execute(q)
        borrowers = res.scalars().all()

        segments = {"Safe (750+)": 0, "Good (700-749)": 0, "Fair (650-699)": 0, "Subprime (<650)": 0}
        for b in borrowers:
            if b.credit_score >= 750:
                segments["Safe (750+)"] += 1
            elif b.credit_score >= 700:
                segments["Good (700-749)"] += 1
            elif b.credit_score >= 650:
                segments["Fair (650-699)"] += 1
            else:
                segments["Subprime (<650)"] += 1

        return [{"segment": k, "count": v} for k, v in segments.items()]

    @staticmethod
    async def get_historical_oracle_trends(db: AsyncSession, limit: int = 500) -> List[Dict[str, Any]]:
        q = select(
            OraclePrice.timestamp,
            OraclePrice.price,
            RWAAsset.name,
            RWAAsset.asset_type
        ).join(RWAAsset, OraclePrice.asset_id == RWAAsset.id).order_by(OraclePrice.timestamp.desc()).limit(limit)
        res = await db.execute(q)

        return [
            {
                "timestamp": row[0].isoformat() if row[0] else None,
                "price": row[1],
                "asset_name": row[2],
                "asset_type": row[3].value if row[3] else "unknown",
            }
            for row in res.all()
        ]

    @staticmethod
    async def get_loan_risk_breakdown(db: AsyncSession) -> Dict[str, int]:
        q = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
        res = await db.execute(q)
        loans = res.scalars().all()

        buckets = {"critical": 0, "high": 0, "medium": 0, "low": 0, "safe": 0}
        for l in loans:
            hf = l.health_factor
            if hf < 1.0:
                buckets["critical"] += 1
            elif hf < 1.2:
                buckets["high"] += 1
            elif hf < 1.5:
                buckets["medium"] += 1
            elif hf < 2.0:
                buckets["low"] += 1
            else:
                buckets["safe"] += 1
        return buckets
