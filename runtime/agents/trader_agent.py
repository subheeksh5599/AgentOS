"""
Trader Agent — arbitrage across DeepBook Spot + Margin via Groq.
"""
import asyncio

from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent

AGENT_NAME = "Arb Hunter v2"
AGENT_TYPE = "trader"

GUARDRAILS = {
    "max_tx_sui": 50,
    "daily_spend_sui": 300,
    "stop_loss_pct": 5.0,
    "min_profit_pct": 0.5,
}


async def run():
    bus.emit(AgentEvent(
        agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
        event_type="startup", summary="Trader Agent online — scanning order books",
    ))

    while True:
        try:
            pools = get_pools()
            wallet = get_wallet_state()

            state = f"""
Balance: {wallet.balance_sui} SUI
Positions: {len(wallet.positions)} open
"""
            for pos in wallet.positions:
                state += f"  - {pos['pool']}: {pos['amount_sui']} SUI (PnL: {pos['pnl']})\n"

            state += "\nMarket prices:\n"
            for p in pools:
                state += f"  - {p.token_a}/{p.token_b}: TVL ${p.tvl_sui:,.0f}, 24h Vol ${p.volume_24h_sui:,.0f}\n"

            state += f"\nGuardrails: max_position={GUARDRAILS['max_tx_sui']} SUI, stop_loss={GUARDRAILS['stop_loss_pct']}%"

            decision = decide(AGENT_TYPE, state,
                            max_position=GUARDRAILS["max_tx_sui"],
                            stop_loss=GUARDRAILS["stop_loss_pct"])

            if decision.action == "hold":
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="decision", summary=f"No edge — {decision.reasoning[:100]}",
                    details={"decision": decision.action, "reasoning": decision.reasoning},
                ))
            elif decision.amount > GUARDRAILS["max_tx_sui"]:
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="guardrail_hit",
                    summary=f"Blocked: {decision.amount} SUI exceeds max position ({GUARDRAILS['max_tx_sui']} SUI)",
                    details={"amount": decision.amount, "limit": GUARDRAILS["max_tx_sui"]},
                ))
            else:
                log_entry = log_agent_action(AGENT_TYPE, AGENT_NAME, decision.__dict__, "")

                expected_profit = decision.__dict__.get("expected_profit_pct", 0)
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="txn",
                    summary=f"{decision.action.upper()}: {decision.amount} {decision.token_in} → {decision.token_out} | Expected profit: {expected_profit}% (conf: {decision.confidence:.0%})",
                    details={
                        "action": decision.action,
                        "token_in": decision.token_in,
                        "token_out": decision.token_out,
                        "amount": decision.amount,
                        "confidence": decision.confidence,
                        "expected_profit_pct": expected_profit,
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

        await asyncio.sleep(30)
