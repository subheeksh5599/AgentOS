"""
Yield Agent — configurable loop. Real TX on Sui testnet.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state, get_network_status, get_gas_price, get_market_data, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.onchain import submit_agent_transfer
from runtime.event_bus import bus, AgentEvent


def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="startup",
                            summary=f"{agent_name} online — real Sui testnet TX, {interval}s loop"))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                pools = get_pools()
                md = get_market_data()

                state = f"SUI TESTNET | Epoch {network.epoch} | Checkpoint {network.checkpoint:,} | {network.total_txns:,} txns\n"
                state += f"SUI Price: ${md.sui_price_usd:.4f} ({md.price_change_24h_pct:+.2f}%)\n"
                state += f"Balance: {wallet.balance_sui} SUI\n"
                state += f"Guardrails: max_tx={guardrails.get('max_tx_sui',100)} SUI\n"
                decision = decide(agent_type, state)

                if wallet.balance_sui >= 0.001 and decision.action != "hold":
                    # Submit real on-chain transfer
                    amount = min(decision.amount, wallet.balance_sui * 0.1, 0.01)
                    tx_result = submit_agent_transfer(amount)
                    txn_digest = tx_result.get("digest", "")
                    txn_status = tx_result.get("status", "unknown")

                    le = log_agent_action(agent_type, agent_name, decision.__dict__, txn_digest)
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="txn",
                        summary=f"REAL TX: {decision.action.upper()} {amount} SUI — {txn_status.upper()} (view on SuiVision)",
                        details={"action": decision.action, "amount": amount,
                                 "confidence": decision.confidence, "reasoning": decision.reasoning,
                                 "epoch": network.epoch, "tx_status": txn_status,
                                 "explorer": tx_result.get("explorer_url", "")},
                        txn_digest=txn_digest, walrus_blob_id=le.get("walrus_blob_id", ""),
                    ))
                elif decision.action != "hold":
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"{decision.action.upper()} suggested but balance too low ({wallet.balance_sui} SUI)",
                        details={"balance": wallet.balance_sui, "action": decision.action,
                                 "reasoning": decision.reasoning[:100]},
                    ))
                else:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"Holding — {decision.reasoning[:120]}",
                        details={"reasoning": decision.reasoning},
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error",
                                    summary=f"Error: {str(e)[:120]}", details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop()
