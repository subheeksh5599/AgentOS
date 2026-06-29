"""
Prediction Agent — real Sui testnet data. DeepBook Predict via Groq.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_predict_markets, get_wallet_state, get_network_status, get_gas_price, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.event_bus import bus, AgentEvent


async def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(
            agent_type=agent_type, agent_name=agent_name,
            event_type="startup", summary=f"{agent_name} online — real testnet, {interval}s loop",
        ))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                markets = get_predict_markets()
                gas = get_gas_price()
                state = f"SUI TESTNET | Epoch {network.epoch} | Gas {gas} MIST\nBalance: {wallet.balance_sui} SUI\n"
                if markets:
                    for m in markets:
                        state += f"  - {m.title}: {m.implied_pct}% implied\n"
                else:
                    state += "(no Predict markets deployed on testnet)\n"
                state += f"Guardrails: max_bet={guardrails.get('max_bet_sui',10)} SUI\n"
                decision = decide(agent_type, state, max_bet=guardrails.get("max_bet_sui", 10))
                if wallet.balance_sui >= guardrails.get("max_bet_sui", 10):
                    le = log_agent_action(agent_type, agent_name, decision.__dict__, "")
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="txn",
                        summary=f"{decision.action.upper()}: {decision.amount} SUI — epoch {network.epoch}",
                        details={"action": decision.action, "amount": decision.amount,
                                 "confidence": decision.confidence, "epoch": network.epoch},
                        walrus_blob_id=le.get("walrus_blob_id", ""),
                    ))
                else:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"Need test SUI — balance {wallet.balance_sui} SUI",
                        details={"balance": wallet.balance_sui, "faucet": f"https://faucet.sui.io/?address={WALLET_ADDRESS}"},
                    ))
            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"Error: {str(e)[:120]}", details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop
