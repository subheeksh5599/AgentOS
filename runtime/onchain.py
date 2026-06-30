"""
On-chain transaction module — submits real TX via Sui CLI.
Uses `sui client` subprocess for signing (key in local keystore).
"""
import os
import re
import subprocess
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

PKG = os.environ.get("AGENTOS_PACKAGE_ID", "0x8be6a574ed9711fc0815e5821358eeb9fd0b269c1c5aa399338c6da786c8f9de")
WALLET = os.environ.get("AGENT_WALLET_ADDRESS", "0xfc7567d27098037e971f8d4d4c06a96f4ea51cf5da0149e7429033446019503c")
AGENTOS_DIR = os.environ.get("AGENTOS_DIR", os.path.expanduser("~/agentos"))

_TYPE_MAP = {"yield": "0", "trader": "1", "prediction": "2"}


def _sui(args: str, timeout: int = 60) -> tuple[int, str]:
    """Run a Sui CLI command. Returns (exit_code, stdout)."""
    cmd = f"sui {args}"
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        timeout=timeout, cwd=AGENTOS_DIR,
        env={**os.environ, "PATH": os.environ.get("PATH", "")},
    )
    return result.returncode, result.stdout


def _parse_digest(output: str) -> str:
    """Extract transaction digest from Sui CLI output."""
    m = re.search(r'Digest:\s*(\w{40,50})', output)
    return m.group(1) if m else ""


def factory_deploy(name: str, agent_type: str, guardrails: dict) -> dict:
    at = _TYPE_MAP.get(agent_type, "0")
    max_tx_mist = int(guardrails.get("max_tx_sui", guardrails.get("max_bet_sui", 100))) * 1_000_000_000
    daily_mist = int(guardrails.get("daily_spend_sui", 500)) * 1_000_000_000
    allowed_actions = 255
    safe_name = name.replace("'", "").replace('"', "").replace(" ", "_")[:32]

    cmd = (
        f'client call --package {PKG} --module agent_factory --function deploy '
        f'--args \'"{safe_name}"\' {at} \'"strategy"\' {max_tx_mist} {daily_mist} {allowed_actions} \'"[]"\' '
        f'--gas-budget 50000000'
    )

    try:
        code, out = _sui(cmd)
        digest = _parse_digest(out)

        wallet_obj, cap_obj, registry_obj = "", "", ""
        last_object_id = ""
        for line in out.split("\n"):
            oid_match = re.search(r'ObjectID:\s*(0x[a-f0-9]{64})', line)
            if oid_match:
                last_object_id = oid_match.group(1)
            if "AgentWalletCap" in line and last_object_id:
                cap_obj = last_object_id
            elif "AgentWallet" in line and "AgentWalletCap" not in line and last_object_id:
                wallet_obj = last_object_id
            elif "AgentEntry" in line and last_object_id:
                registry_obj = last_object_id

        if code != 0 or ("Status: Success" not in out and digest == ""):
            return {"status": "error", "error": out[-400:], "digest": digest,
                    "wallet_obj_id": wallet_obj, "cap_obj_id": cap_obj, "registry_obj_id": registry_obj}

        return {
            "status": "success", "digest": digest,
            "wallet_obj_id": wallet_obj, "cap_obj_id": cap_obj, "registry_obj_id": registry_obj,
            "explorer_url": f"https://testnet.suivision.xyz/txblock/{digest}" if digest else "",
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "digest": ""}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200], "digest": ""}


def submit_agent_transfer(amount_sui: float, recipient: str = "") -> dict:
    """
    Submit a real SUI transfer from the agent wallet on testnet.
    Uses sui client ptb to split gas coin and transfer.
    Returns {tx_digest, status, explorer_url}.
    """
    amount_mist = int(amount_sui * 1_000_000_000)
    if amount_mist < 1:
        return {"status": "skipped", "digest": "", "reason": "amount too small"}

    recipient = recipient or WALLET  # send back to self for demo

    cmd = (
        f"client ptb "
        f"--split-coins gas '[{amount_mist}]' "
        f"--assign coin "
        f"--transfer-objects '[coin]' '@{recipient}' "
        f"--gas-budget 10000000"
    )

    try:
        code, out = _sui(cmd)
        digest = _parse_digest(out)

        if code != 0 or "Status: Success" not in out:
            return {"status": "error", "digest": digest or "", "error": out[-300:]}

        return {
            "status": "success",
            "digest": digest,
            "amount_sui": amount_sui,
            "recipient": recipient[:16] + "...",
            "explorer_url": f"https://testnet.suivision.xyz/txblock/{digest}" if digest else "",
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "digest": ""}
    except Exception as e:
        return {"status": "error", "digest": "", "error": str(e)[:200]}
