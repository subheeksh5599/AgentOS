/// Verifiable Action Log — immutable, append-only execution trail.
/// Designed for Walrus storage: each log batch is published to Walrus
/// with content-addressed blob IDs stored on-chain.
module agentos::action_log {
    use std::vector;
    use sui::object::{Self, UID};
    use sui::tx_context::TxContext;
    use sui::event;

    // ── Types ──

    /// A single logged action — the atomic unit of the audit trail
    public struct ActionRecord has copy, drop, store {
        agent_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        timestamp_ms: u64,
        walrus_blob_id: vector<u8>,  // content-addressed Walrus blob
        txn_digest: vector<u8>,      // Sui TXN digest
        success: bool,
    }

    /// Agent's log — a growing vector of action records
    public struct AgentActionLog has key, store {
        id: UID,
        agent_id: address,
        records: vector<ActionRecord>,
        total_actions: u64,
        total_volume: u64,
        last_walrus_batch: vector<u8>,  // blob ID of last Walrus batch
    }

    // ── Events ──

    public struct ActionLogged has copy, drop {
        agent_id: address,
        action_type: u8,
        amount: u64,
        txn_digest: vector<u8>,
        walrus_blob_id: vector<u8>,
    }

    // ── Public functions ──

    /// Create a new action log for an agent
    public fun create(agent_id: address, ctx: &mut TxContext): AgentActionLog {
        AgentActionLog {
            id: object::new(ctx),
            agent_id,
            records: vector::empty(),
            total_actions: 0,
            total_volume: 0,
            last_walrus_batch: vector::empty(),
        }
    }

    /// Append an action to the log
    public fun log_action(
        log: &mut AgentActionLog,
        agent_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        timestamp_ms: u64,
        walrus_blob_id: vector<u8>,
        txn_digest: vector<u8>,
        success: bool,
    ) {
        let record = ActionRecord {
            agent_id,
            action_type,
            amount,
            target,
            timestamp_ms,
            walrus_blob_id,
            txn_digest,
            success,
        };

        vector::push_back(&mut log.records, record);
        log.total_actions = log.total_actions + 1;
        log.total_volume = log.total_volume + amount;

        event::emit(ActionLogged {
            agent_id,
            action_type,
            amount,
            txn_digest,
            walrus_blob_id,
        });
    }

    /// Publish log batch to Walrus and record blob ID
    public fun seal_batch(log: &mut AgentActionLog, walrus_blob_id: vector<u8>) {
        log.last_walrus_batch = walrus_blob_id;
    }

    /// View functions
    public fun total_actions(log: &AgentActionLog): u64 { log.total_actions }
    public fun total_volume(log: &AgentActionLog): u64 { log.total_volume }
    public fun record_count(log: &AgentActionLog): u64 { vector::length(&log.records) as u64 }
}
