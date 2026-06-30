"""
Trader Agent — real market analysis + conditional transfers on Sui testnet.
Uses live SUI price, validators-as-pools, and arbitrage reasoning with real TX.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state, get_network_status, get_market_data, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.onchain import conditional_transfer
from runtime.event_bus import bus, AgentEvent


def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="startup",
                            summary=f"{agent_name} online — real market data + conditional TX, {interval}s loop"))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                pools = get_pools()
                md = get_market_data()

                state = f"SUI TESTNET | Epoch {network.epoch}\n"
                state += f"SUI/USD: ${md.sui_price_usd:.4f} ({md.price_change_24h_pct:+.2f}% 24h) | 24h High: ${md.high_24h:.4f} Low: ${md.low_24h:.4f}\n"
                state += f"24h Volume: ${md.volume_24h_usd:,.0f} | Market Cap: ${md.market_cap_usd:,.0f}\n"
                state += f"Balance: {wallet.balance_sui} SUI\n"
                state += f"Real pools from testnet validators:\n"
                for p in pools[:5]:
                    spread = abs(p.commission_pct - (pools[-1].commission_pct if len(pools) > 1 else p.commission_pct))
                    state += f"  {p.validator_name[:18]}: {p.apr_pct:.1f}% est.APY, {p.commission_pct:.1f}% fee, {p.tvl_sui:,.0f} SUI TVL\n"
                state += f"\nGuardrails: max_pos={guardrails.get('max_tx_sui',50)} SUI, stop_loss={guardrails.get('stop_loss_pct',5)}%, min_profit={guardrails.get('min_profit_pct',0.5)}%\n"

                decision = decide(agent_type, state, max_position=guardrails.get("max_tx_sui", 50),
                                   stop_loss=guardrails.get("stop_loss_pct", 5.0))

                if wallet.balance_sui >= 0.005 and decision.action == "swap" and decision.confidence >= 0.5:
                    amount = min(decision.amount, wallet.balance_sui * 0.1, guardrails.get("max_tx_sui", 50) * 0.2)
                    if amount >= 0.001:
                        tx_result = conditional_transfer(amount, f"swap:{decision.token_in}->{decision.token_out}")
                        txn_digest = tx_result.get("digest", "")
                        tx_status = tx_result.get("status", "unknown")
                        le = log_agent_action(agent_type, agent_name, decision.__dict__, txn_digest)
                        bus.emit(AgentEvent(
                            agent_type=agent_type, agent_name=agent_name, event_type="txn",
                            summary=f"SWAP {amount:.4f} SUI ({decision.token_in}→{decision.token_out}) — profit est. {decision.expected_profit_pct:.2f}% — {tx_status.upper()}",
                            details={"action": "swap", "amount": amount, "token_in": decision.token_in,
                                     "token_out": decision.token_out, "confidence": decision.confidence,
                                     "expected_profit_pct": decision.expected_profit_pct,
                                     "reasoning": decision.reasoning, "sui_price": md.sui_price_usd,
                                     "explorer": tx_result.get("explorer_url", "")},
                            txn_digest=txn_digest, walrus_blob_id=le.get("walrus_blob_id", ""),
                        ))
                else:
                    reason = decision.reasoning[:100] if decision.reasoning else "no profitable opportunity"
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"{decision.action.upper()}: {reason}",
                        details={"action": decision.action, "confidence": decision.confidence,
                                 "sui_price": md.sui_price_usd, "reasoning": decision.reasoning},
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error",
                                    summary=f"Error: {str(e)[:120]}", details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop()
