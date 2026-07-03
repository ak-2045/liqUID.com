import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import math

@dataclass
class OracleConfig:
    price_model: str = "gbm"
    volatility: float = 0.02
    drift: float = 0.0001
    crash_probability: float = 0.005
    crash_magnitude: float = 0.35
    recovery_rate: float = 0.02
    seasonal_amplitude: float = 0.05
    seasonal_period: int = 365
    cycle_period: int = 1000
    cycle_amplitude: float = 0.15
    min_price_ratio: float = 0.05
    max_price_ratio: float = 5.0

ASSET_VOLATILITY: Dict[str, float] = {
    "real_estate": 0.008,
    "gold": 0.012,
    "vehicle": 0.015,
    "invoice": 0.005,
    "land": 0.006,
    "machinery": 0.010,
    "artwork": 0.025,
    "warehouse_receipt": 0.007,
    "bond": 0.004,
}

@dataclass
class AssetPriceState:
    asset_id: int
    initial_price: float
    current_price: float
    asset_type: str = "real_estate"
    in_crash: bool = False
    crash_floor: float = 0.0
    recovery_target: float = 0.0
    ticks_in_crash: int = 0

class OracleEngine:
    def __init__(self, config: Optional[OracleConfig] = None):
        self.config = config or OracleConfig()
        self.asset_states: Dict[int, AssetPriceState] = {}
        self.tick = 0
        self._rng = np.random.default_rng(42)
        self._manual_overrides: Dict[int, float] = {}

    def register_asset(self, asset_id: int, initial_price: float, asset_type: str = "real_estate"):
        self.asset_states[asset_id] = AssetPriceState(
            asset_id=asset_id,
            initial_price=initial_price,
            current_price=initial_price,
            asset_type=asset_type,
        )

    def set_manual_price(self, asset_id: int, price: float):
        self._manual_overrides[asset_id] = price

    def clear_manual_price(self, asset_id: int):
        self._manual_overrides.pop(asset_id, None)

    def trigger_crash(self, magnitude: Optional[float] = None):
        mag = magnitude or self.config.crash_magnitude
        for state in self.asset_states.values():
            state.in_crash = True
            state.crash_floor = state.current_price * (1 - mag)
            state.recovery_target = state.current_price
            state.ticks_in_crash = 0

    def trigger_recovery(self):
        for state in self.asset_states.values():
            if state.in_crash:
                state.in_crash = False
                state.recovery_target = state.initial_price

    def update_prices(self) -> Dict[int, Tuple[float, float, float]]:
        self.tick += 1
        results = {}

        for asset_id, state in self.asset_states.items():
            old_price = state.current_price

            if asset_id in self._manual_overrides:
                new_price = self._manual_overrides[asset_id]
                self._manual_overrides.pop(asset_id)
            elif state.in_crash:
                new_price = self._crash_price(state)
            else:
                new_price = self._model_price(state)

            min_p = state.initial_price * self.config.min_price_ratio
            max_p = state.initial_price * self.config.max_price_ratio
            new_price = max(min_p, min(max_p, new_price))

            state.current_price = new_price
            delta_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
            results[asset_id] = (new_price, old_price, delta_pct)

        return results

    def _model_price(self, state: AssetPriceState) -> float:
        model = self.config.price_model
        vol = ASSET_VOLATILITY.get(state.asset_type, self.config.volatility)

        if self._rng.random() < self.config.crash_probability:
            state.in_crash = True
            mag = self.config.crash_magnitude * (0.5 + self._rng.random() * 0.5)
            state.crash_floor = state.current_price * (1 - mag)
            state.recovery_target = state.current_price
            state.ticks_in_crash = 0
            return state.crash_floor

        if model == "gbm":
            return self._gbm(state.current_price, vol)
        elif model == "random_walk":
            return self._random_walk(state.current_price, vol)
        elif model == "seasonal":
            return self._seasonal(state)
        elif model == "economic_cycle":
            return self._economic_cycle(state)
        else:
            return self._gbm(state.current_price, vol)

    def _gbm(self, price: float, volatility: float) -> float:
        dt = 1.0
        drift = self.config.drift
        dW = self._rng.normal(0, math.sqrt(dt))
        return price * math.exp((drift - 0.5 * volatility**2) * dt + volatility * dW)

    def _random_walk(self, price: float, volatility: float) -> float:
        step = self._rng.normal(0, price * volatility)
        return price + step

    def _seasonal(self, state: AssetPriceState) -> float:
        base_price = self._gbm(state.current_price, ASSET_VOLATILITY.get(state.asset_type, 0.01))
        seasonal_factor = 1 + self.config.seasonal_amplitude * math.sin(
            2 * math.pi * self.tick / self.config.seasonal_period
        )
        return base_price * seasonal_factor

    def _economic_cycle(self, state: AssetPriceState) -> float:
        base_price = self._gbm(state.current_price, ASSET_VOLATILITY.get(state.asset_type, 0.01))
        cycle_phase = (self.tick % self.config.cycle_period) / self.config.cycle_period
        cycle_factor = 1 + self.config.cycle_amplitude * math.sin(2 * math.pi * cycle_phase)
        return base_price * cycle_factor

    def _crash_price(self, state: AssetPriceState) -> float:
        state.ticks_in_crash += 1

        if state.ticks_in_crash < 5:
            decline = 1 - (self.config.crash_magnitude / 5)
            return state.current_price * decline
        else:
            recovery_speed = self.config.recovery_rate
            target = state.recovery_target
            gap = target - state.current_price
            noise = self._rng.normal(0, state.current_price * 0.005)
            new_price = state.current_price + gap * recovery_speed + noise

            if new_price >= target * 0.95:
                state.in_crash = False

            return new_price

    def get_price(self, asset_id: int) -> float:
        state = self.asset_states.get(asset_id)
        return state.current_price if state else 0.0

    def get_all_prices(self) -> Dict[int, float]:
        return {aid: state.current_price for aid, state in self.asset_states.items()}

    def get_volatility(self, asset_id: int) -> float:
        state = self.asset_states.get(asset_id)
        if not state:
            return 0.0
        return ASSET_VOLATILITY.get(state.asset_type, self.config.volatility)

    def reset(self):
        for state in self.asset_states.values():
            state.current_price = state.initial_price
            state.in_crash = False
            state.ticks_in_crash = 0
        self.tick = 0
        self._manual_overrides.clear()
        self._rng = np.random.default_rng(42)
