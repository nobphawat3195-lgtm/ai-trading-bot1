#!/usr/bin/env python3
"""Pilot run — hypotheses A1 / G1 / F3 บนข้อมูลจริง 1 สัปดาห์ (2026-06-30 ถึง 2026-07-07)

**นี่คือ PILOT ไม่ใช่ Statistical Discovery ตามข้อ 5 ของ MASTER COMMAND**

ทำไมต้องแยก "pilot" ออกจาก "Discovery":
  1. ข้อมูลที่มีตอนนี้ (research/data/XAUUSDVIP_M1_202607010100_202607072151.csv)
     ยาวแค่ ~6,500 แท่ง M1 (ราว 1 สัปดาห์) — ทุก hypothesis ใน
     research/hypotheses/ ระบุไว้ชัดเจนว่าต้องการข้อมูลระดับเดือน-ปีเพื่อให้
     sample size พอสรุปทางสถิติได้ (ดู Failure Condition ของแต่ละข้อ)
  2. บาง hypothesis (เช่น F3) ต้องใช้ empirical distribution ของ streak length
     จากข้อมูลยาวหลายปีมาหา percentile ที่แท้จริง — ข้อมูล 1 สัปดาห์ทำแบบนั้น
     ไม่ได้ จึงใช้ threshold ตายตัวแทนชั่วคราว (ระบุไว้ในแต่ละคลาสว่าง่ายกว่า
     spec เต็มตรงไหน)
  3. เป้าหมายของสคริปต์นี้คือ "พิสูจน์ว่า pipeline ทำงานถูกต้องบนข้อมูลจริง"
     (โหลดข้อมูล -> เข้า/ออกไม่มี look-ahead -> คิดต้นทุนจริง -> สถิติออกมา
     สมเหตุสมผล) ไม่ใช่ "สรุปว่า hypothesis ไหนมี edge" — ผลลัพธ์จากรอบนี้
     **ห้ามใช้ตัดสิน ACCEPT/REJECT ใดๆ ทั้งสิ้น** ต้องรอข้อมูลยาวกว่านี้ก่อน

รัน:
    PYTHONPATH=. python3 research/pilot/run_pilot_2026w27.py
"""
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.hypothesis_backtest_engine import (  # noqa: E402
    BUY, SELL, Bar, CostModel, Signal, Strategy, load_ohlc_csv, run, show, stats,
    stress_test, monte_carlo_trade_order,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / \
    "XAUUSDVIP_M1_202607010100_202607072151.csv"

# สมมติฐาน GMT offset: docs/EXNESS_vs_VTMARKETS.md ระบุ VT Markets ฤดูร้อน (มี.ค.-ต.ค.)
# = GMT+3 และไฟล์นี้ชื่อ "XAUUSDVIP" ตรงกับสัญลักษณ์ VT Markets VIP ที่เอกสารอ้างถึง
# กรกฎาคมอยู่ในฤดูร้อน จึงสมมติ GMT+3 — **ยังไม่ได้ยืนยันด้วย BrokerProbe.mq5 จริง**
# ถ้าค่านี้ผิด ผลทุก hypothesis ที่ผูกกับ session (ไม่มีในชุด pilot นี้อยู่แล้ว
# เพราะ A1/G1/F3 ไม่ได้กรอง session) จะไม่กระทบ แต่ analysis อื่นในอนาคตต้อง
# ยืนยัน offset นี้ก่อนเสมอ
SERVER_GMT_OFFSET = 3

# ต้นทุนจากคอลัมน์ spread จริงในไฟล์ (เฉลี่ย ~30 จุด = ~$0.30 ที่ digits=2)
# ไม่ได้ผูกกับ spread รายแท่ง (เอนจินยังไม่รองรับ per-bar cost) ใช้ค่าเฉลี่ยแทน
# เป็นการประมาณ ไม่ใช่ต้นทุนที่แม่นยำระดับไม้ต่อไม้
AVG_SPREAD_PRICE_UNITS = 0.30
COMMISSION_ROUND_TRIP = 0.07   # ประมาณจาก Exness Raw ตาม docs (VT ไม่มีคอมฯ แยก)
SLIPPAGE = 0.05


# --------------------------------------------------------------------- A1
class PilotLiquiditySweepReversal(Strategy):
    """เวอร์ชันย่อของ A1 (research/hypotheses/A_liquidity.md)

    ตัดจากสเปกเต็ม: ใช้ fractal แบบง่าย (2 แท่งซ้าย-ขวา) แทน swing detection
    เต็มรูปแบบ, TP เป็น fixed R-multiple แทน "liquidity pool ถัดไป" (เพราะยังไม่
    implement swing-tracking ระยะไกล) — ยังคงตรรกะหลัก: sweep แล้ว reclaim
    เข้าสวนทาง ไม่ใช่ straddle ทั้งสองฝั่ง (ไม่ขัด FORBIDDEN_LOGIC.md)
    """
    warmup_bars = 20

    def __init__(self, fractal_n: int = 5, wick_ratio: float = 0.55, r_multiple: float = 1.5):
        self.fractal_n = fractal_n
        self.wick_ratio = wick_ratio
        self.r_multiple = r_multiple

    def _last_swing_high(self, bars: List[Bar], i: int) -> Optional[float]:
        n = self.fractal_n
        for j in range(i - n, n, -1):
            window = bars[j - n:j + n + 1]
            if bars[j].high == max(b.high for b in window):
                return bars[j].high
        return None

    def _last_swing_low(self, bars: List[Bar], i: int) -> Optional[float]:
        n = self.fractal_n
        for j in range(i - n, n, -1):
            window = bars[j - n:j + n + 1]
            if bars[j].low == min(b.low for b in window):
                return bars[j].low
        return None

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < self.warmup_bars:
            return None
        bar = bars[i]
        rng = bar.high - bar.low
        if rng <= 0:
            return None
        body = abs(bar.close - bar.open)

        swing_high = self._last_swing_high(bars, i - 1)
        if swing_high and bar.high > swing_high:
            upper_wick = bar.high - max(bar.open, bar.close)
            if upper_wick / rng >= self.wick_ratio and bar.close < swing_high:
                risk = bar.high - bar.close
                if risk > 0:
                    sl = bar.high + risk * 0.2
                    tp = bar.close - risk * self.r_multiple
                    return Signal(side=SELL, sl=sl, tp=tp, max_hold_bars=60, tag="A1_sweep_high")

        swing_low = self._last_swing_low(bars, i - 1)
        if swing_low and bar.low < swing_low:
            lower_wick = min(bar.open, bar.close) - bar.low
            if lower_wick / rng >= self.wick_ratio and bar.close > swing_low:
                risk = bar.close - bar.low
                if risk > 0:
                    sl = bar.low - risk * 0.2
                    tp = bar.close + risk * self.r_multiple
                    return Signal(side=BUY, sl=sl, tp=tp, max_hold_bars=60, tag="A1_sweep_low")
        return None


# --------------------------------------------------------------------- G1
class PilotMomentumBurst(Strategy):
    """เวอร์ชันย่อของ G1 (research/hypotheses/G_momentum.md)

    ตัดจากสเปกเต็ม: ใช้ threshold ตายตัว (ผ่าน constructor) แทนการคำนวณ 95th
    percentile จาก rolling distribution จริง เพราะ 1 สัปดาห์ยังไม่พอสร้าง
    distribution ที่เชื่อถือได้ — ต้องกลับมา calibrate percentile ใหม่เมื่อมี
    ข้อมูลยาวกว่านี้
    """
    warmup_bars = 20

    def __init__(self, n_bars: int = 3, return_threshold: float = 3.5,
                 body_ratio: float = 0.6, r_multiple: float = 1.2):
        self.n_bars = n_bars
        self.return_threshold = return_threshold
        self.body_ratio = body_ratio
        self.r_multiple = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < self.n_bars:
            return None
        bar = bars[i]
        rng = bar.high - bar.low
        if rng <= 0:
            return None
        body = abs(bar.close - bar.open)
        ret = bar.close - bars[i - self.n_bars].close

        if body / rng < self.body_ratio:
            return None
        if abs(ret) < self.return_threshold:
            return None

        side = BUY if ret > 0 else SELL
        start_price = bars[i - self.n_bars].close
        risk = abs(bar.close - start_price)
        if risk <= 0:
            return None
        sl = start_price
        tp = bar.close + risk * self.r_multiple * side
        return Signal(side=side, sl=sl, tp=tp, max_hold_bars=15, tag="G1_burst")


# --------------------------------------------------------------------- F3
class PilotStreakOverextension(Strategy):
    """เวอร์ชันย่อของ F3 (research/hypotheses/F_mean_reversion.md)

    ตัดจากสเปกเต็ม: ใช้ streak length ตายตัว (constructor) แทน 95th percentile
    ของ empirical distribution จริง (เหตุผลเดียวกับ G1 — sample ไม่พอ)
    """
    warmup_bars = 15

    def __init__(self, streak_len: int = 6, retrace_r: float = 0.5):
        self.streak_len = streak_len
        self.retrace_r = retrace_r

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < self.streak_len:
            return None
        closes = [bars[j].close for j in range(i - self.streak_len, i + 1)]
        diffs = [closes[k + 1] - closes[k] for k in range(len(closes) - 1)]
        if all(d > 0 for d in diffs):
            side = SELL
        elif all(d < 0 for d in diffs):
            side = BUY
        else:
            return None

        bar = bars[i]
        streak_start = closes[0]
        move = abs(bar.close - streak_start)
        if move <= 0:
            return None
        sl = (bar.close + move * 0.15) if side == SELL else (bar.close - move * 0.15)
        tp = (bar.close - move * self.retrace_r) if side == SELL else (bar.close + move * self.retrace_r)
        return Signal(side=side, sl=sl, tp=tp, max_hold_bars=30, tag="F3_streak")


def main() -> int:
    print("=== PILOT RUN — ข้อมูลจริง 1 สัปดาห์ (2026-06-30 ถึง 2026-07-07 UTC) ===")
    print("*** ผลลัพธ์นี้ preliminary เท่านั้น ห้ามใช้ตัดสิน ACCEPT/REJECT ***\n")

    bars = load_ohlc_csv(str(DATA_PATH), server_gmt_offset=SERVER_GMT_OFFSET)
    cost = CostModel(spread_points=AVG_SPREAD_PRICE_UNITS,
                      commission_round_trip=COMMISSION_ROUND_TRIP,
                      slippage=SLIPPAGE)

    strategies = {
        "A1 Liquidity Sweep Reversal (pilot)": lambda: PilotLiquiditySweepReversal(),
        "G1 Momentum Burst Continuation (pilot)": lambda: PilotMomentumBurst(),
        "F3 Streak Overextension (pilot)": lambda: PilotStreakOverextension(),
    }

    results = {}
    for name, factory in strategies.items():
        deals, equity = run(bars, factory(), cost)
        s = stats(deals, start_balance=10_000)
        show(s, name)
        results[name] = (deals, s)

        if s["trades"] >= 5:
            mc = monte_carlo_trade_order(deals, start_balance=10_000, n_runs=1000, seed=7)
            print(f"  Monte Carlo (trade-order, {mc['runs']} รอบ): "
                  f"final p5/p50/p95 = {mc['final_balance_p5']:.2f}/"
                  f"{mc['final_balance_p50']:.2f}/{mc['final_balance_p95']:.2f}  "
                  f"maxDD p50/p95 = {mc['max_dd_p50']:.1f}%/{mc['max_dd_p95']:.1f}%")
            st = stress_test(bars, factory, cost)
            print("  Stress (spread x2 / slippage x3 / commission x2):", end=" ")
            print(f"net={st['spread_x2']['net']:+.2f}/{st['slippage_x3']['net']:+.2f}/"
                  f"{st['commission_x2']['net']:+.2f}  (base net={s['net']:+.2f})")
        else:
            print("  ไม้น้อยเกิน 5 ไม้ — ข้าม Monte Carlo/Stress (ค่าจะไม่มีความหมายทางสถิติ)")
        print()

    print("=== จบ pilot run — ทุกตัวเลขข้างบนคือ sample size ระดับ 1 สัปดาห์ ===")
    print("=== ต้องมีข้อมูลยาวกว่านี้มากก่อนจะเรียกว่า Statistical Discovery ได้จริง ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
