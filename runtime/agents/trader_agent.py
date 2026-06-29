"""
Trader Agent — configurable, dynamic loop. Arbitrage across DeepBook.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent


async def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(
            agent_type=agent_type, agent_name=agent_name,
            event_type="startup", summary=f"{agent_name} online — scanning order books every {interval}s",
        ))
        while True:
            try:
                pools = get_pools()
                wallet = get_wallet_state()
                state = f"Balance: {wallet.balance_sui} SUI\nPositions:\n"
                for pos in wallet.positions:
                    state += f"  - {pos['pool']}: {pos['amount_sui']} SUI (PnL: {pos['pnl']})\n"
                state += "\nOrder books:\n"
                for p in pools:
                    state += f"  - {p.pool_id}: {p.token_a}/{p.token_b} | TVL: ${p.tvl_sui:,.0f} | APR: {p.apr_pct}% | Vol: ${p.volume_24h_sui:,.0f}\n"
                state += f"\nGuardrails: max_tx={guardrails.get('max_tx_sui',50)} SUI, stop_loss={guardrails.get('stop_loss_pct',5)}%, min_profit={guardrails.get('min_profit_pct',0.5)}%"
                decision = decide(agent_type, state, max_position=guardrails.get("max_tx_sui", 50), stop_loss=guardrails.get("stop_loss_pct", 5.0))
                if decision.action == "hold":
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="decision", summary=f"Holding — {decision.reasoning[:100]}",
                        details={"decision": decision.action, "reasoning": decision.reasoning},
                    ))
                elif decision.amount > guardrails.get("max_tx_sui", 50):
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="guardrail_hit",
                        summary=f"Blocked: {decision.amount} SUI exceeds max ({guardrails.get('max_tx_sui',50)} SUI)",
                        details={"decision": decision.action, "amount": decision.amount, "limit": guardrails.get("max_tx_sui", 50)},
                    ))
                else:
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, "")
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="txn",
                        summary=f"{decision.action.upper()}: {decision.amount} {decision.token_in} → {decision.token_out} (confidence: {decision.confidence:.0%})",
                        details={"action": decision.action, "token_in": decision.token_in,
                                 "token_out": decision.token_out, "amount": decision.amount,
                                 "pool_id": decision.pool_id, "confidence": decision.confidence,
                                 "reasoning": decision.reasoning, "expected_profit": decision.expected_profit_pct},
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


async def run():
    loop = await make_loop("Arb Hunter v2", "trader",
                           {"max_tx_sui": 50, "daily_spend_sui": 300, "stop_loss_pct": 5.0, "min_profit_pct": 0.5}, 30)
    await loop()
