import math
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class AuctionState:
    auction_id: int
    loan_id: int
    asset_id: int
    start_price: float
    current_price: float
    reserve_price: float
    decay_rate: float
    duration_ticks: int
    elapsed_ticks: int = 0
    is_active: bool = True
    is_settled: bool = False
    buyer_address: Optional[str] = None
    settled_price: Optional[float] = None

class AuctionEngine:
    def __init__(self, decay_type: str = "linear"):
        self.decay_type = decay_type
        self.active_auctions: Dict[int, AuctionState] = {}

    def create_auction(
        self,
        auction_id: int,
        loan_id: int,
        asset_id: int,
        start_price: float,
        reserve_price: float,
        duration_ticks: int = 360,
    ) -> AuctionState:
        if start_price <= reserve_price:
            start_price = reserve_price * 1.3

        decay_rate = (start_price - reserve_price) / max(duration_ticks, 1)

        state = AuctionState(
            auction_id=auction_id,
            loan_id=loan_id,
            asset_id=asset_id,
            start_price=start_price,
            current_price=start_price,
            reserve_price=reserve_price,
            decay_rate=decay_rate,
            duration_ticks=duration_ticks,
        )
        self.active_auctions[auction_id] = state
        return state

    def tick(self) -> Dict[int, float]:
        results = {}
        expired = []

        for aid, state in self.active_auctions.items():
            if not state.is_active:
                continue

            state.elapsed_ticks += 1

            if self.decay_type == "exponential":
                lam = -math.log(state.reserve_price / state.start_price) / state.duration_ticks
                state.current_price = state.start_price * math.exp(-lam * state.elapsed_ticks)
            else:
                state.current_price = state.start_price - state.decay_rate * state.elapsed_ticks

            state.current_price = max(state.current_price, state.reserve_price)

            if state.elapsed_ticks >= state.duration_ticks:
                expired.append(aid)

            results[aid] = round(state.current_price, 2)

        for aid in expired:
            self.active_auctions[aid].is_active = False

        return results

    def buy(
        self,
        auction_id: int,
        buyer_address: str,
        max_price: float,
    ) -> Optional[Dict]:
        state = self.active_auctions.get(auction_id)
        if not state or not state.is_active:
            return None

        if max_price < state.current_price:
            return None

        state.settled_price = state.current_price
        state.buyer_address = buyer_address
        state.is_active = False
        state.is_settled = True

        return {
            "auction_id": auction_id,
            "settled_price": round(state.current_price, 2),
            "buyer_address": buyer_address,
            "asset_id": state.asset_id,
            "loan_id": state.loan_id,
            "elapsed_ticks": state.elapsed_ticks,
            "discount_pct": round(
                (1 - state.current_price / state.start_price) * 100, 2
            ),
        }

    def cancel(self, auction_id: int) -> bool:
        state = self.active_auctions.get(auction_id)
        if state and state.is_active:
            state.is_active = False
            return True
        return False

    def get_auction(self, auction_id: int) -> Optional[AuctionState]:
        return self.active_auctions.get(auction_id)

    def get_active_auctions(self) -> list:
        return [s for s in self.active_auctions.values() if s.is_active]

    def get_price(self, auction_id: int) -> float:
        state = self.active_auctions.get(auction_id)
        return state.current_price if state else 0.0

    def reset(self):
        self.active_auctions.clear()
