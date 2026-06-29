"""
Yield Agent — configurable loop. Real Sui testnet data via RPC.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state, get_network_status, get_gas_price, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent


async def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(
            agent_type=agent_type, agent_name=agent_name,
            event_type="startup",
            summary=f"{agent_name} online — real Sui testnet data, {interval}s loop",
        ))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                pools = get_pools()
                gas = get_gas_price()

                state = f"SUI TESTNET LIVE\nEpoch {network.epoch} | Checkpoint {network.checkpoint:,} | {network.total_txns:,} txns\n"
                state += f"Balance: {wallet.balance_sui} SUI | Gas price: {gas} MIST\n"
                state += f"Wallet: {WALLET_ADDRESS[:10]}...{WALLET_ADDRESS[-6:]}\n\n"

                if pools:
                    state += "DeepBook pools:\n"
                    for p in pools:
                        state += f"  - {p.pool_id[:20]}... {p.token_a}/{p.token_b}\n"
                else:
                    state += "No DeepBook pools deployed on testnet yet.\n"

                state += f"Guardrails: max_tx={guardrails.get('max_tx_sui',100)} SUI\n"
                decision = decide(agent_type, state)

                if wallet.balance_sui >= guardrails.get("max_tx_sui", 100):
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, "")
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="txn",
                        summary=f"{decision.action.upper()}: {decision.amount} SUI — epoch {network.epoch} (real testnet)",
                        details={"action": decision.action, "amount": decision.amount,
                                 "confidence": decision.confidence, "reasoning": decision.reasoning,
                                 "epoch": network.epoch, "checkpoint": network.checkpoint},
                        walrus_blob_id=le.get("walrus_blob_id", ""),
                    ))
                else:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="decision",
                        summary=f"Waiting for test SUI — balance {wallet.balance_sui} SUI (need faucet)",
                        details={"balance": wallet.balance_sui, "epoch": network.epoch,
                                 "faucet": f"https://faucet.sui.io/?address={WALLET_ADDRESS}"},
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name,
                                    event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name,
                                    event_type="error", summary=f"Error: {str(e)[:120]}",
                                    details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop
