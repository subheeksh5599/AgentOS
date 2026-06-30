/// Agent Wallet — programmable DeFi wallet with on-chain guardrails.
module agentos::agent_wallet {
    use sui::object::{Self, UID};
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::tx_context::{Self, TxContext};
    use sui::event;

    public struct AgentWalletCap has key, store {
        id: UID,
        owner: address,
    }

    public struct AgentWallet has key, store {
        id: UID,
        balance: u64,
        cap_id: address,
        max_tx_value: u64,
        daily_spend_limit: u64,
        daily_spent: u64,
        last_reset_ms: u64,
        allowed_actions: u64,
        encrypted_state_hash: vector<u8>,
        paused: bool,
    }

    public struct AgentAction has copy, drop {
        agent_id: address,
        action_type: u8,
        amount: u64,
        target: address,
        timestamp_ms: u64,
        success: bool,
    }

    const E_NOT_AUTHORIZED: u64 = 1;
    const E_TX_TOO_LARGE: u64 = 2;
    const E_DAILY_LIMIT_HIT: u64 = 3;
    const E_PAUSED: u64 = 4;

    public fun create(
        max_tx_value: u64,
        daily_spend_limit: u64,
        allowed_actions: u64,
        encrypted_state_hash: vector<u8>,
        ctx: &mut TxContext,
    ): (AgentWalletCap, AgentWallet) {
        let cap = AgentWalletCap {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
        };
        let cap_id = object::uid_to_address(&cap.id);

        let wallet = AgentWallet {
            id: object::new(ctx),
            balance: 0,
            cap_id,
            max_tx_value,
            daily_spend_limit,
            daily_spent: 0,
            last_reset_ms: tx_context::epoch_timestamp_ms(ctx),
            allowed_actions,
            encrypted_state_hash,
            paused: false,
        };

        (cap, wallet)
    }

    public fun agent_transfer(
        cap: &AgentWalletCap,
        wallet: &mut AgentWallet,
        coin: &mut Coin<SUI>,
        recipient: address,
        amount: u64,
        ctx: &mut TxContext,
    ) {
        assert!(cap.owner == tx_context::sender(ctx), E_NOT_AUTHORIZED);
        assert!(!wallet.paused, E_PAUSED);
        assert!(amount <= wallet.max_tx_value, E_TX_TOO_LARGE);
        assert!(wallet.daily_spent + amount <= wallet.daily_spend_limit, E_DAILY_LIMIT_HIT);

        wallet.daily_spent = wallet.daily_spent + amount;
        wallet.balance = wallet.balance + coin::value(coin) - amount;

        let payment = coin::split(coin, amount, ctx);
        transfer::public_transfer(payment, recipient);

        event::emit(AgentAction {
            agent_id: object::uid_to_address(&wallet.id),
            action_type: 0,
            amount,
            target: recipient,
            timestamp_ms: tx_context::epoch_timestamp_ms(ctx),
            success: true,
        });
    }

    public fun pause(cap: &AgentWalletCap, wallet: &mut AgentWallet, ctx: &TxContext) {
        assert!(cap.owner == tx_context::sender(ctx), E_NOT_AUTHORIZED);
        wallet.paused = true;
    }

    public fun resume(cap: &AgentWalletCap, wallet: &mut AgentWallet, ctx: &TxContext) {
        assert!(cap.owner == tx_context::sender(ctx), E_NOT_AUTHORIZED);
        wallet.paused = false;
    }

    public fun balance(wallet: &AgentWallet): u64 { wallet.balance }
    public fun is_paused(wallet: &AgentWallet): bool { wallet.paused }
    public fun max_tx(wallet: &AgentWallet): u64 { wallet.max_tx_value }
    public fun cap_id(wallet: &AgentWallet): address { wallet.cap_id }
    public fun cap_owner(cap: &AgentWalletCap): address { cap.owner }
    public fun wallet_id(wallet: &AgentWallet): address { object::uid_to_address(&wallet.id) }
}
