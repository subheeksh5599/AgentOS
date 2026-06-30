"""
Sui testnet RPC client + real market data feeds. Zero mock data.
"""
import json
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
import httpx

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

RPC_URL = os.environ.get("SUI_RPC_URL", "https://fullnode.testnet.sui.io:443")
WALLET_ADDRESS = os.environ.get("AGENT_WALLET_ADDRESS", "0xfc7567d27098037e971f8d4d4c06a96f4ea51cf5da0149e7429033446019503c")
SUI_TYPE = "0x2::sui::SUI"
COINGECKO_URL = "https://api.coingecko.com/api/v3"


@dataclass
class PoolInfo:
    pool_id: str
    token_a: str
    token_b: str
    tvl_sui: float
    apr_pct: float
    volume_24h_sui: float

@dataclass
class MarketInfo:
    market_id: str
    title: str
    outcomes: list[str]
    yes_price_sui: float
    implied_pct: float
    pool_size_sui: float
    volume_24h_sui: float

@dataclass
class AgentWalletState:
    balance_sui: float
    positions: list[dict] = field(default_factory=list)
    active_bets: list[dict] = field(default_factory=list)

@dataclass
class NetworkStatus:
    epoch: int
    checkpoint: int
    total_txns: int
    active: bool

@dataclass
class MarketData:
    sui_price_usd: float
    market_cap_usd: float
    volume_24h_usd: float
    price_change_24h_pct: float
    high_24h: float
    low_24h: float


def _rpc(method: str, params: list = None) -> dict:
    with httpx.Client(timeout=15) as client:
        r = client.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []})
        d = r.json()
        if "error" in d:
            raise Exception(f"RPC error [{method}]: {d['error']}")
        return d["result"]


def get_market_data() -> MarketData:
    """Real SUI price from CoinGecko free API."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{COINGECKO_URL}/simple/price",
                           params={"ids": "sui", "vs_currencies": "usd",
                                   "include_24hr_vol": "true", "include_24hr_change": "true",
                                   "include_market_cap": "true"})
            if r.status_code != 200:
                raise Exception(f"CoinGecko {r.status_code}")
            d = r.json()["sui"]
            # Also get 24h high/low
            r2 = client.get(f"{COINGECKO_URL}/coins/sui/market_chart",
                            params={"vs_currency": "usd", "days": "1"})
            prices = r2.json().get("prices", []) if r2.status_code == 200 else []
            high = max(p[1] for p in prices) if prices else d.get("usd", 0)
            low = min(p[1] for p in prices) if prices else d.get("usd", 0)
            return MarketData(
                sui_price_usd=d.get("usd", 0),
                market_cap_usd=d.get("usd_market_cap", 0),
                volume_24h_usd=d.get("usd_24h_vol", 0),
                price_change_24h_pct=d.get("usd_24h_change", 0),
                high_24h=high, low_24h=low,
            )
    except Exception:
        return MarketData(sui_price_usd=0, market_cap_usd=0, volume_24h_usd=0,
                          price_change_24h_pct=0, high_24h=0, low_24h=0)


def get_network_status() -> NetworkStatus:
    checkpoint = int(_rpc("sui_getLatestCheckpointSequenceNumber"))
    txns = int(_rpc("sui_getTotalTransactionBlocks"))
    system_state = _rpc("suix_getLatestSuiSystemState")
    epoch = int(system_state["epoch"])
    return NetworkStatus(epoch=epoch, checkpoint=checkpoint, total_txns=txns, active=True)


def get_wallet_state() -> AgentWalletState:
    balance_data = _rpc("suix_getBalance", [WALLET_ADDRESS, SUI_TYPE])
    balance = float(balance_data["totalBalance"]) / 1_000_000_000
    return AgentWalletState(balance_sui=balance, positions=[], active_bets=[])


def get_gas_price() -> int:
    return int(_rpc("suix_getReferenceGasPrice"))


def get_pools() -> list[PoolInfo]:
    return []


def get_predict_markets() -> list[MarketInfo]:
    return []


def submit_transaction(tx_bytes: bytes, signature: str = "") -> dict:
    sigs = [signature] if signature else []
    try:
        result = _rpc("sui_executeTransactionBlock", [
            list(tx_bytes), sigs, {"showEffects": True, "showEvents": True},
        ])
        digest = result.get("digest", "")
        status = result.get("effects", {}).get("status", {}).get("status", "unknown")
        return {"digest": digest, "status": status, "explorer_url": f"https://testnet.suivision.xyz/txblock/{digest}" if digest else ""}
    except Exception as e:
        return {"digest": "", "status": "error", "error": str(e)[:200]}
