#!/usr/bin/env python3
"""Backtest EA XAU_StraddleReverse (v5.00 default parameters) บนข้อมูลจริง 1 สัปดาห์

ผู้ใช้ขอให้ backtest "EA StraddleReverse v5" — ข้อเท็จจริงที่ต้องระบุก่อน:

  - **ไม่มีไฟล์ source โค้ด v5.00 อยู่จริงทั้งใน repo และ Google Drive** (ค้นแล้วทั้งคู่
    ยืนยันตรงกับที่ `docs/EXNESS_vs_VTMARKETS.md` เคยระบุไว้ — Drive มีแต่เอกสารคู่มือ
    v5.00 ไม่มีไฟล์ .mq5) — source ที่มีจริงคือ v4.41 (`MQL5/Experts/
    XAU_StraddleReverse_v4_40.mq5`)
  - `tools/ea_backtest_engine.py` (จำลอง Python) ตั้งค่า **default parameters ตรงกับ
    v5.00** ตามที่ผู้เขียนเดิมระบุไว้ในคอมเมนต์ของไฟล์นั้นเอง — สคริปต์นี้ใช้ default
    เหล่านั้นตรงๆ ("ค่าเริ่มต้น = ค่า v5.00")
  - ตรรกะที่รันจริงจึงเป็น **v4.41 logic + v5.00 default params** ไม่ใช่ v5.00 ตัวจริง
    100% เพราะไม่รู้ว่า v5.00 แก้ตรรกะภายในไปจากไหนบ้าง (docs เคยเตือนไว้เรื่อง
    `InpS1/S2/S3` ตีความเวลาต่างกันระหว่างเวอร์ชัน — ดูหัวข้อ 7 ของเอกสารนั้น)

ข้อจำกัดเพิ่มเติมของรอบนี้:
  - `ea_backtest_engine.py` ต้องการ tick bid/ask จริง (จาก ExportSessionTicks.mq5)
    แต่ข้อมูลที่มีตอนนี้คือ **M1 OHLC** (จาก MT5 native export) — สคริปต์นี้จึงแปลง
    OHLC เป็น "synthetic tick" 4 จุดต่อแท่ง (open→low→high→close หรือ
    open→high→low→close ตามทิศทางแท่ง) โดยใช้คอลัมน์ spread จริงของแต่ละแท่งคำนวณ
    bid/ask — เป็นการประมาณ path ราคาภายในแท่ง ไม่ใช่ tick จริง ผลเลขจึงหยาบกว่า
    การรันด้วย tick จริงพอสมควร (โดยเฉพาะกลยุทธ์นี้ที่ไวต่อ intrabar micro-structure
    เพราะวางออเดอร์ห่างราคาแค่ $1.00)
  - ข้อมูลมีแค่ 1 สัปดาห์ (2026-06-30 ถึง 2026-07-07) — session เป้าหมาย (19:00-20:30
    UTC) เกิดขึ้นได้ไม่กี่ครั้งในช่วงนี้ trade count จะน้อยมาก ไม่พอสรุปอะไรทั้งสิ้น

**นี่คือ PILOT/approximation เท่านั้น ไม่ใช่ผลยืนยันประสิทธิภาพ EA จริง**

รัน:
    PYTHONPATH=. python3 research/pilot/backtest_straddlereverse_v5params.py [out.png]
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from tools.hypothesis_backtest_engine import load_ohlc_csv  # noqa: E402
from tools.ea_backtest_engine import Params, run, stats, show  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / \
    "XAUUSDVIP_M1_202607010100_202607072151.csv"
SERVER_GMT_OFFSET = 3
POINT = 0.01  # digits=2 ยืนยันจากไฟล์ข้อมูลจริง (ราคาทศนิยม 2 ตำแหน่ง)


def bars_to_synthetic_ticks(bars):
    """แปลงแท่ง M1 OHLC (+spread จริงต่อแท่ง) เป็น tick bid/ask 4 จุด/แท่ง"""
    times, bids, asks = [], [], []
    for b in bars:
        spread = (b.spread or 0.0) * POINT
        if b.close >= b.open:
            path = [b.open, b.low, b.high, b.close]
        else:
            path = [b.open, b.high, b.low, b.close]
        offsets = [0, 15, 30, 45]
        for px, off in zip(path, offsets):
            t = b.time + timedelta(seconds=off)
            times.append(t)
            bids.append(px - spread / 2)
            asks.append(px + spread / 2)
    return times, bids, asks


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/straddlereverse_v5_pilot.png")

    print("=== Backtest EA XAU_StraddleReverse (v4.41 logic + v5.00 default params) ===")
    print("*** PILOT/approximation เท่านั้น — ดู docstring ของสคริปต์นี้ก่อนเชื่อผล ***\n")

    bars = load_ohlc_csv(str(DATA_PATH), server_gmt_offset=SERVER_GMT_OFFSET)
    times, bids, asks = bars_to_synthetic_ticks(bars)
    print(f"สร้าง synthetic tick {len(times):,} จุด จาก {len(bars):,} แท่ง M1")

    p = Params(commission_per_lot_side=3.5, slippage=0.05)  # Exness Raw ประมาณตาม docs
    print(f"Session window (UTC): {p.win_start//60:02d}:{p.win_start%60:02d}-"
          f"{p.win_end//60:02d}:{p.win_end%60:02d}  "
          f"straddle_dist=${p.straddle_dist}  SL=${p.stop_loss}  "
          f"reverse_start=${p.reverse_start}  reverse_gap=${p.reverse_gap}")

    deals, equity = run(times, bids, asks, p)
    s = stats(deals, p)
    show(s, "XAU_StraddleReverse (v5.00 params, pilot approximation, 1wk real data)")

    fig, ax = plt.subplots(figsize=(11, 5))
    if equity:
        xs = [e[0] for e in equity]
        ys = [e[1] for e in equity]
        color = "#1a9850" if s["net"] > 0 else "#d73027"
        ax.plot(xs, ys, color=color, linewidth=1.2, marker="o", markersize=3)
        ax.axhline(p.start_balance, color="#888888", linewidth=0.6, linestyle="--")
    ax.set_title(
        "EA: XAU_StraddleReverse (v4.41 logic + v5.00 default params)\n"
        f"trades={s['trades']}  net={s['net']:+.2f}  PF={s['pf']:.2f}  "
        f"winrate={s['wr']:.1f}%  DD={s['dd_pct']:.1f}%\n"
        "PILOT — OHLC-derived synthetic ticks, 1 week real data — NOT a verified result",
        fontsize=10)
    ax.set_ylabel("Balance ($)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    print(f"\nเขียนกราฟ: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
