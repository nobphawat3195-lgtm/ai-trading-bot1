#!/usr/bin/env python3
"""Pilot run ทั้ง 30 hypotheses บนข้อมูลจริง 1 สัปดาห์ (2026-06-30 ถึง 2026-07-07 UTC)

**PILOT เท่านั้น — ไม่ใช่ Statistical Discovery** เหตุผลเดียวกับ
research/pilot/PILOT_RESULTS_2026-07-01_to_07.md: sample เล็กเกิน, strategy เป็น
เวอร์ชันตัดทอน (ดู research/pilot/common.py และ hypotheses_pilot.py), C3/D1-D3/H1-H3
ข้ามไปเพราะต้องการข้อมูลยาวกว่านี้มาก (ดู NOT_TESTABLE ใน hypotheses_pilot.py)

รัน:
    PYTHONPATH=. python3 research/pilot/run_pilot_all30.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.hypothesis_backtest_engine import CostModel, load_ohlc_csv, run, stats  # noqa: E402
from research.pilot.hypotheses_pilot import ALL_PILOT_STRATEGIES, NOT_TESTABLE  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / \
    "XAUUSDVIP_M1_202607010100_202607072151.csv"
SERVER_GMT_OFFSET = 3  # สมมติ VT Markets ฤดูร้อน — ดูคำเตือนใน run_pilot_2026w27.py

AVG_SPREAD_PRICE_UNITS = 0.30
COMMISSION_ROUND_TRIP = 0.07
SLIPPAGE = 0.05


def h4_session_autocorrelation(bars):
    """H4 ไม่ใช่ trading strategy — เป็น correlation test ล้วนๆ วัด correlation ระหว่าง
    return ของ session ก่อนหน้ากับ session ถัดไป (Asian->London ในสัปดาห์นี้)
    sample มีแค่ราว 5-7 คู่ — รายงานตัวเลขได้แต่ไม่มีนัยสำคัญทางสถิติเลย
    """
    from research.pilot.common import today_session_high_low  # noqa
    days = sorted({b.time.date() for b in bars})
    pairs = []
    for d in days:
        asian_closes = [b.close for b in bars if b.time.date() == d and 0 <= b.time.hour < 7]
        london_closes = [b.close for b in bars if b.time.date() == d and 7 <= b.time.hour < 16]
        if len(asian_closes) < 2 or len(london_closes) < 2:
            continue
        asian_ret = asian_closes[-1] - asian_closes[0]
        london_ret = london_closes[-1] - london_closes[0]
        pairs.append((asian_ret, london_ret))
    if len(pairs) < 3:
        return None, len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None, len(pairs)
    return cov / (sx * sy), len(pairs)


def main() -> int:
    print("=== PILOT RUN ทั้ง 30 hypotheses — ข้อมูลจริง 1 สัปดาห์ ===")
    print("*** ผลลัพธ์นี้ preliminary เท่านั้น ห้ามใช้ตัดสิน ACCEPT/REJECT ***\n")

    bars = load_ohlc_csv(str(DATA_PATH), server_gmt_offset=SERVER_GMT_OFFSET)
    cost = CostModel(spread_points=AVG_SPREAD_PRICE_UNITS,
                      commission_round_trip=COMMISSION_ROUND_TRIP, slippage=SLIPPAGE)

    rows = []
    for hid, cls in ALL_PILOT_STRATEGIES.items():
        try:
            deals, _ = run(bars, cls(), cost)
            s = stats(deals, start_balance=10_000)
            rows.append((hid, s["trades"], s["net"], s["pf"], s["wr"], s["avg_r"], s["dd_pct"]))
        except Exception as e:  # noqa: BLE001 — pilot: อยากเห็นทุกตัวแม้บางตัว error
            rows.append((hid, "ERROR", str(e), None, None, None, None))
            traceback.print_exc()

    print(f"{'ID':<5}{'ไม้':>6}{'สุทธิ':>12}{'PF':>7}{'ชนะ%':>8}{'R เฉลี่ย':>10}{'DD%':>7}")
    print("-" * 60)
    for hid, trades, net, pf, wr, avg_r, dd in rows:
        if trades == "ERROR":
            print(f"{hid:<5}  ERROR: {net}")
            continue
        if trades == 0:
            print(f"{hid:<5}{trades:>6}   ไม่มีไม้เลยในหน้าต่างข้อมูลนี้")
            continue
        print(f"{hid:<5}{trades:>6}{net:>12.2f}{pf:>7.2f}{wr:>8.1f}{avg_r:>+10.2f}{dd:>7.1f}")

    print(f"\n=== ข้ามไป {len(NOT_TESTABLE)} hypotheses (ต้องการข้อมูลยาวกว่า 1 สัปดาห์มาก) ===")
    for hid, reason in NOT_TESTABLE.items():
        print(f"  {hid}: {reason}")

    corr, n = h4_session_autocorrelation(bars)
    print(f"\n=== H4 (correlation test, ไม่ใช่ trading strategy) ===")
    if corr is None:
        print(f"  sample ไม่พอคำนวณ (n={n})")
    else:
        print(f"  Asian->London return correlation = {corr:+.3f}  (n={n} คู่ — "
              "เล็กเกินกว่าจะมีนัยสำคัญทางสถิติ ห้ามตีความเป็น edge)")

    print("\n=== จบ pilot run ทั้ง 30 — sample size ระดับ 1 สัปดาห์เท่านั้น ===")
    print("=== ต้องมีข้อมูลยาวกว่านี้มากก่อนจะเรียกว่า Statistical Discovery ได้จริง ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
