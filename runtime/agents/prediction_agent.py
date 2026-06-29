"""
Prediction Agent — trades DeepBook Predict markets via Groq.
"""
import asyncio

from runtime.llm import decide
from runtime.sui_client import get_predict_markets, get_wallet_state
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent

AGENT_NAME = "Prediction Scout"
AGENT_TYPE = "prediction"

GUARDRAILS = {
    "max_bet_sui": 10,
    "daily_spend_sui": 50,
    "min_confidence_pct": 60,
}


async def run():
    bus.emit(AgentEvent(
        agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
        event_type="startup", summary="Prediction Agent online — scanning Predict markets",
    ))

    while True:
        try:
            markets = get_predict_markets()
            wallet = get_wallet_state()

            state = f"""
Balance: {wallet.balance_sui} SUI
Active bets: {len(wallet.active_bets)}
"""
            for bet in wallet.active_bets:
                state += f"  - {bet.get('market','?')}: {bet.get('amount',0)} SUI on {bet.get('outcome','?')}\n"

            state += "\nActive prediction markets:\n"
            for m in markets:
                state += f"  - {m.title} | Pool: {m.pool_size_sui:,.0f} SUI | Yes: {m.yes_price_sui} SUI ({m.implied_pct}%) | 24h Vol: {m.volume_24h_sui:,.0f} SUI\n"

            state += f"\nGuardrails: max_bet={GUARDRAILS['max_bet_sui']} SUI, min_confidence={GUARDRAILS['min_confidence_pct']}%"

            decision = decide(AGENT_TYPE, state,
                            max_bet=GUARDRAILS["max_bet_sui"])

            if decision.action == "hold":
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="decision", summary=f"No edge — {decision.reasoning[:100]}",
                    details={"decision": decision.action, "reasoning": decision.reasoning},
                ))
            elif decision.amount > GUARDRAILS["max_bet_sui"]:
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="guardrail_hit",
                    summary=f"Blocked: {decision.amount} SUI exceeds max bet ({GUARDRAILS['max_bet_sui']} SUI)",
                    details={"amount": decision.amount, "limit": GUARDRAILS["max_bet_sui"]},
                ))
            else:
                log_entry = log_agent_action(AGENT_TYPE, AGENT_NAME, decision.__dict__, "")

                edge = decision.your_estimate_pct - decision.market_implied_pct
                bus.emit(AgentEvent(
                    agent_type=AGENT_TYPE, agent_name=AGENT_NAME,
                    event_type="txn",
                    summary=f"BET: {decision.amount} SUI on outcome #{decision.outcome} ({decision.pool_id[:16]}…) | Edge: {edge:.0f}% | Conf: {decision.confidence:.0%}",
                    details={
                        "action": "bet",
                        "amount": decision.amount,
                        "market_id": decision.pool_id,
                        "outcome": getattr(decision, "outcome", 0),
                        "confidence": decision.confidence,
                        "edge_pct": edge,
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

        await asyncio.sleep(60)
