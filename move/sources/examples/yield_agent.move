/// Yield Agent — autonomously finds best DeepBook liquidity pools
/// and rebalances funds daily to maximize yield.
///
/// Strategy:
/// 1. Scan all DeepBook pools for highest APR
/// 2. Rebalance if current pool APR drops below threshold
/// 3. Compound rewards automatically
/// 4. All actions logged to Walrus via verifiable audit trail
module agentos::examples::yield_agent {
    use std::vector;

    /// Yield Agent configuration — stored on-chain as dynamic field on the agent entry
    public struct YieldConfig has store, drop {
        min_apr_bps: u64,           // minimum acceptable APR (basis points, e.g. 500 = 5%)
        rebalance_threshold_bps: u64, // switch pools if new pool is X bps better
        max_single_pool_pct: u64,   // max % in one pool (0-100)
        compound_enabled: bool,     // auto-compound rewards
        last_rebalance_epoch: u64,  // last time we rebalanced
    }

    /// A yield opportunity discovered by the agent
    public struct YieldOpportunity has store, drop {
        pool_id: address,
        token_a: vector<u8>,
        token_b: vector<u8>,
        apr_bps: u64,
        tvl: u64,
        volume_24h: u64,
    }

    // ── Constants ──

    const DEFAULT_MIN_APR: u64 = 300;       // 3% minimum
    const DEFAULT_REBALANCE_THRESHOLD: u64 = 200; // 2% better to switch
    const DEFAULT_MAX_POOL_PCT: u64 = 50;   // 50% max in one pool

    // ── Public functions ──

    /// Create default yield config
    public fun default_config(): YieldConfig {
        YieldConfig {
            min_apr_bps: DEFAULT_MIN_APR,
            rebalance_threshold_bps: DEFAULT_REBALANCE_THRESHOLD,
            max_single_pool_pct: DEFAULT_MAX_POOL_PCT,
            compound_enabled: true,
            last_rebalance_epoch: 0,
        }
    }

    /// Check if rebalancing is needed (called by off-chain agent runtime)
    public fun should_rebalance(
        config: &YieldConfig,
        current_apr_bps: u64,
        best_apr_bps: u64,
        current_epoch: u64,
    ): bool {
        if (config.last_rebalance_epoch == current_epoch) return false;
        if (best_apr_bps < config.min_apr_bps + config.rebalance_threshold_bps) return false;
        current_apr_bps + config.rebalance_threshold_bps < best_apr_bps
    }

    /// Calculate optimal allocation across pools
    /// Returns percentages for each pool position
    public fun allocate(
        config: &YieldConfig,
        opportunities: vector<YieldOpportunity>,
        total_capital: u64,
    ): vector<u64> {
        let n = vector::length(&opportunities);
        if (n == 0) return vector::empty();

        let allocations = vector::empty();
        let remaining_pct: u64 = 100;
        let i: u64 = 0;

        // Sort by APR descending (simplified — real impl uses heap)
        // Allocate to top pools until max_single_pool_pct reached
        while (i < n && remaining_pct > 0) {
            let pct = config.max_single_pool_pct;
            if (pct > remaining_pct) pct = remaining_pct;
            vector::push_back(&mut allocations, pct);
            remaining_pct = remaining_pct - pct;
            i = i + 1;
        };

        allocations
    }

    // ── View functions ──

    public fun min_apr(config: &YieldConfig): u64 { config.min_apr_bps }
    public fun is_compounding(config: &YieldConfig): bool { config.compound_enabled }
}
