#!/usr/bin/env python3
"""ตัวจำลองอ้างอิงของ MQL5/Experts/XAU_LadderGrid.mq5 (สมมติฐาน H-GRID1)

ทำอะไร
  - จำลองกฎเดียวกับ EA: เริ่ม basket เมื่อราคายืดจาก EMA(M5) เกิน stretch x ATR,
    เปิดทีละชั้นห่างกัน step, ชั้นละหลาย order ที่ TP ต่างกัน, มี basket stop (SL เดียวกันทุก order),
    คำนวณ lot จากขาดทุนสูงสุดตอนชน basket stop, มีเพดาน daily loss / max DD
  - ใช้ tick แบบ bid/ask จริง (เข้าฝั่งเดียวกับที่โบรกจับ: ขายที่ Bid ปิดที่ Ask, ซื้อที่ Ask ปิดที่ Bid)

ข้อจำกัดที่ต้องรู้
  - เป็น "แบบจำลองของกฎ" ไม่ใช่ Strategy Tester: ไม่มี margin call, ไม่มี slippage นอกจากช่อง gap ของ tick,
    ไม่มี swap, และ TP ถือว่าได้ราคา TP พอดีเมื่อ tick ข้ามไป
  - ผล synthetic (--synthetic) ใช้ดู "รูปทรงความเสี่ยง" เท่านั้น ห้ามใช้เป็นหลักฐาน edge

ใช้:
    python3 tools/ladder_grid_sim.py ticks.csv --server-gmt 3 --equity 12000
    python3 tools/ladder_grid_sim.py --synthetic
ticks.csv = server_time,bid,ask (สร้างจาก MQL5/Scripts/ExportSessionTicks.mq5)
"""
import argparse
import calendar
import math
import os
import random
import sys
from dataclasses import dataclass, replace
from typing import Optional

CONTRACT = 100.0  # ออนซ์ต่อ 1 lot ของ XAUUSD -> ราคาขยับ $1 = $100 ต่อ 1 lot


@dataclass(frozen=True)
class Params:
    direction: str = "both"            # sell | buy | both
    ema_period: int = 100
    atr_period: int = 14
    stretch_atr: float = 2.0
    tf_sec: int = 300                  # M5
    step: float = 10.0                 # ดอลลาร์/ออนซ์
    max_levels: int = 3
    ladder: tuple = (1.0, 2.0, 4.0)    # TP ของแต่ละ order = ตัวคูณ x step (จำนวนค่า = order ต่อชั้น)
    stop_buffer: float = 15.0          # basket stop = เกินชั้นสุดท้ายอีกเท่านี้
    max_spread: float = 0.6
    lot: float = 0.0                   # 0 = คำนวณจาก risk_pct, >0 = fixed
    risk_pct: float = 2.0
    hard_risk_pct: float = 10.0
    slip_usd: float = 0.5
    lot_min: float = 0.01
    lot_step: float = 0.01
    lot_max: float = 0.10
    max_total_lots: float = 0.30
    cooldown_sec: int = 900
    daily_loss_pct: Optional[float] = 3.0
    max_dd_pct: Optional[float] = 10.0
    commission_per_lot_side: float = 0.0
    start_equity: float = 300.0


# ---------------------------------------------------------------- ขนาดไม้ / เพดาน
def stop_distance(p: Params) -> float:
    """ระยะจาก anchor ถึง basket stop"""
    return (p.max_levels - 1) * p.step + p.stop_buffer


def worst_case_per_lot(p: Params, spread: float) -> float:
    """ขาดทุนสูงสุดต่อ 1 lot (ต่อ order) ถ้าเปิดครบทุกชั้นแล้วชน basket stop
    ชั้น k เข้าที่ anchor + k x step จึงห่างจาก stop = stop_distance - k x step
    เผื่อ spread + slippage ต่อ order (แบบอนุรักษ์นิยม)"""
    n = len(p.ladder)
    per_oz = 0.0
    for k in range(p.max_levels):
        per_oz += n * ((stop_distance(p) - k * p.step) + spread + p.slip_usd)
    return per_oz * CONTRACT


def size_lot(p: Params, equity: float, spread: float) -> float:
    """lot ต่อ order  คืน 0.0 = ปฏิเสธ (ไม่ปัดขึ้นให้เสี่ยงเกิน)"""
    n = len(p.ladder)
    wc = worst_case_per_lot(p, spread)
    lot = p.lot if p.lot > 0 else equity * p.risk_pct / 100.0 / wc
    lot = min(lot, p.lot_max, p.max_total_lots / (n * p.max_levels))
    lot = math.floor(lot / p.lot_step + 1e-9) * p.lot_step
    if lot < p.lot_min - 1e-12:
        return 0.0
    if lot * wc > equity * p.hard_risk_pct / 100.0:
        return 0.0
    return round(lot, 2)


def required_equity(p: Params, lot: float, spread: float, risk_pct: float) -> float:
    return lot * worst_case_per_lot(p, spread) / (risk_pct / 100.0)


# ---------------------------------------------------------------- ตัวจำลอง
def simulate(times, bids, asks, p: Params):
    """times เป็นวินาที (float) เรียงเวลา  คืน dict ผลลัพธ์"""
    n_ord = len(p.ladder)
    balance = p.start_equity
    positions, trades, baskets = [], [], []
    basket = None
    cooldown_until = -1.0
    dd_halted = False
    halt_day = None
    day = None
    day_start_eq = balance
    peak = min_eq = balance
    max_dd = 0.0
    refusals = 0
    max_open_pos = 0
    max_open_lots = 0.0
    n_halts = 0

    bucket = None
    bar_h = bar_l = bar_c = 0.0
    prev_close = None
    ema = atr = None
    trs = []
    nbars = 0
    alpha = 2.0 / (p.ema_period + 1)

    def close_pos(pos, exit_px, why, t):
        nonlocal balance
        gross = (pos["entry"] - exit_px) if pos["dir"] == -1 else (exit_px - pos["entry"])
        pnl = gross * pos["lot"] * CONTRACT - 2 * p.commission_per_lot_side * pos["lot"]
        balance += pnl
        trades.append({"open_t": pos["open_t"], "close_t": t, "dir": pos["dir"], "level": pos["level"],
                       "lot": pos["lot"], "entry": pos["entry"], "exit": exit_px, "why": why, "pnl": pnl,
                       "basket": pos["basket"]})

    for i in range(len(times)):
        t, bid, ask = times[i], bids[i], asks[i]

        # ---- แท่ง M5 ที่ปิดแล้ว (ใช้ค่าเฉพาะแท่งที่ปิด ไม่มี look-ahead)
        b = int(t // p.tf_sec)
        if bucket is None:
            bucket, bar_h, bar_l, bar_c = b, bid, bid, bid
        elif b != bucket:
            c = bar_c
            ema = c if ema is None else ema + alpha * (c - ema)
            tr = bar_h - bar_l if prev_close is None else max(
                bar_h - bar_l, abs(bar_h - prev_close), abs(bar_l - prev_close))
            nbars += 1
            if atr is None:
                trs.append(tr)
                if len(trs) >= p.atr_period:
                    atr = sum(trs) / len(trs)
            else:
                atr = (atr * (p.atr_period - 1) + tr) / p.atr_period
            prev_close = c
            bucket, bar_h, bar_l, bar_c = b, bid, bid, bid
        else:
            bar_h = max(bar_h, bid)
            bar_l = min(bar_l, bid)
            bar_c = bid

        # ---- ออกจากไม้ (TP / SL)
        if positions:
            keep = []
            for pos in positions:
                if pos["dir"] == -1:
                    if ask >= pos["sl"]:
                        close_pos(pos, ask, "SL", t)
                    elif ask <= pos["tp"]:
                        close_pos(pos, pos["tp"], "TP", t)
                    else:
                        keep.append(pos)
                else:
                    if bid <= pos["sl"]:
                        close_pos(pos, bid, "SL", t)
                    elif bid >= pos["tp"]:
                        close_pos(pos, pos["tp"], "TP", t)
                    else:
                        keep.append(pos)
            positions = keep

        # ---- equity + เพดานรายวัน / DD
        floating = 0.0
        for pos in positions:
            px = (pos["entry"] - ask) if pos["dir"] == -1 else (bid - pos["entry"])
            floating += px * pos["lot"] * CONTRACT
        equity = balance + floating
        d = int(t // 86400)
        if d != day:
            day = d
            day_start_eq = equity
            halt_day = None
        peak = max(peak, equity)
        min_eq = min(min_eq, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
        if positions:
            hit = None
            if p.daily_loss_pct and day_start_eq > 0 and \
                    (day_start_eq - equity) / day_start_eq * 100.0 >= p.daily_loss_pct:
                hit, halt_day = "HALT_DAILY", d
            elif p.max_dd_pct and peak > 0 and (peak - equity) / peak * 100.0 >= p.max_dd_pct:
                hit, dd_halted = "HALT_DD", True
            if hit:
                n_halts += 1
                for pos in positions:
                    close_pos(pos, ask if pos["dir"] == -1 else bid, hit, t)
                positions = []

        # ---- basket จบ
        if basket is not None and not positions:
            mine = [x for x in trades if x["basket"] == basket["id"]]
            baskets.append({"id": basket["id"], "dir": basket["dir"], "open_t": basket["open_t"], "close_t": t,
                            "levels": basket["level"] + 1, "pnl": sum(x["pnl"] for x in mine),
                            "stopped": any(x["why"] == "SL" for x in mine),
                            "halted": any(x["why"].startswith("HALT") for x in mine)})
            basket = None
            cooldown_until = t + p.cooldown_sec

        spread = ask - bid
        # ---- เปิดชั้นถัดไป
        if basket is not None and basket["level"] + 1 <= p.max_levels - 1 and spread <= p.max_spread:
            k = basket["level"] + 1
            if basket["dir"] == -1:
                ok = bid >= basket["anchor"] + k * p.step and bid < basket["sl"]
                entry = bid
            else:
                ok = ask <= basket["anchor"] - k * p.step and ask > basket["sl"]
                entry = ask
            if ok:
                for mult in p.ladder:
                    positions.append({"dir": basket["dir"], "entry": entry, "lot": basket["lot"],
                                      "tp": entry + basket["dir"] * mult * p.step,
                                      "sl": basket["sl"], "level": k, "open_t": t, "basket": basket["id"]})
                basket["level"] = k
                max_open_pos = max(max_open_pos, len(positions))
                max_open_lots = max(max_open_lots, sum(x["lot"] for x in positions))

        # ---- เริ่ม basket ใหม่
        elif basket is None and ema is not None and atr is not None and nbars >= p.ema_period \
                and not dd_halted and halt_day != d and t >= cooldown_until and spread <= p.max_spread:
            direction = 0
            if p.direction in ("sell", "both") and bid >= ema + p.stretch_atr * atr:
                direction = -1
            elif p.direction in ("buy", "both") and bid <= ema - p.stretch_atr * atr:
                direction = 1
            if direction:
                lot = size_lot(p, equity, spread)
                if lot <= 0:
                    refusals += 1
                else:
                    entry = bid if direction == -1 else ask
                    sl = entry - direction * stop_distance(p)
                    basket = {"id": len(baskets) + 1, "dir": direction, "anchor": entry, "sl": sl, "lot": lot,
                              "level": 0, "open_t": t}
                    for mult in p.ladder:
                        positions.append({"dir": direction, "entry": entry, "lot": lot,
                                          "tp": entry + direction * mult * p.step, "sl": sl, "level": 0,
                                          "open_t": t, "basket": basket["id"]})
                    max_open_pos = max(max_open_pos, len(positions))
                    max_open_lots = max(max_open_lots, sum(x["lot"] for x in positions))

    # ปิดของค้างท้ายข้อมูลที่ราคาตลาด (นับเป็นผลจริง)
    if positions:
        t, bid, ask = times[-1], bids[-1], asks[-1]
        for pos in positions:
            close_pos(pos, ask if pos["dir"] == -1 else bid, "END", t)
        if basket is not None:
            mine = [x for x in trades if x["basket"] == basket["id"]]
            baskets.append({"id": basket["id"], "dir": basket["dir"], "open_t": basket["open_t"], "close_t": t,
                            "levels": basket["level"] + 1, "pnl": sum(x["pnl"] for x in mine),
                            "stopped": False, "halted": False})
    return {"trades": trades, "baskets": baskets, "balance": balance, "max_dd_pct": max_dd,
            "min_equity": min_eq, "refusals": refusals, "max_open_pos": max_open_pos,
            "max_open_lots": max_open_lots, "n_halts": n_halts, "start_equity": p.start_equity}


# ---------------------------------------------------------------- สรุปผล
def summarize(res) -> dict:
    pnl = [t["pnl"] for t in res["trades"]]
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x < 0]
    gl = -sum(losses)
    by_day = {}
    for t in res["trades"]:
        by_day[int(t["close_t"] // 86400)] = by_day.get(int(t["close_t"] // 86400), 0.0) + t["pnl"]
    net = sum(pnl)
    top2 = sum(sorted([v for v in by_day.values() if v > 0], reverse=True)[:2])
    bk = res["baskets"]
    return {
        "trades": len(pnl), "baskets": len(bk), "stopped": sum(1 for b in bk if b["stopped"]),
        "net": net, "pf": (sum(wins) / gl) if gl > 0 else None,
        "win_rate": 100.0 * len(wins) / len(pnl) if pnl else None,
        "expectancy": net / len(pnl) if pnl else None,
        "avg_win": sum(wins) / len(wins) if wins else None,
        "avg_loss": -gl / len(losses) if losses else None,
        "worst_basket": min((b["pnl"] for b in bk), default=0.0),
        "max_dd_pct": res["max_dd_pct"], "min_equity": res["min_equity"],
        "refusals": res["refusals"], "halts": res["n_halts"],
        "max_open_pos": res["max_open_pos"], "max_open_lots": res["max_open_lots"],
        "top2_day_share_pct": (100.0 * top2 / net) if net > 0 else None,
    }


# ---------------------------------------------------------------- ข้อมูลสังเคราะห์ (ดูรูปทรงความเสี่ยงเท่านั้น)
def make_ticks(segments, warm_sec=43200, base=4200.0, spread=0.3, sigma=0.15, seed=1, t0=1_800_000_000):
    """เดินเชิงเส้นตาม segments [(วินาที, ราคาเป้าหมาย), ...] หลังช่วงอุ่นเครื่อง + jitter แบบ AR(1)"""
    rng = random.Random(seed)
    times, bids, asks = [], [], []
    jitter = 0.0
    t = float(t0)

    def emit(mid):
        nonlocal jitter, t
        jitter = 0.97 * jitter + rng.gauss(0.0, sigma)
        m = mid + jitter
        times.append(t)
        bids.append(round(m - spread / 2, 3))
        asks.append(round(m + spread / 2, 3))
        t += 1.0

    for _ in range(int(warm_sec)):
        emit(base)
    cur = base
    for dur, target in segments:
        n = int(dur)
        for k in range(1, n + 1):
            emit(cur + (target - cur) * k / n)
        cur = target
    return times, bids, asks


def scenarios(base=4200.0):
    h = 3600
    return {
        "reversion (ยืดแล้วดึงกลับ)": [(1200, base + 22), (3 * h, base - 45), (h, base - 45)],
        "chop (วนกรอบ +-12)": sum([[(1200, base + 12), (1200, base - 12)] for _ in range(6)], []),
        "drop_day (ขึ้น 15 แล้วร่วง 140)": [(1800, base + 15), (h, base + 15), (6 * h, base - 125)],
        "rally (ไล่ขึ้น 90 ใน 3 ชม.)": [(3 * h, base + 90), (h, base + 90)],
        "rally_long (ไล่ขึ้น 180 ใน 8 ชม.)": [(8 * h, base + 180), (h, base + 180)],
    }


def run_synthetic():
    eq = 20000.0
    capped = Params(start_equity=eq)
    capped_sell = replace(capped, direction="sell")
    # ตะแกรงไม่มีเพดาน (สมมติ): lot คงที่ 0.01, 10 ชั้น, ไม่มี basket stop, ไม่มี daily loss / DD guard
    unc = replace(capped_sell, lot=0.01, max_levels=10, stop_buffer=1e9, daily_loss_pct=None, max_dd_pct=None,
                  hard_risk_pct=math.inf, max_total_lots=10.0, cooldown_sec=0)
    variants = (("capped ทั้งสองทิศ", capped), ("capped sell อย่างเดียว", capped_sell),
                ("uncapped sell (ทุน 20k)", unc), ("uncapped sell (ทุน 300)", replace(unc, start_equity=300.0)))
    print(f"{'สถานการณ์':36s} {'แบบ':26s} {'net':>9s} {'minEq':>10s} {'maxDD%':>7s} {'basket':>6s} {'stop':>4s} {'refuse':>6s}")
    for name, seg in scenarios().items():
        tk = make_ticks(seg)
        for label, prm in variants:
            s = summarize(simulate(*tk, prm))
            print(f"{name:36s} {label:26s} {s['net']:9.1f} {s['min_equity']:10.1f} {s['max_dd_pct']:7.1f} "
                  f"{s['baskets']:6d} {s['stopped']:4d} {s['refusals']:6d}")
    print("\nหมายเหตุ: ข้อมูลสังเคราะห์ ใช้ดูรูปทรงความเสี่ยงเท่านั้น ไม่ใช่หลักฐานว่ามี edge")


def load_csv(path, server_gmt):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ea_backtest_engine import load_ticks
    times, bids, asks = load_ticks(path, server_gmt)
    return [float(calendar.timegm(t.timetuple())) for t in times], bids, asks


def main():
    ap = argparse.ArgumentParser(description="จำลอง XAU_LadderGrid (H-GRID1)")
    ap.add_argument("ticks", nargs="?", help="CSV: server_time,bid,ask")
    ap.add_argument("--synthetic", action="store_true", help="รันสถานการณ์สังเคราะห์เทียบ capped/uncapped")
    ap.add_argument("--server-gmt", type=int, default=0)
    ap.add_argument("--equity", type=float, default=300.0)
    ap.add_argument("--direction", default="both", choices=["sell", "buy", "both"])
    ap.add_argument("--step", type=float, default=10.0)
    ap.add_argument("--levels", type=int, default=3)
    ap.add_argument("--ladder", default="1,2,4", help="ตัวคูณ TP ต่อ order คั่นด้วย comma")
    ap.add_argument("--buffer", type=float, default=15.0)
    ap.add_argument("--stretch", type=float, default=2.0)
    ap.add_argument("--risk-pct", type=float, default=2.0)
    ap.add_argument("--lot", type=float, default=0.0)
    ap.add_argument("--commission", type=float, default=0.0, help="ต่อ lot ต่อด้าน (Exness Raw = 3.5)")
    a = ap.parse_args()
    if a.synthetic:
        return run_synthetic()
    if not a.ticks:
        ap.error("ต้องระบุไฟล์ ticks หรือใช้ --synthetic")
    p = Params(direction=a.direction, step=a.step, max_levels=a.levels,
               ladder=tuple(float(x) for x in a.ladder.split(",")), stop_buffer=a.buffer,
               stretch_atr=a.stretch, risk_pct=a.risk_pct, lot=a.lot, start_equity=a.equity,
               commission_per_lot_side=a.commission)
    wc = worst_case_per_lot(p, 0.3)
    print(f"ขาดทุนสูงสุดต่อ basket ที่ 0.01 lot ~ ${wc * 0.01:,.0f}  "
          f"(ทุนที่ต้องมีเพื่อเสี่ยง {p.risk_pct}% ~ ${required_equity(p, 0.01, 0.3, p.risk_pct):,.0f})")
    times, bids, asks = load_csv(a.ticks, a.server_gmt)
    s = summarize(simulate(times, bids, asks, p))
    for k, v in s.items():
        print(f"{k:22s} {v if not isinstance(v, float) else round(v, 3)}")


if __name__ == "__main__":
    main()
