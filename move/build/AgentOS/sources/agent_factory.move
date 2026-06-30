/// Agent Factory — one-click deploy: wallet + registry entry.
module agentos::agent_factory {
    use std::string::String;
    use sui::tx_context::{Self, TxContext};
    use sui::event;
    use agentos::agent_wallet;
    use agentos::agent_registry;

    public struct AgentDeployed has copy, drop {
        agent_id: address,
        owner: address,
        name: String,
        agent_type: u8,
    }

    public fun deploy(
        name: String,
        agent_type: u8,
        strategy_module: String,
        max_tx_value: u64,
        daily_spend_limit: u64,
        allowed_actions: u64,
        encrypted_state_hash: vector<u8>,
        ctx: &mut TxContext,
    ) {
        let (cap, wallet) = agent_wallet::create(
            max_tx_value, daily_spend_limit, allowed_actions, encrypted_state_hash, ctx,
        );

        agent_registry::register(
            name, agent_type, strategy_module, agent_wallet::cap_id(&wallet), ctx,
        );

        let wallet_id = agent_wallet::wallet_id(&wallet);

        event::emit(AgentDeployed {
            agent_id: wallet_id, owner: tx_context::sender(ctx), name, agent_type,
        });
        transfer::public_transfer(cap, tx_context::sender(ctx));
        transfer::public_transfer(wallet, tx_context::sender(ctx));
    }
}
