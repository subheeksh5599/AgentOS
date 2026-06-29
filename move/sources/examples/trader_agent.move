/// Trader Agent — autonomous spot/margin trading via DeepBook.
///
/// Strategy:
/// 1. Monitor DeepBook order books for arbitrage opportunities
/// 2. Execute trades within guardrail limits
/// 3. Track PnL on-chain
/// 4. Emergency stop-loss at configurable threshold
module agentos::examples::trader_agent {
    use std::vector;

    /// Trader configuration
    public struct TraderConfig has store, drop {
        max_position_size: u64,      // max SUI per position (MIST)
        max_slippage_bps: u64,       // max slippage tolerance (basis points)
        stop_loss_bps: u64,          // auto-sell at X bps loss
        take_profit_bps: u64,        // auto-sell at X bps gain
        max_open_positions: u64,     // max concurrent positions
        allowed_pairs: vector<vector<u8>>,  // whitelist of trading pairs
    }

    /// A single trading position
    public struct Position has store, drop {
        pair: vector<u8>,
        entry_price: u64,
        current_price: u64,
        size: u64,
        direction: bool,  // true = long, false = short
        opened_epoch: u64,
        pnl: i64,         // signed PnL in MIST
    }

    // ── Constants ──

    const DEFAULT_MAX_POSITION: u64 = 100_000_000_000;  // 100 SUI
    const DEFAULT_SLIPPAGE: u64 = 100;                   // 1%
    const DEFAULT_STOP_LOSS: u64 = 500;                  // 5% loss
    const DEFAULT_TAKE_PROFIT: u64 = 1000;               // 10% gain
    const DEFAULT_MAX_POSITIONS: u64 = 5;

    // ── Public functions ──

    public fun default_config(allowed_pairs: vector<vector<u8>>): TraderConfig {
        TraderConfig {
            max_position_size: DEFAULT_MAX_POSITION,
            max_slippage_bps: DEFAULT_SLIPPAGE,
            stop_loss_bps: DEFAULT_STOP_LOSS,
            take_profit_bps: DEFAULT_TAKE_PROFIT,
            max_open_positions: DEFAULT_MAX_POSITIONS,
            allowed_pairs,
        }
    }

    /// Check if stop-loss triggered
    public fun check_stop_loss(config: &TraderConfig, entry: u64, current: u64): bool {
        if (current >= entry) return false;
        let loss_bps = ((entry - current) * 10000) / entry;
        loss_bps >= config.stop_loss_bps
    }

    /// Check if take-profit triggered
    public fun check_take_profit(config: &TraderConfig, entry: u64, current: u64): bool {
        if (current <= entry) return false;
        let gain_bps = ((current - entry) * 10000) / entry;
        gain_bps >= config.take_profit_bps
    }

    /// Calculate PnL for a position
    public fun calc_pnl(position: &Position): i64 {
        if (position.direction) {
            ((position.current_price as i64) - (position.entry_price as i64)) * (position.size as i64)
        } else {
            ((position.entry_price as i64) - (position.current_price as i64)) * (position.size as i64)
        }
    }

    // ── View functions ──

    public fun max_position(config: &TraderConfig): u64 { config.max_position_size }
    public fun slippage(config: &TraderConfig): u64 { config.max_slippage_bps }
}
