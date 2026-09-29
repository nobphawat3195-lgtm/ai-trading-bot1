# RESEARCH_STATE.md

## Current priority
THAOFORAX

## Status
Autonomous research-control system initialized.

## Current objective
Inspect, compile, baseline-test, and improve THAOFORAX for XAUUSD using disciplined research rather than curve fitting.

## Current hypothesis
H-GRID1 (ladder grid, XAU_LadderGrid.mq5 v0.10): after price stretches > N x ATR from EMA(M5, closed bars), gold
partially reverts; a fixed-step multi-level grid with a TP ladder and a hard basket stop can harvest it with bounded loss.
Full record (why it may exist, when it fails, falsification): docs/LADDER_GRID_HYPOTHESIS.md.
Origin: behaviour observed in a commercial EA's trade history (black-box only; no decompilation, no code copied).
THAOFORAX priority is unchanged; H-GRID1 is queued as research_queue id 10.

## Last completed experiment
None with real data yet. Synthetic path tests only (tools/ladder_grid_sim.py --synthetic): they show risk SHAPE
(capped loss per basket vs uncapped tail), not edge. 14 invariant tests pass (tools/test_ladder_grid_sim.py).

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
- 2026-09-29: Added H-GRID1: `docs/LADDER_GRID_HYPOTHESIS.md`, `tools/ladder_grid_sim.py` (+14 tests),
  `MQL5/Experts/XAU_LadderGrid.mq5` v0.10. EA NOT compiled. Default grid needs ~$11.6k equity for 2% basket risk
  at 0.01 lot and is refused on $300 by design (worst case ~$232 = 77%).
  Next: compile in MetaEditor -> export full-day ticks (ExportSessionTicks) -> run ladder_grid_sim.py on real data ->
  Real Ticks baseline in Strategy Tester -> compare sim vs tester.
