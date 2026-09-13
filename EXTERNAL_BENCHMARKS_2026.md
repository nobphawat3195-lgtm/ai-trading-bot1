# EXTERNAL_BENCHMARKS_2026.md

Purpose: external benchmark set for THAOFORAX research. These are not source-code templates and are not proof of a reproducible edge. Use them only to generate and prioritize hypotheses.

## Benchmark systems

### Stable Gold EA — Myfxbook strategy/backtest
Source: https://www.myfxbook.com/strategies/stable-gold-ea/373222
- Test period: 2020-08-04 to 2026-04-20
- Timeframe: H1
- Trades: 10,241
- Gain: +5881.83%
- Monthly: 6.06%
- Drawdown: 14.25%
- Profit Factor: 1.78
- Average win: $21.20
- Average loss: -$22.56
- Expectancy: $5.74/trade
- Average trade length: 7h 40m
- Long win rate: 66%
- Short win rate: 64%

Research lesson:
High sample size + moderate PF + moderate DD is a stronger robustness benchmark than very high short-period monthly returns. This profile is useful as a 'quality edge' benchmark, not as proof that H1 is optimal.

### Chronos Algorithm (GOLD) — ThaiFXBook
Source: https://thaifxbook.com/en/p/3e572d7c-9011-4d29-ab19-9f5fdc2b9755
- Gain: +136.75%
- Monthly: +27.40%
- Equity Drawdown: 3.56% on current headline view
- XAUUSDc long-only
- 2,438 trades
- Win rate: 71.9%
- AI analysis notes Sharpe around 0.11 and 317 overleveraging events

Research lesson:
The combination of high monthly growth, high win rate and low headline DD deserves behavioral reverse engineering, but low Sharpe and overleveraging warnings mean position sizing and tail risk must be treated separately from entry edge.

### CLOUDPips Sora — ThaiFXBook
Source: https://thaifxbook.com/en/p/e04c6af9-c3b7-4158-8c85-89fd53ecee40
- Gain: +29.20%
- Monthly: +41.82%
- Drawdown: 22.35%
- 490 positions
- Win rate: 59.59%
- Long win rate: 61.6%
- Short win rate: 57.27%
- Average loss is larger than average win
- Thursday reported as strongest day; Monday-Tuesday were a drag

Research lesson:
High headline monthly return can coexist with mediocre payoff structure. Time/day and long-short asymmetry are worth testing, but day filters must be replicated across independent periods before use.

### CLOUDPips Kumo — ThaiFXBook
Source: https://thaifxbook.com/en/p/90be93d3-9539-48e4-b226-23343aa80067
- Gain: +135.92%
- Monthly: +74.27%
- Headline drawdown: 53.17%
- 743 positions
- Win rate: 75.24%
- Average loss materially larger than average win
- ThaiFXBook analysis flags extreme drawdown/tail risk

Research lesson:
This is a useful example of the difference between high growth and sustainable growth. Do not use win rate alone. Measure payoff asymmetry, equity DD, giveback, risk of ruin and tail dependence.

### CLOUDPips Hoshi — ThaiFXBook
Source: https://thaifxbook.com/en/p/364fc253-f453-4928-80d8-66c10878165b
- Gain: +30.73%
- Monthly: +14.40%
- Drawdown: 46.55%
- 309 entries
- Win rate: 69.26%
- Profit Factor: 1.18
- 03:00-06:00 reported as a strong time window in the visible analysis

Research lesson:
Session effects may be real but must not be copied directly. Test multiple time windows with timezone verification and untouched OOS periods.

### Rcn S23 — ThaiFXBook
Source: https://thaifxbook.com/en/p/4862e5af-034f-45f5-aa30-be6d1d2af4cf
- Nearly pure XAUUSD
- 9,950 XAUUSD trades
- Long 5,252 / Short 4,698
- Win rate around 68%

Research lesson:
Very high trade count is valuable for studying long/short asymmetry, time-of-day, holding time, lot progression and payoff shape. Do not infer edge from win rate alone.

### TOMAHAWK — ThaiFXBook
Source: https://thaifxbook.com/en/p/fe770d18-b1ca-445a-ba76-5b60f5aeae95
- 4,655 XAUUSD trades
- Win rate: 75.45%
- Average win: 7.55 cent
- Average loss: -22.21 cent
- Longest loss streak: 9
- Average hold: 32m
- Recovery factor: 0.18

Research lesson:
Another strong warning that a high win rate can hide a weak payoff structure. New THAOFORAX engines must report avg win/loss and expectancy, not only WR.

## Meta-lessons for THAOFORAX

1. High monthly return often comes with either high DD, weak payoff asymmetry, overleveraging, or short sample length.
2. Large sample size + moderate PF + moderate DD should be used as a robustness benchmark.
3. Session/time-of-day, long-short asymmetry, volatility regime, holding time and position-size behavior are recurring dimensions worth testing.
4. Win rate is not a primary success metric. PF, expectancy, avg win/loss, DD, recovery and OOS matter more.
5. Separate entry edge from capital/risk scaling. A high return profile may be mostly sizing/compounding rather than a stronger edge.
6. Build multiple independent engines first; combine only after each shows positive OOS expectancy and sufficiently low PnL correlation.
7. Use rejected/high-risk public systems as negative evidence and hypothesis generators, not as templates to copy.

## Research queue generated from external benchmarks

### EB01 — Long-side asymmetry
Test whether XAUUSD long-only or long-biased execution has higher expectancy than symmetric long/short under identical entry logic.

### EB02 — Session selectivity
Test rolling 3-hour windows and major market sessions. Verify broker/server timezone. Require replication across at least two independent periods before adding a time filter.

### EB03 — Day-of-week asymmetry
Test each weekday independently, but do not adopt a day filter unless the effect persists OOS and has adequate trades.

### EB04 — Short-hold high-frequency edge
Test 15m-90m holding-time hypotheses with strict spread/slippage modeling. Compare expectancy net of transaction cost.

### EB05 — High-win-rate / poor-payoff failure mode
Build a diagnostic that rejects systems where average loss is too large relative to average win even if WR > 65%.

### EB06 — Risk-scaling decomposition
For every promising engine run fixed-lot, fixed-fractional 0.5/1/2/3/5%, and report how much return improvement comes from edge versus compounding/risk.

### EB07 — Regime router
Evaluate whether trend strength, ATR percentile, range expansion and session jointly predict which engine should be active. Router rules must be based only on information known before entry.

### EB08 — Multi-engine diversification
After at least three engines pass OOS, compute daily/weekly PnL correlation, simultaneous DD, and combined return/DD. Combine only low-correlation engines.

## Target framework

Do not force the target mechanically, but evaluate against:
- Preferred engine PF >= 1.30
- OOS PF > 1.10
- Expectancy > 0
- Preferred Max Equity DD <= 15-20% at base risk
- Recovery Factor >= 2 when available
- Positive stress-test result
- No single month or top few trades dominate total profit

High-growth profiles may target 50-100% monthly only after underlying edge is validated. If the target requires DD > 40-50% or extreme risk scaling, classify as HIGH RISK / NOT PRODUCTION even when net profit is large.
