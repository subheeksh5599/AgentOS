"""
Yield Agent — scans DeepBook pools via Groq, decides where to allocate.
"""
import asyncio

from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent

AGENT_NAME = "Alpha Yield"
AGENT_TYPE = "yield"


GUARDRAILS = {
    "max_tx_sui": 100,
    "daily_spend_sui": 500,
    "min_apr_threshold_pct": 3.0,
    "max_single_pool_pct": 50,
}


async def run():
    """Main agent loop — polls pools, calls Groq, acts."""
    bus.emit(AgentEvent(
        agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
        event_type="startup", summary="Yield Agent online — scanning DeepBook pools",
    ))

    while True:
        try:
            # 1. Fetch real on-chain state
            pools = get_pools()
            wallet = get_wallet_state()

            state = f"""
Balance: {wallet.balance_sui} SUI
Active positions:
"""
            for pos in wallet.positions:
                state += f"  - {pos['pool']}: {pos['amount_sui']} SUI @ {pos['apr']}% APR (PnL: {pos['pnl']})\n"

            state += "\nAvailable pools:\n"
            for p in pools:
                state += f"  - {p.pool_id}: {p.token_a}/{p.token_b} | TVL: ${p.tvl_sui:,.0f} | APR: {p.apr_pct}% | 24h Vol: ${p.volume_24h_sui:,.0f}\n"

            state += f"\nGuardrails: max_tx={GUARDRAILS['max_tx_sui']} SUI, min_apr={GUARDRAILS['min_apr_threshold_pct']}%"

            # 2. Ask Groq to decide
            decision = decide(AGENT_TYPE, state)

            # 3. Validate against guardrails
            if decision.action == "hold":
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="decision", summary=f"Holding — {decision.reasoning[:100]}",
                    details={"decision": decision.action, "reasoning": decision.reasoning},
                ))
            elif decision.amount > GUARDRAILS["max_tx_sui"]:
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="guardrail_hit",
                    summary=f"Blocked: {decision.amount} SUI exceeds max TX ({GUARDRAILS['max_tx_sui']} SUI)",
                    details={"decision": decision.action, "amount": decision.amount, "limit": GUARDRAILS["max_tx_sui"]},
                ))
            else:
                # 4. Log to Walrus
                log_entry = log_agent_action(
                    AGENT_TYPE, AGENT_NAME, decision.__dict__, ""
                )

                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="txn",
                    summary=f"{decision.action.upper()}: {decision.amount} {decision.token_in} → {decision.token_out} via {decision.pool_id[:16]}… (confidence: {decision.confidence:.0%})",
                    details={
                        "action": decision.action,
                        "token_in": decision.token_in,
                        "token_out": decision.token_out,
                        "amount": decision.amount,
                        "pool_id": decision.pool_id,
                        "confidence": decision.confidence,
                        "reasoning": decision.reasoning,
                    },
                    walrus_blob_id=log_entry.get("walrus_blob_id", ""),
                ))

        except Exception as e:
            bus.emit(AgentEvent(
                agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                event_type="error", summary=f"Error: {str(e)[:100]}",
                details={"error": str(e)},
            ))

        await asyncio.sleep(45)  # check every 45 seconds
