import math
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class LoanRiskMetrics:
    loan_id: int
    ltv_ratio: float
    health_factor: float
    liquidation_price: float
    distance_to_liquidation: float
    liquidation_probability: float
    risk_tier: str
    is_healthy: bool

@dataclass
class ProtocolRiskMetrics:
    weighted_avg_ltv: float
    weighted_avg_health_factor: float
    concentration_risk: float
    largest_position_pct: float
    at_risk_loans_count: int
    at_risk_value: float
    expected_loss: float
    risk_index: float
    protocol_health_score: float

class RiskEngine:
    def __init__(
        self,
        liquidation_threshold: float = 0.85,
        min_health_factor: float = 1.0,
        warning_health_factor: float = 1.2,
    ):
        self.liquidation_threshold = liquidation_threshold
        self.min_health_factor = min_health_factor
        self.warning_health_factor = warning_health_factor

    def calculate_ltv(self, debt: float, collateral_value: float) -> float:
        if collateral_value <= 0:
            return float('inf')
        return debt / collateral_value

    def calculate_health_factor(
        self, collateral_value: float, debt: float,
        liquidation_threshold: Optional[float] = None,
    ) -> float:
        threshold = liquidation_threshold or self.liquidation_threshold
        if debt <= 0:
            return float('inf')
        return (collateral_value * threshold) / debt

    def calculate_liquidation_price(
        self, debt: float, collateral_units: float,
        liquidation_threshold: Optional[float] = None,
    ) -> float:
        threshold = liquidation_threshold or self.liquidation_threshold
        if collateral_units <= 0 or threshold <= 0:
            return float('inf')
        return debt / (collateral_units * threshold)

    def assess_loan_risk(
        self,
        loan_id: int,
        debt: float,
        collateral_value: float,
        liquidation_threshold: Optional[float] = None,
    ) -> LoanRiskMetrics:
        threshold = liquidation_threshold or self.liquidation_threshold
        ltv = self.calculate_ltv(debt, collateral_value)
        hf = self.calculate_health_factor(collateral_value, debt, threshold)
        liq_price = self.calculate_liquidation_price(debt, 1.0, threshold)

        distance = (hf - self.min_health_factor) / self.min_health_factor if hf != float('inf') else float('inf')

        if hf == float('inf'):
            liq_prob = 0.0
        else:
            x = -(hf - 1.0) * 10
            liq_prob = 1 / (1 + math.exp(-x))

        if hf == float('inf') or hf > 2.0:
            risk_tier = "safe"
        elif hf > 1.5:
            risk_tier = "low"
        elif hf > self.warning_health_factor:
            risk_tier = "medium"
        elif hf > self.min_health_factor:
            risk_tier = "high"
        else:
            risk_tier = "critical"

        return LoanRiskMetrics(
            loan_id=loan_id,
            ltv_ratio=round(ltv, 4),
            health_factor=round(hf, 4) if hf != float('inf') else 999.0,
            liquidation_price=round(liq_price, 2),
            distance_to_liquidation=round(distance, 4) if distance != float('inf') else 999.0,
            liquidation_probability=round(liq_prob, 4),
            risk_tier=risk_tier,
            is_healthy=hf > self.min_health_factor,
        )

    def assess_protocol_risk(
        self,
        loans: List[Dict],
    ) -> ProtocolRiskMetrics:
        if not loans:
            return ProtocolRiskMetrics(
                weighted_avg_ltv=0.0, weighted_avg_health_factor=0.0,
                concentration_risk=0.0, largest_position_pct=0.0,
                at_risk_loans_count=0, at_risk_value=0.0,
                expected_loss=0.0, risk_index=0.0,
                protocol_health_score=100.0,
            )

        total_debt = sum(l.get("debt", 0) for l in loans)
        total_collateral = sum(l.get("collateral_value", 0) for l in loans)

        w_ltv = total_debt / total_collateral if total_collateral > 0 else 0.0

        health_factors = []
        at_risk_count = 0
        at_risk_value = 0.0
        expected_loss = 0.0
        collateral_values = []

        for loan in loans:
            debt = loan.get("debt", 0)
            cv = loan.get("collateral_value", 0)
            hf = self.calculate_health_factor(cv, debt)

            if hf != float('inf'):
                health_factors.append(hf)

            if hf < self.warning_health_factor:
                at_risk_count += 1
                at_risk_value += debt
                x = -(hf - 1.0) * 10
                prob = 1 / (1 + math.exp(-x)) if hf != float('inf') else 0.0
                lgd = max(0, debt - cv * 0.8)
                expected_loss += prob * lgd

            collateral_values.append(cv)

        w_hf = np.mean(health_factors) if health_factors else 999.0

        if total_collateral > 0:
            shares = [cv / total_collateral for cv in collateral_values]
            concentration = sum(s ** 2 for s in shares)
        else:
            concentration = 0.0

        largest_pct = max(collateral_values) / total_collateral * 100 if total_collateral > 0 else 0.0

        risk_factors = []
        risk_factors.append(min(100, w_ltv * 100))
        risk_factors.append(min(100, (1 / w_hf) * 100) if w_hf > 0 else 100)
        risk_factors.append(min(100, at_risk_count / max(len(loans), 1) * 200))
        risk_factors.append(min(100, concentration * 200))
        risk_index = np.mean(risk_factors)

        health_score = max(0, 100 - risk_index)

        return ProtocolRiskMetrics(
            weighted_avg_ltv=round(w_ltv, 4),
            weighted_avg_health_factor=round(float(w_hf), 4),
            concentration_risk=round(concentration, 4),
            largest_position_pct=round(largest_pct, 2),
            at_risk_loans_count=at_risk_count,
            at_risk_value=round(at_risk_value, 2),
            expected_loss=round(expected_loss, 2),
            risk_index=round(float(risk_index), 2),
            protocol_health_score=round(float(health_score), 2),
        )
