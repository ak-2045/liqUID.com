

import httpx
import os
from typing import Dict, List, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


class APIClient:
    

    @staticmethod
    def _get(url: str, params: Optional[Dict] = None) -> Any:
        with httpx.Client(base_url=BACKEND_URL) as client:
            res = client.get(url, params=params, timeout=10.0)
            res.raise_for_status()
            return res.json()

    @staticmethod
    def _post(url: str, json_data: Optional[Dict] = None) -> Any:
        with httpx.Client(base_url=BACKEND_URL) as client:
            res = client.post(url, json=json_data, timeout=10.0)
            res.raise_for_status()
            return res.json()

    
    @classmethod
    def register_asset(cls, data: Dict) -> Dict:
        return cls._post("/assets/", data)

    @classmethod
    def list_assets(cls, owner: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        return cls._get("/assets/", {"owner": owner, "status": status})

    @classmethod
    def get_asset(cls, asset_id: int) -> Dict:
        return cls._get(f"/assets/{asset_id}")

    @classmethod
    def tokenize_asset(cls, asset_id: int) -> Dict:
        return cls._post("/assets/tokenize", {"asset_id": asset_id})

    
    @classmethod
    def borrow(cls, data: Dict) -> Dict:
        return cls._post("/loans/", data)

    @classmethod
    def list_loans(cls, status: Optional[str] = None) -> List[Dict]:
        return cls._get("/loans/", {"status": status})

    @classmethod
    def get_loan(cls, loan_id: int) -> Dict:
        return cls._get(f"/loans/{loan_id}")

    @classmethod
    def get_loan_health(cls, loan_id: int) -> Dict:
        return cls._get(f"/loans/{loan_id}/health")

    @classmethod
    def repay_loan(cls, loan_id: int, amount: float) -> Dict:
        return cls._post("/loans/repay", {"loan_id": loan_id, "amount": amount})

    
    @classmethod
    def update_oracle_price(cls, asset_id: int, price: float, model: str = "manual") -> Dict:
        return cls._post("/oracle/update", {"asset_id": asset_id, "price": price, "model": model})

    @classmethod
    def configure_oracle(cls, data: Dict) -> Dict:
        return cls._post("/oracle/config", data)

    @classmethod
    def get_price_history(cls, asset_id: int, limit: int = 100) -> List[Dict]:
        return cls._get(f"/oracle/history/{asset_id}", {"limit": limit})

    
    @classmethod
    def list_auctions(cls, status: Optional[str] = None) -> List[Dict]:
        return cls._get("/auctions/", {"status": status})

    @classmethod
    def buy_auction(cls, auction_id: int, buyer_address: str, max_price: float) -> Dict:
        return cls._post("/auctions/buy", {"auction_id": auction_id, "buyer_address": buyer_address, "max_price": max_price})

    
    @classmethod
    def start_simulation(cls, data: Dict) -> Dict:
        return cls._post("/simulation/start", data)

    @classmethod
    def control_simulation(cls, action: str, params: Optional[Dict] = None) -> Dict:
        return cls._post("/simulation/control", {"action": action, "params": params})

    
    @classmethod
    def get_analytics_summary(cls) -> Dict:
        return cls._get("/analytics/summary")

    @classmethod
    def get_collateral_distribution(cls) -> List[Dict]:
        return cls._get("/analytics/collateral-distribution")

    @classmethod
    def get_borrower_segmentation(cls) -> List[Dict]:
        return cls._get("/analytics/borrower-segmentation")

    @classmethod
    def get_oracle_trends(cls, limit: int = 500) -> List[Dict]:
        return cls._get("/analytics/oracle-trends", {"limit": limit})

    @classmethod
    def get_risk_breakdown(cls) -> Dict[str, int]:
        return cls._get("/analytics/risk-breakdown")

    
    @classmethod
    def update_protocol_parameters(cls, default_interest_rate: float, max_ltv_ratio: float, liquidation_threshold: float) -> Dict:
        params = f"?default_interest_rate={default_interest_rate}&max_ltv_ratio={max_ltv_ratio}&liquidation_threshold={liquidation_threshold}"
        return cls._post(f"/admin/parameters{params}")

    @classmethod
    def cancel_auction(cls, auction_id: int) -> Dict:
        return cls._post(f"/admin/auctions/{auction_id}/cancel")
