"""
Prediction Agent — configurable, dynamic loop. Trades DeepBook Predict markets.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_predict_markets, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent


async def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(
            agent_type=agent_type, agent_name=agent_name,
            event_type="startup", summary=f"{agent_name} online — scanning Predict markets every {interval}s",
        ))
        while True:
            try:
                markets = get_predict_markets()
                wallet = get_wallet_state()
                state = f"Balance: {wallet.balance_sui} SUI\nActive bets:\n"
                for b in wallet.active_bets:
                    state += f"  - {b['market']}: {b['amount_sui']} SUI @ {b['entry_pct']}% (PnL: {b['pnl']})\n"
                state += "\nMarkets:\n"
                for m in markets:
                    state += f"  - {m.market_id}: {m.title} | Pool: ${m.pool_size_sui:,.0f} | Yes: {m.yes_price_sui} SUI ({m.implied_pct}%) | Vol: ${m.volume_24h_sui:,.0f}\n"
                state += f"\nGuardrails: max_bet={guardrails.get('max_bet_sui',10)} SUI, min_confidence={guardrails.get('min_confidence_pct',60)}%"
                decision = decide(agent_type, state, max_bet=guardrails.get("max_bet_sui", 10))
                if decision.action == "hold":
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="decision", summary=f"Holding — {decision.reasoning[:100]}",
                        details={"decision": decision.action, "reasoning": decision.reasoning},
                    ))
                elif decision.confidence < guardrails.get("min_confidence_pct", 60) / 100:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="guardrail_hit",
                        summary=f"Blocked: confidence {decision.confidence:.0%} below {guardrails.get('min_confidence_pct',60)}% threshold",
                        details={"decision": decision.action, "confidence": decision.confidence, "limit": guardrails.get("min_confidence_pct", 60)},
                    ))
                elif decision.amount > guardrails.get("max_bet_sui", 10):
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="guardrail_hit",
                        summary=f"Blocked: {decision.amount} SUI exceeds max bet ({guardrails.get('max_bet_sui',10)} SUI)",
                        details={"decision": decision.action, "amount": decision.amount, "limit": guardrails.get("max_bet_sui", 10)},
                    ))
                else:
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, "")
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="txn",
                        summary=f"BET: {decision.amount} SUI on outcome {decision.outcome} of {decision.pool_id[:16]}… (edge: {decision.edge_pct if hasattr(decision,'edge_pct') else '?'}%, conf: {decision.confidence:.0%})",
                        details={"action": decision.action, "amount": decision.amount,
                                 "market_id": decision.pool_id, "outcome": decision.outcome,
                                 "confidence": decision.confidence, "reasoning": decision.reasoning,
                                 "implied_pct": decision.market_implied_pct, "estimate_pct": decision.your_estimate_pct},
                        walrus_blob_id=le.get("walrus_blob_id", ""),
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name,
                                    event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name,
                                    event_type="error", summary=f"Error: {str(e)[:100]}",
                                    details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop


async def run():
    loop = await make_loop("Prediction Scout", "prediction",
                           {"max_bet_sui": 10, "daily_spend_sui": 50, "min_confidence_pct": 60}, 60)
    await loop()
