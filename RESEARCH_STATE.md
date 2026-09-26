# RESEARCH_STATE.md

## Current priority
THAOFORAX

## Status
Autonomous research-control system initialized.

## Current objective
Inspect, compile, baseline-test, and improve THAOFORAX for XAUUSD using disciplined research rather than curve fitting.

## Current hypothesis
Claude must write the current falsifiable hypothesis here before changing trading logic.

## Last completed experiment
None recorded here yet.

## Best candidate
None confirmed yet.

## Next exact task
1. Locate and inspect the current THAOFORAX source.
2. Summarize entry / exit / risk / session / regime logic.
3. Record the first falsifiable hypothesis.
4. Compile.
5. Run baseline XAUUSD test with Every Tick Based on Real Ticks.
6. Record metrics in results_summary.csv.
7. Update this file and research_queue.csv.

## Blockers
Verify MT5, MetaEditor, Strategy Tester paths, broker symbol mapping, and report-output path before claiming autonomous backtesting is available.

## Resource note
One EA at a time. One heavy optimization at a time. 1–2 tester agents by default. Do not start heavy work if RAM > 80%.

## Infrastructure log
- 2026-09-26: Added `bridge/` (FastAPI control plane + dashboard, 8 tests passing) and
  `MQL5/Experts/XAU_ControlBridge.mq5` v0.10 (risk guard + HMAC-signed sync). No trading logic:
  `StrategySignal()` is a stub. EA NOT yet compiled in MetaEditor — next: compile, send log, demo run.
- GitHub scan results: `docs/GITHUB_SCAN_2026-09.md`; hypotheses H-GH1..3 queued in research_queue.csv.
