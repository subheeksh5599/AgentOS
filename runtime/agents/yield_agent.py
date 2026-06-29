"""
Yield Agent — configurable, dynamic loop. Scans DeepBook pools via Groq.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent


async def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    """Returns a coroutine function that runs the yield agent loop."""
    async def _loop():
        bus.emit(AgentEvent(
            agent_type=agent_type, agent_name=agent_name,
            event_type="startup",
            summary=f"{agent_name} online — scanning DeepBook pools every {interval}s",
        ))
        while True:
            try:
                pools = get_pools()
                wallet = get_wallet_state()
                state = f"Balance: {wallet.balance_sui} SUI\nActive positions:\n"
                for pos in wallet.positions:
                    state += f"  - {pos['pool']}: {pos['amount_sui']} SUI @ {pos['apr']}% APR (PnL: {pos['pnl']})\n"
                state += "\nAvailable pools:\n"
                for p in pools:
                    state += f"  - {p.pool_id}: {p.token_a}/{p.token_b} | TVL: ${p.tvl_sui:,.0f} | APR: {p.apr_pct}% | 24h Vol: ${p.volume_24h_sui:,.0f}\n"
                state += f"\nGuardrails: max_tx={guardrails.get('max_tx_sui',100)} SUI, min_apr={guardrails.get('min_apr_threshold_pct',3)}%"
                decision = decide(agent_type, state)
                if decision.action == "hold":
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="decision", summary=f"Holding — {decision.reasoning[:100]}",
                        details={"decision": decision.action, "reasoning": decision.reasoning},
                    ))
                elif decision.amount > guardrails.get("max_tx_sui", 100):
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="guardrail_hit",
                        summary=f"Blocked: {decision.amount} SUI exceeds max ({guardrails.get('max_tx_sui',100)} SUI)",
                        details={"decision": decision.action, "amount": decision.amount, "limit": guardrails.get("max_tx_sui", 100)},
                    ))
                else:
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, "")
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name,
                        event_type="txn",
                        summary=f"{decision.action.upper()}: {decision.amount} {decision.token_in} → {decision.token_out} via {decision.pool_id[:16]}… ({decision.confidence:.0%})",
                        details={"action": decision.action, "token_in": decision.token_in,
                                 "token_out": decision.token_out, "amount": decision.amount,
                                 "pool_id": decision.pool_id, "confidence": decision.confidence,
                                 "reasoning": decision.reasoning},
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


# Legacy entry for main.py
async def run():
    loop = await make_loop("Alpha Yield", "yield",
                           {"max_tx_sui": 100, "daily_spend_sui": 500, "min_apr_threshold_pct": 3.0, "max_single_pool_pct": 50}, 45)
    await loop()
