"""
Trader Agent — real TX on Sui testnet. CoinGecko price data.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state, get_network_status, get_market_data, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.onchain import submit_agent_transfer
from runtime.event_bus import bus, AgentEvent


def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="startup",
                            summary=f"{agent_name} online — live SUI price + real TX, {interval}s loop"))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                pools = get_pools()
                md = get_market_data()

                state = f"SUI TESTNET | Epoch {network.epoch}\n"
                state += f"SUI/USD: ${md.sui_price_usd:.4f} ({md.price_change_24h_pct:+.2f}% 24h)\n"
                state += f"Balance: {wallet.balance_sui} SUI\n"
                state += f"Guardrails: max_pos={guardrails.get('max_tx_sui',50)} SUI, stop_loss={guardrails.get('stop_loss_pct',5)}%, min_profit={guardrails.get('min_profit_pct',0.5)}%\n"
                decision = decide(agent_type, state, max_position=guardrails.get("max_tx_sui", 50), stop_loss=guardrails.get("stop_loss_pct", 5.0))

                if wallet.balance_sui >= 0.001 and decision.action != "hold":
                    amount = min(decision.amount, wallet.balance_sui * 0.05, 0.01)
                    tx_result = submit_agent_transfer(amount)
                    txn_digest = tx_result.get("digest", "")
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, txn_digest)
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="txn",
                        summary=f"REAL TX: {decision.action.upper()} {amount} SUI — {tx_result.get('status','').upper()}",
                        details={"action": decision.action, "amount": amount, "confidence": decision.confidence,
                                 "reasoning": decision.reasoning, "sui_price": md.sui_price_usd,
                                 "explorer": tx_result.get("explorer_url", "")},
                        txn_digest=txn_digest, walrus_blob_id=le.get("walrus_blob_id", ""),
                    ))
                else:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"{decision.action.upper()}: {decision.reasoning[:100]}",
                        details={"action": decision.action, "confidence": decision.confidence, "reasoning": decision.reasoning},
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error",
                                    summary=f"Error: {str(e)[:120]}", details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop()
