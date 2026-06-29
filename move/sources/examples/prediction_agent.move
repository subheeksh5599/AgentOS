/// Prediction Agent — trades on DeepBook Predict markets.
///
/// Strategy:
/// 1. Fetch active prediction markets via DeepBook Predict
/// 2. Score outcomes using configurable model (simplified on-chain)
/// 3. Place bets within guardrail limits
/// 4. Claim winnings, compound to next market
///
/// DeepBook Predict launched May 2026 — few have built on it yet.
module agentos::examples::prediction_agent {
    use std::vector;

    /// Prediction market configuration
    public struct PredictConfig has store, drop {
        max_bet_per_market: u64,        // max bet in MIST
        min_confidence_bps: u64,        // only bet if confidence > X%
        max_exposure_bps: u64,          // max % of wallet at risk
        allowed_categories: vector<vector<u8>>,  // e.g. ["crypto", "sports", "politics"]
        auto_compound: bool,            // reinvest winnings
    }

    /// A market prediction (bet placement)
    public struct Prediction has store, drop {
        market_id: address,
        outcome: u8,            // which outcome was bet on
        amount: u64,            // bet size
        confidence_bps: u64,    // model confidence
        placed_epoch: u64,
        resolved: bool,
        won: bool,
        payout: u64,
    }

    /// A scored market outcome from the prediction model
    public struct MarketScore has store, drop {
        market_id: address,
        outcome: u8,
        probability_bps: u64,   // model-estimated probability
        edge_bps: u64,          // edge over market-implied probability
    }

    // ── Constants ──

    const DEFAULT_MAX_BET: u64 = 10_000_000_000;      // 10 SUI
    const DEFAULT_MIN_CONFIDENCE: u64 = 6000;          // 60% confidence
    const DEFAULT_MAX_EXPOSURE: u64 = 30;              // 30% max exposure

    // ── Public functions ──

    public fun default_config(allowed_categories: vector<vector<u8>>): PredictConfig {
        PredictConfig {
            max_bet_per_market: DEFAULT_MAX_BET,
            min_confidence_bps: DEFAULT_MIN_CONFIDENCE,
            max_exposure_bps: DEFAULT_MAX_EXPOSURE,
            allowed_categories,
            auto_compound: true,
        }
    }

    /// Calculate edge: model probability minus market-implied probability
    /// Positive edge means the model thinks the market is mispriced
    public fun calc_edge(score: &MarketScore, market_implied_bps: u64): u64 {
        if (score.probability_bps > market_implied_bps) {
            score.probability_bps - market_implied_bps
        } else {
            0
        }
    }

    /// Determine if a bet should be placed based on config + score
    public fun should_bet(
        config: &PredictConfig,
        score: &MarketScore,
        market_implied_bps: u64,
        current_exposure_pct: u64,
    ): bool {
        // Check exposure limit
        if (current_exposure_pct >= config.max_exposure_bps) return false;

        // Check edge
        let edge = calc_edge(score, market_implied_bps);
        if (edge < 100) return false;  // need at least 1% edge

        // Check confidence
        score.probability_bps >= config.min_confidence_bps
    }

    /// Calculate Kelly criterion position size (simplified)
    public fun kelly_size(
        config: &PredictConfig,
        score: &MarketScore,
        market_implied_bps: u64,
        wallet_balance: u64,
    ): u64 {
        let edge = calc_edge(score, market_implied_bps);
        let odds_bps = (10000 * 10000) / market_implied_bps - 10000;
        if (odds_bps == 0) return 0;

        let kelly_pct = (edge * 100) / odds_bps;
        let raw_size = (wallet_balance * kelly_pct) / 10000;

        if (raw_size > config.max_bet_per_market) config.max_bet_per_market
        else raw_size
    }

    // ── View functions ──

    public fun max_bet(config: &PredictConfig): u64 { config.max_bet_per_market }
    public fun min_confidence(config: &PredictConfig): u64 { config.min_confidence_bps }
}
