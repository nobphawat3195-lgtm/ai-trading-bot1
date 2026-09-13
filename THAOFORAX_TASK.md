# THAOFORAX_TASK.md

## Current directive
THAOFORAX is the highest-priority EA project.

### First requirement: make GitHub the source of truth
If the current THAOFORAX source exists only in Claude Code's local/VPS workspace:
1. Commit all relevant .mq5/.mqh source to this repository.
2. Include required .set/config files needed to reproduce tests.
3. Do not commit secrets, account credentials, broker passwords, or private API keys.
4. Record the exact MT5/MetaEditor/tester paths in RESEARCH_STATE.md only if they are non-secret environment paths.

### Then execute the research loop
1. Read CLAUDE.md and all research-state files.
2. Audit current logic before changes.
3. Write a falsifiable hypothesis.
4. Compile with 0 errors.
5. Run baseline XAUUSD Every Tick Based on Real Ticks.
6. Save report/metrics.
7. Run ablation before broad optimization.
8. Optimize only if raw edge is credible.
9. Validate OOS / walk-forward / spread/slippage stress.
10. Update project memory after every experiment.

### Required baseline metrics
- Profit Factor
- Max Equity Drawdown
- Net Profit
- Trades
- Win Rate
- Expectancy
- Avg Win / Avg Loss
- Sharpe
- Recovery Factor
- Longest Losing Streak
- MAE/MFE if available
- Average Holding Time

### Decision
PASS / WATCH / REJECT must include the reason and the next exact task.

### Continue autonomously
Do not stop merely to ask what to do next when the next experiment is already implied by CLAUDE.md or research_queue.csv.
Stop only for a genuine blocker such as missing MT5 access, missing source/dependency, credentials, destructive action, or a decision that requires the user.
