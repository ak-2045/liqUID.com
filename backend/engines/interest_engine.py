import math
from dataclasses import dataclass
from typing import List

@dataclass
class AmortizationEntry:
    period: int
    payment: float
    principal_portion: float
    interest_portion: float
    remaining_balance: float

class InterestEngine:
    @staticmethod
    def compound_interest(
        principal: float,
        annual_rate: float,
        periods_per_year: int = 365,
        elapsed_periods: int = 1,
    ) -> float:
        if annual_rate <= 0 or principal <= 0:
            return principal
        rate_per_period = annual_rate / periods_per_year
        return principal * (1 + rate_per_period) ** elapsed_periods

    @staticmethod
    def accrued_interest(
        principal: float,
        annual_rate: float,
        elapsed_seconds: float,
    ) -> float:
        if annual_rate <= 0 or principal <= 0 or elapsed_seconds <= 0:
            return 0.0
        seconds_per_year = 365.25 * 24 * 3600
        t = elapsed_seconds / seconds_per_year
        total = principal * math.exp(annual_rate * t)
        return total - principal

    @staticmethod
    def per_tick_interest(
        principal: float,
        annual_rate: float,
        ticks_per_year: int = 8760,
    ) -> float:
        if annual_rate <= 0 or principal <= 0:
            return 0.0
        rate_per_tick = annual_rate / ticks_per_year
        return principal * rate_per_tick

    @staticmethod
    def amortization_schedule(
        principal: float,
        annual_rate: float,
        num_payments: int,
    ) -> List[AmortizationEntry]:
        if annual_rate <= 0 or principal <= 0 or num_payments <= 0:
            return []

        monthly_rate = annual_rate / 12
        payment = principal * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / (
            (1 + monthly_rate) ** num_payments - 1
        )

        schedule = []
        balance = principal

        for period in range(1, num_payments + 1):
            interest_portion = balance * monthly_rate
            principal_portion = payment - interest_portion
            balance -= principal_portion
            balance = max(0, balance)

            schedule.append(AmortizationEntry(
                period=period,
                payment=round(payment, 2),
                principal_portion=round(principal_portion, 2),
                interest_portion=round(interest_portion, 2),
                remaining_balance=round(balance, 2),
            ))

        return schedule

    @staticmethod
    def effective_annual_rate(nominal_rate: float, compounds_per_year: int = 12) -> float:
        if nominal_rate <= 0:
            return 0.0
        return (1 + nominal_rate / compounds_per_year) ** compounds_per_year - 1

    @staticmethod
    def total_debt_at_tick(
        principal: float,
        annual_rate: float,
        tick: int,
        ticks_per_year: int = 8760,
        payments_made: float = 0.0,
    ) -> float:
        if principal <= 0:
            return 0.0
        rate_per_tick = annual_rate / ticks_per_year
        accrued = principal * ((1 + rate_per_tick) ** tick - 1)
        total = principal + accrued - payments_made
        return max(0, total)
