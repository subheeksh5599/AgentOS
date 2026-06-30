/// Action Log — immutable on-chain audit trail for agent decisions.
module agentos::action_log {
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::event;

    public struct ActionEntry has key, store {
        id: UID,
        agent_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        timestamp_ms: u64,
        walrus_blob_id: vector<u8>,
        txn_digest: vector<u8>,
        success: bool,
    }

    public struct VerifiableExecutionLog has copy, drop {
        agent_id: address,
        action_type: u8,
        timestamp_ms: u64,
        walrus_blob_id: vector<u8>,
    }

    public fun log(
        agent_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        walrus_blob_id: vector<u8>,
        txn_digest: vector<u8>,
        success: bool,
        ctx: &mut TxContext,
    ) {
        let entry = ActionEntry {
            id: object::new(ctx),
            agent_id, action_type, amount, target,
            timestamp_ms: tx_context::epoch_timestamp_ms(ctx),
            walrus_blob_id, txn_digest, success,
        };

        event::emit(VerifiableExecutionLog {
            agent_id, action_type,
            timestamp_ms: entry.timestamp_ms,
            walrus_blob_id: entry.walrus_blob_id,
        });
        transfer::public_share_object(entry);
    }
}
