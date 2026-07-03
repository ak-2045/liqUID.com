from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = Field(default="liqUID.com", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    frontend_host: str = Field(default="127.0.0.1", alias="FRONTEND_HOST")
    frontend_port: int = Field(default=8501, alias="FRONTEND_PORT")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/liquid.db",
        alias="DATABASE_URL",
    )

    blockchain_rpc_url: str = Field(
        default="http://127.0.0.1:8545", alias="BLOCKCHAIN_RPC_URL"
    )
    chain_id: int = Field(default=31337, alias="CHAIN_ID")
    deployer_private_key: str = Field(
        default="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        alias="DEPLOYER_PRIVATE_KEY",
    )

    pinata_api_key: Optional[str] = Field(default=None, alias="PINATA_API_KEY")
    pinata_secret_key: Optional[str] = Field(default=None, alias="PINATA_SECRET_KEY")
    ipfs_gateway: str = Field(
        default="https://gateway.pinata.cloud/ipfs/", alias="IPFS_GATEWAY"
    )

    default_interest_rate: float = Field(
        default=0.08, alias="DEFAULT_INTEREST_RATE"
    )
    max_ltv_ratio: float = Field(default=0.75, alias="MAX_LTV_RATIO")
    liquidation_threshold: float = Field(
        default=0.85, alias="LIQUIDATION_THRESHOLD"
    )
    liquidation_penalty: float = Field(
        default=0.05, alias="LIQUIDATION_PENALTY"
    )
    auction_duration_seconds: int = Field(
        default=21600, alias="AUCTION_DURATION_SECONDS"
    )
    auction_premium_multiplier: float = Field(
        default=1.3, alias="AUCTION_PREMIUM_MULTIPLIER"
    )
    min_health_factor: float = Field(default=1.0, alias="MIN_HEALTH_FACTOR")
    protocol_fee_rate: float = Field(default=0.02, alias="PROTOCOL_FEE_RATE")

    default_simulation_speed: int = Field(
        default=10, alias="DEFAULT_SIMULATION_SPEED"
    )
    max_simulation_loans: int = Field(
        default=5000, alias="MAX_SIMULATION_LOANS"
    )
    oracle_update_interval_ms: int = Field(
        default=1000, alias="ORACLE_UPDATE_INTERVAL_MS"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "populate_by_name": True,
    }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
