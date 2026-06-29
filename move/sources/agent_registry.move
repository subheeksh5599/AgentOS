/// Agent Registry — central directory for all deployed agents.
/// Stores agent metadata, owner binding, and discovery index.
module agentos::agent_registry {
    use std::string::String;
    use std::vector;
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;
    use sui::event;

    // ── Types ──

    /// Agent categories
    const CATEGORY_YIELD: u8 = 0;
    const CATEGORY_TRADER: u8 = 1;
    const CATEGORY_PREDICTION: u8 = 2;
    const CATEGORY_CUSTOM: u8 = 3;

    /// An agent entry in the registry — one per deployed agent
    public struct AgentEntry has key, store {
        id: UID,
        owner: address,           // creator/controller (zkLogin addr)
        agent_type: u8,           // category
        name: String,             // human-readable
        strategy_module: String,  // Move module implementing agent logic
        wallet_cap: address,      // address of AgentWalletCap for this agent
        active: bool,             // can be paused by owner
        created_at: u64,          // epoch
    }

    /// The global registry singleton
    public struct AgentRegistry has key {
        id: UID,
        agents: vector<address>,  // list of agent object IDs
        total_deployed: u64,
    }

    // ── Events ──

    public struct AgentRegistered has copy, drop {
        agent_id: address,
        owner: address,
        name: String,
        agent_type: u8,
    }

    // ── Init ──

    fun init(ctx: &mut TxContext) {
        transfer::share_object(AgentRegistry {
            id: object::new(ctx),
            agents: vector::empty(),
            total_deployed: 0,
        });
    }

    // ── Public functions ──

    /// Register a new agent with the registry
    public fun register(
        registry: &mut AgentRegistry,
        name: String,
        agent_type: u8,
        strategy_module: String,
        wallet_cap: address,
        ctx: &mut TxContext,
    ): AgentEntry {
        let entry = AgentEntry {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
            agent_type,
            name,
            strategy_module,
            wallet_cap,
            active: true,
            created_at: tx_context::epoch(ctx),
        };

        let agent_id = object::id(&entry);
        vector::push_back(&mut registry.agents, agent_id.to_bytes());
        registry.total_deployed = registry.total_deployed + 1;

        event::emit(AgentRegistered {
            agent_id: agent_id.to_bytes(),
            owner: tx_context::sender(ctx),
            name,
            agent_type,
        });

        entry
    }

    /// Toggle agent active status
    public fun set_active(entry: &mut AgentEntry, active: bool) {
        entry.active = active;
    }

    /// Get total agents deployed
    public fun total_deployed(registry: &AgentRegistry): u64 {
        registry.total_deployed
    }

    /// Check if an agent entry belongs to a given owner
    public fun is_owner(entry: &AgentEntry, addr: address): bool {
        entry.owner == addr
    }
}
