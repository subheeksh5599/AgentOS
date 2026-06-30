"""
Yield Agent — real Sui staking via sui_system::request_add_stake.
Picks validators from live network state, stakes SUI with best APY.
"""
import asyncio
from runtime.llm import decide
from runtime.sui_client import get_pools, get_wallet_state, get_network_status, get_gas_price, get_market_data, WALLET_ADDRESS
from runtime.walrus_client import log_agent_action
from runtime.onchain import conditional_transfer
from runtime.event_bus import bus, AgentEvent


def make_loop(agent_name: str, agent_type: str, guardrails: dict, interval: int):
    async def _loop():
        bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="startup",
                            summary=f"{agent_name} online — real validator pools + TX, {interval}s loop"))
        while True:
            try:
                network = get_network_status()
                wallet = get_wallet_state()
                pools = get_pools()
                md = get_market_data()
                gas_price = get_gas_price()

                state = f"SUI TESTNET | Epoch {network.epoch} | {network.total_txns:,} txns\n"
                state += f"SUI Price: ${md.sui_price_usd:.4f} ({md.price_change_24h_pct:+.2f}% 24h)\n"
                state += f"Balance: {wallet.balance_sui:.6f} SUI  |  Gas: {gas_price} MIST\n"
                if wallet.positions:
                    staked = sum(p.get("principal", 0) for p in wallet.positions)
                    state += f"Staked: {staked:.4f} SUI across {len(wallet.positions)} validators\n"
                state += f"Guardrails: max_tx={guardrails.get('max_tx_sui',100)} SUI, min_apr={guardrails.get('min_apr_threshold_pct',3)}%\n\n"
                state += "Real Validator Pools (live SUI testnet):\n"
                for p in pools[:8]:
                    state += f"  {p.validator_name[:22]:22s} APY~{p.apr_pct:4.1f}%  TVL={p.tvl_sui:>12,.0f} SUI  fee={p.commission_pct:.1f}%  pool={p.pool_id[:16]}...\n"

                decision = decide(agent_type, state)

                if wallet.balance_sui >= 0.005 and decision.action in ("stake", "compound", "swap") and decision.confidence >= 0.5:
                    amount = min(decision.amount, wallet.balance_sui * 0.3, guardrails.get("max_tx_sui", 100))
                    if amount >= 0.001:
                        op_label = f"yield:{decision.action}:{pools[0].validator_name[:12] if pools else 'unknown'}"
                        tx_result = conditional_transfer(amount, op_label)
                        txn_digest = tx_result.get("digest", "")
                        txn_status = tx_result.get("status", "unknown")

                        le = log_agent_action(agent_type, agent_name, decision.__dict__, txn_digest)
                        pool_info = f" → {pools[0].validator_name[:16]} (~{pools[0].apr_pct:.1f}% APY)" if pools else ""
                        bus.emit(AgentEvent(
                            agent_type=agent_type, agent_name=agent_name, event_type="txn",
                            summary=f"{decision.action.upper()} {amount:.4f} SUI{pool_info} — {txn_status.upper()}",
                            details={"action": decision.action, "amount": amount,
                                     "confidence": decision.confidence, "reasoning": decision.reasoning,
                                     "pools_available": len(pools), "epoch": network.epoch,
                                     "tx_status": txn_status, "explorer": tx_result.get("explorer_url", "")},
                            txn_digest=txn_digest, walrus_blob_id=le.get("walrus_blob_id", ""),
                        ))

                elif decision.action == "unstake" and wallet.positions:
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"UNSTAKE suggested — {decision.reasoning[:100]}",
                        details={"action": "unstake", "positions": wallet.positions, "reasoning": decision.reasoning},
                    ))
                else:
                    reason = decision.reasoning[:120] if decision.reasoning else "no profitable pool found"
                    extra = ""
                    if wallet.balance_sui < 0.005:
                        extra = f" (balance {wallet.balance_sui:.6f} SUI too low)"
                    bus.emit(AgentEvent(
                        agent_type=agent_type, agent_name=agent_name, event_type="decision",
                        summary=f"HOLD: {reason}{extra}",
                        details={"balance": wallet.balance_sui, "pools_scanned": len(pools),
                                 "reasoning": decision.reasoning},
                    ))

            except asyncio.CancelledError:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error", summary=f"{agent_name} stopped"))
                break
            except Exception as e:
                bus.emit(AgentEvent(agent_type=agent_type, agent_name=agent_name, event_type="error",
                                    summary=f"Error: {str(e)[:120]}", details={"error": str(e)}))
            await asyncio.sleep(interval)
    return _loop()
