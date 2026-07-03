from typing import Dict, List, Optional
from dataclasses import dataclass
from backend.engines.risk_engine import RiskEngine

@dataclass
class LiquidationEvent:
    loan_id: int
    borrower_id: int
    asset_id: int
    debt: float
    collateral_value: float
    health_factor: float
    ltv_ratio: float
    reason: str

class LiquidationEngine:
    def __init__(
        self,
        risk_engine: Optional[RiskEngine] = None,
        min_health_factor: float = 1.0,
        liquidation_penalty: float = 0.05,
        protocol_fee_rate: float = 0.02,
    ):
        self.risk_engine = risk_engine or RiskEngine()
        self.min_health_factor = min_health_factor
        self.liquidation_penalty = liquidation_penalty
        self.protocol_fee_rate = protocol_fee_rate

    def scan_loans(self, loans: List[Dict]) -> List[LiquidationEvent]:
        events = []
        for loan in loans:
            debt = loan.get("debt", 0)
            cv = loan.get("collateral_value", 0)
            threshold = loan.get("liquidation_threshold", 0.85)

            hf = self.risk_engine.calculate_health_factor(cv, debt, threshold)
            ltv = self.risk_engine.calculate_ltv(debt, cv)

            if hf < self.min_health_factor and debt > 0:
                reason = f"Health factor {hf:.4f} below threshold {self.min_health_factor}"
                events.append(LiquidationEvent(
                    loan_id=loan["loan_id"],
                    borrower_id=loan.get("borrower_id", 0),
                    asset_id=loan.get("asset_id", 0),
                    debt=debt,
                    collateral_value=cv,
                    health_factor=round(hf, 4),
                    ltv_ratio=round(ltv, 4),
                    reason=reason,
                ))

        return events

    def calculate_auction_params(
        self,
        event: LiquidationEvent,
        premium_multiplier: float = 1.3,
        duration_seconds: int = 21600,
    ) -> Dict:
        start_price = event.collateral_value * premium_multiplier
        reserve_price = event.debt
        penalty = event.debt * self.liquidation_penalty
        total_owed = event.debt + penalty

        decay_rate = (start_price - reserve_price) / duration_seconds

        return {
            "loan_id": event.loan_id,
            "asset_id": event.asset_id,
            "start_price": round(start_price, 2),
            "reserve_price": round(reserve_price, 2),
            "outstanding_debt": round(event.debt, 2),
            "liquidation_penalty": round(penalty, 2),
            "total_owed": round(total_owed, 2),
            "decay_rate": round(decay_rate, 6),
            "duration_seconds": duration_seconds,
        }

    def calculate_settlement(
        self,
        settled_price: float,
        outstanding_debt: float,
    ) -> Dict:
        protocol_fee = settled_price * self.protocol_fee_rate
        after_fee = settled_price - protocol_fee

        if after_fee >= outstanding_debt:
            debt_repaid = outstanding_debt
            borrower_refund = after_fee - outstanding_debt
            shortfall = 0.0
        else:
            debt_repaid = after_fee
            borrower_refund = 0.0
            shortfall = outstanding_debt - after_fee

        return {
            "settled_price": round(settled_price, 2),
            "debt_repaid": round(debt_repaid, 2),
            "protocol_fee": round(protocol_fee, 2),
            "borrower_refund": round(borrower_refund, 2),
            "shortfall": round(shortfall, 2),
            "is_fully_covered": shortfall == 0,
        }
