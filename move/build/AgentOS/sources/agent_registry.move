/// Agent Registry — on-chain directory of all deployed agents.
module agentos::agent_registry {
    use std::string::String;
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::event;

    public struct AgentEntry has key, store {
        id: UID,
        owner: address,
        name: String,
        agent_type: u8,
        strategy_module: String,
        wallet_cap_id: address,
        active: bool,
        created_at_ms: u64,
    }

    public struct AgentRegistered has copy, drop {
        agent_id: address,
        owner: address,
        name: String,
        agent_type: u8,
    }

    public fun register(
        name: String,
        agent_type: u8,
        strategy_module: String,
        wallet_cap_id: address,
        ctx: &mut TxContext,
    ) {
        let entry = AgentEntry {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
            name,
            agent_type,
            strategy_module,
            wallet_cap_id,
            active: false,
            created_at_ms: tx_context::epoch_timestamp_ms(ctx),
        };

        let agent_id = object::uid_to_address(&entry.id);
        event::emit(AgentRegistered { agent_id, owner: tx_context::sender(ctx), name: entry.name, agent_type });
        transfer::public_transfer(entry, tx_context::sender(ctx));
    }

    public fun set_active(entry: &mut AgentEntry, active: bool) { entry.active = active; }
    public fun is_active(entry: &AgentEntry): bool { entry.active }
    public fun get_owner(entry: &AgentEntry): address { entry.owner }
    public fun get_wallet_cap(entry: &AgentEntry): address { entry.wallet_cap_id }
    public fun get_name(entry: &AgentEntry): String { entry.name }
    public fun get_type(entry: &AgentEntry): u8 { entry.agent_type }
}
