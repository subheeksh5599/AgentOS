"""
Prediction Agent — real market data turned into prediction markets.
Uses CoinGecko trends + SUI price action for Kelly criterion betting with real TX.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_predict_markets, get_wallet_state, get_network_status, get_market_data, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.onchain import conditional_transfer
from runtime.event_bus import bus, AgentEvent


def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="startup",
                            summary=f"{agent_name} online — real market data + Kelly criterion bets, {interval}s loop"))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                markets = get_predict_markets()
                md = get_market_data()

                state = f"SUI TESTNET | Epoch {network.epoch}\n"
                state += f"SUI/USD: ${md.sui_price_usd:.4f} ({md.price_change_24h_pct:+.2f}% 24h)\n"
                state += f"24h Range: ${md.low_24h:.4f} - ${md.high_24h:.4f}\n"
                state += f"Balance: {wallet.balance_sui} SUI\n"
                state += f"Guardrails: max_bet={guardrails.get('max_bet_sui',10)} SUI, min_confidence={guardrails.get('min_confidence_pct',60)}%\n\n"

                if markets:
                    state += "Live prediction markets (derived from real data):\n"
                    for m in markets:
                        state += f"  [{m.market_id}] {m.title}\n"
                        state += f"    Outcomes: {', '.join(m.outcomes)} | Market implies: {m.implied_pct:.0f}% | Pool: {m.pool_size_sui:,.0f} SUI | 24h vol: {m.volume_24h_sui:,.0f} SUI\n"
                else:
                    state += "No active prediction markets available.\n"

                if md.trending_coins:
                    state += "\nTrending on CoinGecko:\n"
                    for tc in md.trending_coins[:3]:
                        state += f"  {tc['symbol']}: rank #{tc.get('market_cap_rank',0)}, score {tc.get('score',0)}\n"

                decision = decide(agent_type, state, max_bet=guardrails.get("max_bet_sui", 10))

                if wallet.balance_sui >= 0.005 and decision.action == "bet" and decision.confidence >= 0.55:
                    amount = min(decision.amount, wallet.balance_sui * 0.05, guardrails.get("max_bet_sui", 10) * 0.5)
                    if amount >= 0.001:
                        bet_label = f"bet:{decision.market_id}:outcome{decision.outcome}"
                        tx_result = conditional_transfer(amount, bet_label)
                        txn_digest = tx_result.get("digest", "")
                        tx_status = tx_result.get("status", "unknown")
                        le = log_agent_action(agent_type, agent_name, decision.__dict__, txn_digest)
                        bus.emit(AgentEvent(
                            agent_type=agent_type, agent_name=agent_name, event_type="txn",
                            summary=f"BET {amount:.4f} SUI on {decision.market_id} (outcome {decision.outcome}) — edge: {decision.your_estimate_pct - decision.market_implied_pct:.0f}pp — {tx_status.upper()}",
                            details={"action": "bet", "amount": amount, "confidence": decision.confidence,
                                     "market_id": decision.market_id, "outcome": decision.outcome,
                                     "market_implied_pct": decision.market_implied_pct,
                                     "your_estimate_pct": decision.your_estimate_pct,
                                     "reasoning": decision.reasoning,
                                     "explorer": tx_result.get("explorer_url", "")},
                            txn_digest=txn_digest, walrus_blob_id=le.get("walrus_blob_id", ""),
                        ))

                elif decision.action == "claim":
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"CLAIM suggested: {decision.reasoning[:100]}",
                        details={"action": "claim", "confidence": decision.confidence, "reasoning": decision.reasoning},
                    ))
                else:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"{decision.action.upper()}: {decision.reasoning[:100]}" if decision.reasoning else "No edge found — holding",
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
