# GitHub Research Scan — 2026-09-26

Scope: public GitHub, XAUUSD systems + MT5 tooling. README claims are NOT evidence.
Status legend: ADOPT (tooling) / HYPOTHESIS (queued) / REJECT.

## A. Tooling (research infrastructure)

| Repo | What | Verdict |
|---|---|---|
| masdevid/mt5-quant (Rust, MIT) | MCP: compile/backtest/optimize/deal analytics via Wine on Linux/macOS, SQLite report store | ADOPT candidate — could unblock headless backtests (verify Wine+real-tick stability) |
| PHUICMT/mcp-mt5 (Python, MIT, Windows) | MCP: compile, deploy, Strategy Tester run, report parse | ADOPT candidate if MT5 runs on Windows PC/VPS |
| chymian/metatrader-mcp (TS+Flask, MIT) | Optimization via REST in Wine container | Early (8 commits) — reference only |
| ariadng/metatrader-mcp-server (Python, MIT, ~800★) | Live trading/data tools via MetaTrader5 pkg | Monitoring/journal only; no auth on remote mode → never expose publicly |

## B. Strategy sources

| Repo | Idea | Evidence quality | Verdict |
|---|---|---|---|
| anirudhatalmale6-alt/xauusd-strategy-backtest | Trend + zone rejection (001B) vs breakout-retest (001A); Dukascopy bid/ask M1 5y, slippage modeled, IS/OOS split | Best methodology found; 001A negative both periods, 001B +0.095R IS / +0.447R OOS but n=97/29 → not significant | HYPOTHESIS H-GH1 (zone rejection); 001A → do not pursue |
| ilahuerta-IA/backtrader-pullback-window-xauusd (MIT) | M5 EMA-cross → 1-3 bar pullback → breakout window state machine, SL 2.5 ATR / TP 12 ATR | No OOS, costs not explicit; single 5y run | HYPOTHESIS H-GH2 (pullback-window state machine) |
| ikeawesom/xauusd-backtest (MIT) | PDH/PDL sweep-and-reclaim with prior-day bias | No costs, no hard SL (EOD exit), 71% WR headline is untrustworthy | HYPOTHESIS H-GH3 (re-test with real SL + costs) |
| foeed/FvgGold-EA (MIT, .mq5) | FVG quality score + OB confluence + 12-16 GMT killzone, RR 1.5 | 64 trades / 6 months only; $5 daily-loss cap vs stop ≥ $3 at 0.01 lot looks inconsistent | WATCH — score idea only, sample too small |
| yulz008/GOLD_ORB, kalokaman/MT5-GOLD-STRATEGIES | H1 opening-range breakout, fixed 400/1200 pt | Screenshots only, no metrics text / no license (kalokaman) | Low priority; overlaps existing straddle work |
| BlamzKunG/XAUUSD-Grid-EA, coler07/mql5-format | Grid/martingale/hedge | — | REJECT per FAILED_IDEAS (grid as edge substitute) |
| BAKOME-Hub/BAKOMEGoldScalper | ICT + "AI" scalper | Marketing-heavy | Not reviewed further |
