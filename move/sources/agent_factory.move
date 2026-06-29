/// Agent Factory — 1-click agent deployment.
/// Creates wallet + registers agent + sets up guardrails in one PTB.
module agentos::agent_factory {
    use std::string::String;
    use std::vector;
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;
    use sui::event;

    /// Emitted when a new agent is deployed via the factory
    public struct AgentDeployed has copy, drop {
        agent_id: address,
        wallet_id: address,
        owner: address,
        agent_type: u8,
        name: String,
        initial_funding: u64,
    }

    /// Deploy a new agent in one transaction.
    /// 1. Creates AgentWallet with guardrails
    /// 2. Registers in AgentRegistry  
    /// 3. Funds wallet with initial deposit (optional)
    /// 4. Emits AgentDeployed event for frontend indexing
    public fun deploy(
        name: String,
        agent_type: u8,
        strategy_module: String,
        max_tx_value: u64,
        daily_spend_limit: u64,
        allowed_actions: vector<u8>,
        initial_funding: Coin<SUI>,
        encrypted_state_hash: vector<u8>,
        ctx: &mut TxContext,
    ) {
        let funding_amount = coin::value(&initial_funding);

        // Step 1: Create wallet
        let (cap, wallet) = agentos::agent_wallet::create(
            max_tx_value,
            daily_spend_limit,
            allowed_actions,
            encrypted_state_hash,
            ctx,
        );

        // Step 2: Fund wallet
        agentos::agent_wallet::deposit(&mut wallet, initial_funding);

        let wallet_id = object::id_to_address(&wallet);

        // Step 3: Register in registry
        let entry = agentos::agent_registry::register(
            /* registry will be passed via PTB from shared object */ 
            name,
            agent_type,
            strategy_module,
            wallet_id,
            ctx,
        );

        let agent_id = object::id_to_address(&entry);

        // Step 4: Transfer objects to owner
        transfer::transfer(cap, tx_context::sender(ctx));
        transfer::transfer(wallet, tx_context::sender(ctx));
        transfer::transfer(entry, tx_context::sender(ctx));

        // Step 5: Emit event
        event::emit(AgentDeployed {
            agent_id,
            wallet_id,
            owner: tx_context::sender(ctx),
            agent_type,
            name,
            initial_funding: funding_amount,
        });
    }
}
