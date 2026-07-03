

import pytest
import math
from backend.engines.interest_engine import InterestEngine
from backend.engines.risk_engine import RiskEngine
from backend.engines.liquidation_engine import LiquidationEngine


def test_interest_compounding():
    
    principal = 10000.0
    rate = 0.08
    
    
    total_expected = principal * (1 + rate/365) ** 365
    total_calculated = InterestEngine.compound_interest(principal, rate, periods_per_year=365, elapsed_periods=365)
    
    assert math.isclose(total_calculated, total_expected, rel_tol=1e-5)


def test_per_second_interest_accrual():
    
    principal = 10000.0
    rate = 0.08
    elapsed_seconds = 365.25 * 24 * 3600  
    
    calculated_interest = InterestEngine.accrued_interest(principal, rate, elapsed_seconds)
    total = principal + calculated_interest
    
    
    expected_total = principal * math.exp(rate * 1)
    
    assert math.isclose(total, expected_total, rel_tol=1e-5)


def test_ltv_calculations():
    
    risk = RiskEngine()
    debt = 50000.0
    collateral = 100000.0
    
    ltv = risk.calculate_ltv(debt, collateral)
    assert ltv == 0.50


def test_health_factor_scoring():
    
    risk = RiskEngine(liquidation_threshold=0.85)
    
    
    hf_healthy = risk.calculate_health_factor(100000.0, 50000.0) 
    assert hf_healthy == 1.70
    
    
    hf_default = risk.calculate_health_factor(100000.0, 90000.0) 
    assert hf_default < 1.0


def test_liquidation_triggers():
    
    liq_engine = LiquidationEngine(min_health_factor=1.0)
    
    active_loans = [
        {"loan_id": 1, "debt": 50000.0, "collateral_value": 100000.0, "liquidation_threshold": 0.85}, 
        {"loan_id": 2, "debt": 90000.0, "collateral_value": 100000.0, "liquidation_threshold": 0.85}, 
    ]
    
    events = liq_engine.scan_loans(active_loans)
    
    assert len(events) == 1
    assert events[0].loan_id == 2
