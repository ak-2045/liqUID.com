import asyncio
import hashlib
import math
import time
import threading
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.engines.oracle_engine import OracleEngine, OracleConfig
from backend.engines.interest_engine import InterestEngine
from backend.engines.risk_engine import RiskEngine
from backend.engines.liquidation_engine import LiquidationEngine, LiquidationEvent
from backend.engines.auction_engine import AuctionEngine

ASSET_TYPES = [
    "real_estate", "gold", "vehicle", "invoice", "land",
    "machinery", "artwork", "warehouse_receipt", "bond",
]

ASSET_NAMES = {
    "real_estate": ["Manhattan Condo", "Miami Beach Villa", "Tokyo Apartment", "London Flat", "Dubai Tower Unit", "SF Loft", "Paris Studio", "Singapore Penthouse"],
    "gold": ["Gold Bar 1kg", "Gold Coin Collection", "Gold Bullion 500g", "Gold Reserve Certificate", "Swiss Gold Vault"],
    "vehicle": ["Tesla Model S", "Porsche 911", "Ferrari Roma", "BMW i7", "Mercedes EQS", "Rolls Royce Ghost"],
    "invoice": ["Trade Invoice #A1", "Corporate Invoice #B2", "Export Invoice #C3", "Supply Chain Invoice"],
    "land": ["Texas Ranch 50ac", "Montana Farmland", "California Vineyard", "Florida Waterfront Lot"],
    "machinery": ["CNC Machine", "Industrial Robot Arm", "Mining Equipment", "Construction Crane", "3D Printer Farm"],
    "artwork": ["Banksy Print", "Warhol Silkscreen", "Digital Art NFT", "Sculpture Collection", "Renaissance Painting"],
    "warehouse_receipt": ["Coffee 1000 bags", "Wheat Silo #7", "Copper Reserve", "Lithium Storage", "Cocoa Warehouse"],
    "bond": ["US Treasury 10Y", "Corp Bond AAA", "Municipal Bond", "Green Bond", "Convertible Note"],
}

VALUE_RANGES = {
    "real_estate": (200000, 5000000),
    "gold": (50000, 500000),
    "vehicle": (30000, 500000),
    "invoice": (10000, 200000),
    "land": (100000, 2000000),
    "machinery": (50000, 1000000),
    "artwork": (20000, 2000000),
    "warehouse_receipt": (25000, 500000),
    "bond": (50000, 1000000),
}

BORROWER_NAMES = [
    "Alpha Capital", "Meridian Holdings", "Apex Ventures", "Titan Group",
    "Horizon Partners", "Summit Investments", "Nexus Capital", "Vanguard LLC",
    "Pinnacle Fund", "Orion Trading", "Atlas Enterprises", "Zenith Corp",
    "Sterling Assets", "Cobalt Finance", "Ironclad Ventures", "Quantum Fund",
    "Platinum Investments", "Eclipse Capital", "Nova Holdings", "Prime Assets",
]

@dataclass
class SimLoan:
    loan_id: int
    borrower_id: int
    borrower_name: str
    asset_id: int
    asset_name: str
    asset_type: str
    principal: float
    interest_rate: float
    accrued_interest: float = 0.0
    total_debt: float = 0.0
    total_repaid: float = 0.0
    collateral_value: float = 0.0
    initial_collateral: float = 0.0
    ltv_ratio: float = 0.0
    health_factor: float = 999.0
    status: str = "active"
    auto_repay: bool = False
    repay_probability: float = 0.3
    created_tick: int = 0

@dataclass
class SimAuction:
    auction_id: int
    loan_id: int
    asset_id: int
    start_price: float
    current_price: float
    reserve_price: float
    elapsed_ticks: int = 0
    duration_ticks: int = 360
    status: str = "active"

@dataclass
class SimSnapshot:
    tick: int
    timestamp: float
    total_value_locked: float = 0.0
    total_borrowed: float = 0.0
    total_repaid: float = 0.0
    total_liquidated: float = 0.0
    total_fees: float = 0.0
    active_loans: int = 0
    defaulted_loans: int = 0
    active_auctions: int = 0
    avg_ltv: float = 0.0
    avg_health_factor: float = 0.0
    avg_interest_rate: float = 0.0
    recovered_capital: float = 0.0
    protocol_health_score: float = 100.0
    risk_index: float = 0.0

class SimulationEngine:
    def __init__(self):
        self.oracle = OracleEngine()
        self.interest = InterestEngine()
        self.risk = RiskEngine()
        self.liquidation = LiquidationEngine(risk_engine=self.risk)
        self.auction = AuctionEngine()

        self.loans: Dict[int, SimLoan] = {}
        self.auctions: Dict[int, SimAuction] = {}
        self.borrowers: Dict[int, Dict] = {}
        self.assets: Dict[int, Dict] = {}
        self.snapshots: List[SimSnapshot] = []
        self.events: List[Dict] = []

        self.tick = 0
        self.is_running = False
        self.is_paused = False
        self.speed = 10
        self._next_loan_id = 1
        self._next_auction_id = 1
        self._next_asset_id = 1
        self._next_borrower_id = 1
        self._rng = np.random.default_rng(int(time.time()))
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

        self.total_repaid = 0.0
        self.total_liquidated = 0.0
        self.total_fees = 0.0
        self.total_recovered = 0.0

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def generate_loans(
        self,
        count: int = 100,
        auto_repay_probability: float = 0.3,
    ):
        with self._lock:
            self._reset_state()
            borrower_count = min(count, len(BORROWER_NAMES))
            
            for i in range(count):
                asset_type = self._rng.choice(ASSET_TYPES)
                val_range = VALUE_RANGES[asset_type]
                valuation = float(self._rng.uniform(val_range[0], val_range[1]))
                
                names = ASSET_NAMES[asset_type]
                asset_name = names[i % len(names)]
                if i >= len(names):
                    asset_name = f"{asset_name} #{i}"

                asset_id = self._next_asset_id
                self._next_asset_id += 1
                
                self.oracle.register_asset(asset_id, valuation, asset_type)
                self.assets[asset_id] = {
                    "id": asset_id,
                    "name": asset_name,
                    "asset_type": asset_type,
                    "valuation": valuation,
                    "current_value": valuation,
                    "status": "collateralized",
                    "owner_address": f"0x{hashlib.md5(f'owner_{i}'.encode()).hexdigest()[:40]}",
                }

                borrower_idx = i % borrower_count
                if borrower_idx + 1 not in self.borrowers:
                    b_id = borrower_idx + 1
                    self.borrowers[b_id] = {
                        "id": b_id,
                        "name": BORROWER_NAMES[borrower_idx],
                        "address": f"0x{hashlib.md5(f'borrower_{borrower_idx}'.encode()).hexdigest()[:40]}",
                        "credit_score": float(self._rng.uniform(550, 850)),
                        "active_loans": 0,
                        "total_borrowed": 0.0,
                    }
                    self._next_borrower_id = max(self._next_borrower_id, b_id + 1)
                borrower_id = borrower_idx + 1

                ltv = float(self._rng.uniform(0.3, 0.75))
                principal = valuation * ltv
                interest_rate = float(self._rng.uniform(0.04, 0.15))
                auto_repay = float(self._rng.random()) < auto_repay_probability

                loan = SimLoan(
                    loan_id=self._next_loan_id,
                    borrower_id=borrower_id,
                    borrower_name=self.borrowers[borrower_id]["name"],
                    asset_id=asset_id,
                    asset_name=asset_name,
                    asset_type=asset_type,
                    principal=principal,
                    interest_rate=interest_rate,
                    total_debt=principal,
                    collateral_value=valuation,
                    initial_collateral=valuation,
                    ltv_ratio=ltv,
                    health_factor=self.risk.calculate_health_factor(valuation, principal),
                    auto_repay=auto_repay,
                    repay_probability=float(self._rng.uniform(0.01, 0.05)),
                    created_tick=0,
                )
                self.loans[self._next_loan_id] = loan
                self.borrowers[borrower_id]["active_loans"] += 1
                self.borrowers[borrower_id]["total_borrowed"] += principal
                self._next_loan_id += 1

    def _reset_state(self):
        self.loans.clear()
        self.auctions.clear()
        self.borrowers.clear()
        self.assets.clear()
        self.snapshots.clear()
        self.events.clear()
        self.oracle.reset()
        self.auction.reset()
        self.tick = 0
        self._next_loan_id = 1
        self._next_auction_id = 1
        self._next_asset_id = 1
        self._next_borrower_id = 1
        self.total_repaid = 0.0
        self.total_liquidated = 0.0
        self.total_fees = 0.0
        self.total_recovered = 0.0

    def step(self) -> SimSnapshot:
        with self._lock:
            self.tick += 1

            price_updates = self.oracle.update_prices()
            for asset_id, (new_price, old_price, delta) in price_updates.items():
                if asset_id in self.assets:
                    self.assets[asset_id]["current_value"] = new_price

            liquidation_candidates = []
            active_loans = [l for l in self.loans.values() if l.status == "active"]

            for loan in active_loans:
                if loan.asset_id in self.assets:
                    loan.collateral_value = self.assets[loan.asset_id]["current_value"]

                tick_interest = self.interest.per_tick_interest(
                    loan.total_debt, loan.interest_rate, ticks_per_year=8760
                )
                loan.accrued_interest += tick_interest
                loan.total_debt += tick_interest

                loan.ltv_ratio = self.risk.calculate_ltv(
                    loan.total_debt, loan.collateral_value
                )
                loan.health_factor = self.risk.calculate_health_factor(
                    loan.collateral_value, loan.total_debt
                )

                if loan.auto_repay and self._rng.random() < loan.repay_probability:
                    repay_amount = min(
                        loan.total_debt * float(self._rng.uniform(0.01, 0.05)),
                        loan.total_debt,
                    )
                    loan.total_debt -= repay_amount
                    loan.total_repaid += repay_amount
                    self.total_repaid += repay_amount

                    if loan.total_debt <= 0.01:
                        loan.status = "repaid"
                        loan.total_debt = 0
                        self._emit_event("loan_repaid", {"loan_id": loan.loan_id})

                if loan.health_factor < 1.0 and loan.status == "active":
                    liquidation_candidates.append(loan)

            for loan in liquidation_candidates:
                loan.status = "in_auction"
                self.total_liquidated += loan.total_debt

                start_price = loan.collateral_value * 1.3
                reserve_price = loan.total_debt * 0.8
                auction_id = self._next_auction_id
                self._next_auction_id += 1

                sim_auction = SimAuction(
                    auction_id=auction_id,
                    loan_id=loan.loan_id,
                    asset_id=loan.asset_id,
                    start_price=start_price,
                    current_price=start_price,
                    reserve_price=reserve_price,
                )
                self.auctions[auction_id] = sim_auction
                self.auction.create_auction(
                    auction_id, loan.loan_id, loan.asset_id,
                    start_price, reserve_price, 360,
                )

                if loan.asset_id in self.assets:
                    self.assets[loan.asset_id]["status"] = "in_auction"

                self._emit_event("liquidation", {
                    "loan_id": loan.loan_id,
                    "health_factor": loan.health_factor,
                    "debt": loan.total_debt,
                    "auction_id": auction_id,
                })

            auction_prices = self.auction.tick()
            for aid, price in auction_prices.items():
                if aid in self.auctions:
                    self.auctions[aid].current_price = price

            for aid, sa in list(self.auctions.items()):
                if sa.status != "active":
                    continue
                sa.elapsed_ticks += 1

                auction_state = self.auction.get_auction(aid)
                if auction_state and auction_state.is_active:
                    sa.current_price = auction_state.current_price
                    discount = 1 - sa.current_price / sa.start_price
                    buy_prob = min(0.05, discount * 0.15)
                    if self._rng.random() < buy_prob:
                        buyer = f"0x{hashlib.md5(f'buyer_{self.tick}_{aid}'.encode()).hexdigest()[:40]}"
                        result = self.auction.buy(aid, buyer, sa.current_price * 1.1)
                        if result:
                            sa.status = "sold"
                            settled = result["settled_price"]
                            loan = self.loans.get(sa.loan_id)
                            if loan:
                                fee = settled * 0.02
                                self.total_fees += fee
                                self.total_recovered += settled
                                loan.status = "liquidated"
                            if sa.asset_id in self.assets:
                                self.assets[sa.asset_id]["status"] = "sold"
                            self._emit_event("auction_sold", {
                                "auction_id": aid,
                                "price": settled,
                                "buyer": buyer,
                            })

                if sa.elapsed_ticks >= sa.duration_ticks and sa.status == "active":
                    sa.status = "expired"
                    loan = self.loans.get(sa.loan_id)
                    if loan:
                        loan.status = "defaulted"

            snapshot = self._create_snapshot()
            self.snapshots.append(snapshot)

            for cb in self._callbacks:
                try:
                    cb(snapshot)
                except Exception:
                    pass

            return snapshot

    def _create_snapshot(self) -> SimSnapshot:
        active = [l for l in self.loans.values() if l.status == "active"]
        defaulted = [l for l in self.loans.values() if l.status in ("defaulted", "liquidated", "in_auction")]
        active_auctions = [a for a in self.auctions.values() if a.status == "active"]

        tvl = sum(l.collateral_value for l in active)
        total_borrowed = sum(l.total_debt for l in active)
        avg_ltv = float(np.mean([l.ltv_ratio for l in active])) if active else 0.0
        avg_hf = float(np.mean([min(l.health_factor, 10) for l in active])) if active else 0.0
        avg_ir = float(np.mean([l.interest_rate for l in active])) if active else 0.0

        risk_metrics = self.risk.assess_protocol_risk([
            {"loan_id": l.loan_id, "debt": l.total_debt, "collateral_value": l.collateral_value}
            for l in active
        ])

        return SimSnapshot(
            tick=self.tick,
            timestamp=time.time(),
            total_value_locked=round(tvl, 2),
            total_borrowed=round(total_borrowed, 2),
            total_repaid=round(self.total_repaid, 2),
            total_liquidated=round(self.total_liquidated, 2),
            total_fees=round(self.total_fees, 2),
            active_loans=len(active),
            defaulted_loans=len(defaulted),
            active_auctions=len(active_auctions),
            avg_ltv=round(avg_ltv, 4),
            avg_health_factor=round(avg_hf, 4),
            avg_interest_rate=round(avg_ir, 4),
            recovered_capital=round(self.total_recovered, 2),
            protocol_health_score=risk_metrics.protocol_health_score,
            risk_index=risk_metrics.risk_index,
        )

    def _emit_event(self, event_type: str, data: Dict):
        self.events.append({
            "tick": self.tick,
            "type": event_type,
            "timestamp": time.time(),
            **data,
        })

    def start(self, speed: int = 10):
        if self.is_running:
            return
        self.speed = speed
        self.is_running = True
        self.is_paused = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def reset(self):
        self.stop()
        with self._lock:
            self._reset_state()

    def set_speed(self, speed: int):
        self.speed = max(1, min(100, speed))

    def _run_loop(self):
        while self.is_running:
            if not self.is_paused:
                self.step()
            interval = 1.0 / max(self.speed, 1)
            time.sleep(interval)

    def trigger_crash(self, magnitude: float = 0.35):
        self.oracle.trigger_crash(magnitude)
        self._emit_event("market_crash", {"magnitude": magnitude})

    def trigger_recovery(self):
        self.oracle.trigger_recovery()
        self._emit_event("market_recovery", {})

    def trigger_rate_hike(self, increase: float = 0.03):
        with self._lock:
            for loan in self.loans.values():
                if loan.status == "active":
                    loan.interest_rate += increase
            self._emit_event("rate_hike", {"increase": increase})

    def force_default(self, loan_id: int):
        with self._lock:
            loan = self.loans.get(loan_id)
            if loan and loan.status == "active":
                loan.health_factor = 0.5
                loan.collateral_value = loan.total_debt * 0.5

    def get_state(self) -> Dict:
        with self._lock:
            latest = self.snapshots[-1] if self.snapshots else SimSnapshot(tick=0, timestamp=time.time())
            return {
                "tick": self.tick,
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "speed": self.speed,
                "snapshot": {
                    "total_value_locked": latest.total_value_locked,
                    "total_borrowed": latest.total_borrowed,
                    "total_repaid": latest.total_repaid,
                    "total_liquidated": latest.total_liquidated,
                    "total_fees": latest.total_fees,
                    "active_loans": latest.active_loans,
                    "defaulted_loans": latest.defaulted_loans,
                    "active_auctions": latest.active_auctions,
                    "avg_ltv": latest.avg_ltv,
                    "avg_health_factor": latest.avg_health_factor,
                    "avg_interest_rate": latest.avg_interest_rate,
                    "recovered_capital": latest.recovered_capital,
                    "protocol_health_score": latest.protocol_health_score,
                    "risk_index": latest.risk_index,
                },
                "loans_count": len(self.loans),
                "recent_events": self.events[-20:] if self.events else [],
            }

    def get_loans_data(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "loan_id": l.loan_id,
                    "borrower": l.borrower_name,
                    "asset": l.asset_name,
                    "asset_type": l.asset_type,
                    "principal": round(l.principal, 2),
                    "total_debt": round(l.total_debt, 2),
                    "collateral_value": round(l.collateral_value, 2),
                    "ltv_ratio": round(l.ltv_ratio, 4),
                    "health_factor": round(min(l.health_factor, 99), 4),
                    "interest_rate": round(l.interest_rate, 4),
                    "status": l.status,
                    "accrued_interest": round(l.accrued_interest, 2),
                }
                for l in self.loans.values()
            ]

    def get_auctions_data(self) -> List[Dict]:
        with self._lock:
            results = []
            for a in self.auctions.values():
                loan = self.loans.get(a.loan_id)
                asset = self.assets.get(a.asset_id, {})
                results.append({
                    "auction_id": a.auction_id,
                    "loan_id": a.loan_id,
                    "asset_name": asset.get("name", "Unknown"),
                    "asset_type": asset.get("asset_type", "unknown"),
                    "start_price": round(a.start_price, 2),
                    "current_price": round(a.current_price, 2),
                    "reserve_price": round(a.reserve_price, 2),
                    "outstanding_debt": round(loan.total_debt if loan else 0, 2),
                    "elapsed_ticks": a.elapsed_ticks,
                    "duration_ticks": a.duration_ticks,
                    "progress_pct": round(a.elapsed_ticks / max(a.duration_ticks, 1) * 100, 1),
                    "discount_pct": round((1 - a.current_price / a.start_price) * 100, 1) if a.start_price > 0 else 0,
                    "status": a.status,
                })
            return results

    def get_snapshots_data(self, last_n: int = 500) -> List[Dict]:
        with self._lock:
            snaps = self.snapshots[-last_n:] if self.snapshots else []
            return [
                {
                    "tick": s.tick,
                    "tvl": s.total_value_locked,
                    "borrowed": s.total_borrowed,
                    "repaid": s.total_repaid,
                    "liquidated": s.total_liquidated,
                    "fees": s.total_fees,
                    "active_loans": s.active_loans,
                    "defaulted_loans": s.defaulted_loans,
                    "active_auctions": s.active_auctions,
                    "avg_ltv": s.avg_ltv,
                    "avg_hf": s.avg_health_factor,
                    "health_score": s.protocol_health_score,
                    "risk_index": s.risk_index,
                }
                for s in snaps
            ]

    def get_asset_distribution(self) -> Dict[str, float]:
        with self._lock:
            dist: Dict[str, float] = {}
            for loan in self.loans.values():
                if loan.status in ("active", "in_auction"):
                    dist[loan.asset_type] = dist.get(loan.asset_type, 0) + loan.collateral_value
            return dist

    def get_health_distribution(self) -> Dict[str, int]:
        with self._lock:
            buckets = {"critical": 0, "high": 0, "medium": 0, "low": 0, "safe": 0}
            for loan in self.loans.values():
                if loan.status != "active":
                    continue
                hf = loan.health_factor
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
