#!/usr/bin/env python3
"""สร้างกราฟ equity curve ของ pilot run ทั้ง 23 hypotheses ที่ทดสอบได้

ตามที่ผู้ใช้ขอ: ทุกครั้งที่รายงานผล backtest ต้องมีกราฟประกอบ + ระบุชื่อ
hypothesis/EA ที่ทดสอบชัดเจนบนกราฟ (ไม่ใช่แค่ตารางตัวเลข)

**PILOT เท่านั้น** — คำเตือนเดียวกับ PILOT_RESULTS_ALL30_2026-07-01_to_07.md ทุกประการ

รัน:
    PYTHONPATH=. python3 research/pilot/plot_pilot_all30.py [output.png]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from tools.hypothesis_backtest_engine import CostModel, load_ohlc_csv, run, stats  # noqa: E402
from research.pilot.hypotheses_pilot import ALL_PILOT_STRATEGIES  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / \
    "XAUUSDVIP_M1_202607010100_202607072151.csv"
SERVER_GMT_OFFSET = 3

NAMES = {
    "A1": "Liquidity Sweep Reversal", "A2": "Stop Run Continuation",
    "A3": "Equal High/Low Reclaim", "A4": "Prev Session Sweep-Fail",
    "B1": "BOS Continuation (proxy)", "B2": "CHOCH Reversal (proxy)",
    "B3": "Displacement-Compression (proxy)", "B4": "Trend Transition MTF (proxy)",
    "C1": "FVG Fill Reversal", "C2": "FVG Retracement Continuation",
    "E1": "London Open Momentum", "E2": "NY Open Range Fade",
    "E3": "London/NY Overlap Cont.", "E4": "Asian Range BO at London",
    "F1": "VWAP Extreme Deviation", "F2": "Asian Range Reversion",
    "F3": "Consecutive-Candle Overext.", "F4": "VWAP Band Fade",
    "G1": "Momentum Burst Continuation", "G2": "Breakout-and-Retest",
    "G3": "Shallow-Pullback Continuation", "G4": "Tick-Volume Burst Confirm",
}


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path("/tmp/pilot_all30_equity.png")

    bars = load_ohlc_csv(str(DATA_PATH), server_gmt_offset=SERVER_GMT_OFFSET)
    cost = CostModel(spread_points=0.30, commission_round_trip=0.07, slippage=0.05)

    ids = list(ALL_PILOT_STRATEGIES.keys())
    ncols, nrows = 5, 5
    fig, axes = plt.subplots(nrows, ncols, figsize=(22, 18))
    fig.suptitle(
        "PILOT RUN — XAUUSD VT Markets VIP M1, 2026-06-30–07-07 UTC (1 week real data)\n"
        "PILOT ONLY — NOT Statistical Discovery — sample too small, simplified rules "
        "— see research/pilot/PILOT_RESULTS_ALL30_2026-07-01_to_07.md",
        fontsize=13, y=0.995)

    for idx, hid in enumerate(ids):
        r, c = divmod(idx, ncols)
        ax = axes[r][c]
        cls = ALL_PILOT_STRATEGIES[hid]
        deals, equity = run(bars, cls(), cost)
        s = stats(deals, start_balance=0.0)

        if equity:
            xs = list(range(len(equity)))
            ys = [e[1] for e in equity]
            color = "#1a9850" if s["net"] > 0 else "#d73027"
            ax.plot(xs, ys, color=color, linewidth=1)
            ax.axhline(0, color="#888888", linewidth=0.6)
        title = f"{hid} — {NAMES.get(hid, hid)}"
        subtitle = (f"trades={s['trades']}  net={s['net']:+.1f}  PF={s['pf']:.2f}"
                    if s["trades"] else "no trades in this window")
        ax.set_title(title, fontsize=9, loc="left")
        ax.text(0.02, 0.02, subtitle, transform=ax.transAxes, fontsize=7.5, color="#444444",
                verticalalignment="bottom")
        ax.tick_params(labelsize=6)

    # เซลล์ที่เหลือ (25 ช่อง, ใช้จริง 22) ให้ว่างไว้
    for idx in range(len(ids), nrows * ncols):
        r, c = divmod(idx, ncols)
        axes[r][c].axis("off")

    plt.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(out_path, dpi=110)
    print(f"เขียนไฟล์: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
