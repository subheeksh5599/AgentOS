/// Agent Wallet — Sui wallet owned by an AI agent with programmable guardrails.
/// Uses Sponsored TXs for gasless execution and Seal for encrypted state.
module agentos::agent_wallet {
    use std::vector;
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::balance::{Self, Balance};
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;
    use sui::event;

    // ── Types ──

    /// Capability proving ownership of an agent wallet.
    /// Only the holder can authorize agent actions.
    public struct AgentWalletCap has key, store {
        id: UID,
        owner: address,          // agent's controller
    }

    /// The agent's wallet — holds funds and enforces guardrails.
    public struct AgentWallet has key {
        id: UID,
        cap_id: address,         // linked AgentWalletCap
        balance: Balance<SUI>,   // SUI balance
        // Guardrail parameters
        max_tx_value: u64,       // max SUI per single action (in MIST)
        daily_spend_limit: u64,  // max SUI per epoch (in MIST)
        spent_today: u64,        // tracker reset each epoch
        last_epoch: u64,
        allowed_actions: vector<u8>,  // allowed action types
        active: bool,
        // Seal encryption marker
        encrypted_state_hash: vector<u8>,  // hash stored on Walrus
    }

    // ── Events ──

    public struct AgentAction has copy, drop {
        wallet_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        epoch: u64,
    }

    public struct GuardrailHit has copy, drop {
        wallet_id: address,
        reason: vector<u8>,
        attempted_amount: u64,
    }

    // ── Constants ──

    const ACTION_TRANSFER: u8 = 0;
    const ACTION_SWAP: u8 = 1;
    const ACTION_STAKE: u8 = 2;
    const ACTION_LP_DEPOSIT: u8 = 3;
    const ACTION_LP_WITHDRAW: u8 = 4;
    const ACTION_PREDICT: u8 = 5;

    const E_INSUFFICIENT_BALANCE: u64 = 1;
    const E_EXCEEDS_MAX_TX: u64 = 2;
    const E_EXCEEDS_DAILY_LIMIT: u64 = 3;
    const E_ACTION_NOT_ALLOWED: u64 = 4;
    const E_WALLET_INACTIVE: u64 = 5;
    const E_NOT_AUTHORIZED: u64 = 6;

    // ── Public functions ──

    /// Create a new agent wallet with guardrails.
    /// Only callable by the agent factory or via sponsored TX.
    public fun create(
        max_tx_value: u64,
        daily_spend_limit: u64,
        allowed_actions: vector<u8>,
        encrypted_state_hash: vector<u8>,
        ctx: &mut TxContext,
    ): (AgentWalletCap, AgentWallet) {
        let cap = AgentWalletCap {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
        };

        let wallet = AgentWallet {
            id: object::new(ctx),
            cap_id: object::id(&cap),
            balance: balance::zero(),
            max_tx_value,
            daily_spend_limit,
            spent_today: 0,
            last_epoch: tx_context::epoch(ctx),
            allowed_actions,
            active: true,
            encrypted_state_hash,
        };

        (cap, wallet)
    }

    /// Deposit SUI into the agent wallet (anyone can fund)
    public fun deposit(wallet: &mut AgentWallet, coin: Coin<SUI>) {
        let amount = coin::value(&coin);
        balance::join(&mut wallet.balance, coin::into_balance(coin));
    }

    /// Agent executes an action — guardrails enforced.
    /// Callable only via sponsored TX gas station pattern.
    public fun agent_transfer(
        cap: &AgentWalletCap,
        wallet: &mut AgentWallet,
        amount: u64,
        recipient: address,
        action_type: u8,
        ctx: &mut TxContext,
    ): Coin<SUI> {
        assert!(wallet.active, E_WALLET_INACTIVE);
        assert!(cap.owner == tx_context::sender(ctx), E_NOT_AUTHORIZED);
        assert!(amount <= wallet.max_tx_value, E_EXCEEDS_MAX_TX);
        assert!(vector::contains(&wallet.allowed_actions, &action_type), E_ACTION_NOT_ALLOWED);

        // Reset daily tracker if new epoch
        let epoch = tx_context::epoch(ctx);
        if (epoch != wallet.last_epoch) {
            wallet.spent_today = 0;
            wallet.last_epoch = epoch;
        };

        assert!(wallet.spent_today + amount <= wallet.daily_spend_limit, E_EXCEEDS_DAILY_LIMIT);
        wallet.spent_today = wallet.spent_today + amount;

        event::emit(AgentAction {
            wallet_id: object::id(wallet).to_bytes(),
            action_type,
            amount,
            target: recipient,
            epoch,
        });

        coin::take(&mut wallet.balance, amount, ctx)
    }

    /// Emergency pause — owner only
    public fun pause(cap: &AgentWalletCap, wallet: &mut AgentWallet) {
        assert!(cap.owner == tx_context::sender(wallet.id.to_bytes() as &TxContext), E_NOT_AUTHORIZED);
        wallet.active = false;
    }

    /// Emergency resume — owner only
    public fun resume(cap: &AgentWalletCap, wallet: &mut AgentWallet) {
        assert!(cap.owner == tx_context::sender(wallet.id.to_bytes() as &TxContext), E_NOT_AUTHORIZED);
        wallet.active = true;
    }

    /// Update guardrail parameters — owner only
    public fun update_guardrails(
        cap: &AgentWalletCap,
        wallet: &mut AgentWallet,
        max_tx_value: u64,
        daily_spend_limit: u64,
        allowed_actions: vector<u8>,
    ) {
        assert!(cap.owner == tx_context::sender(wallet.id.to_bytes() as &TxContext), E_NOT_AUTHORIZED);
        wallet.max_tx_value = max_tx_value;
        wallet.daily_spend_limit = daily_spend_limit;
        wallet.allowed_actions = allowed_actions;
    }

    /// View functions
    public fun balance(wallet: &AgentWallet): u64 { balance::value(&wallet.balance) }
    public fun is_active(wallet: &AgentWallet): bool { wallet.active }
    public fun get_cap_id(wallet: &AgentWallet): address { wallet.cap_id }
}
