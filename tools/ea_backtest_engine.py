#!/usr/bin/env python3
"""EA Auto Backtest Engine — ตัวจำลอง XAU StraddleReverse บนข้อมูลราคาจริง

ทำไมต้องมีตัวนี้ทั้งที่มี Strategy Tester อยู่แล้ว:
  Strategy Tester รันได้ครั้งละชุดค่า ถ้าอยากรู้ว่า "หน้าต่างเวลาไหนคือของจริง"
  ต้องนั่งกดรันทีละรอบ 96 รอบ  ตัวนี้กวาดให้จบในคำสั่งเดียว (โหมด --sweep-window)
  และใส่ค่าคอมมิชชัน/สลิปเพจของโบรกใหม่ได้โดยไม่ต้องมีบัญชีโบรกนั้น

ข้อมูลเข้า:
  CSV จาก MQL5/Scripts/ExportSessionTicks.mq5  ->  server_time,bid,ask

ใช้ยังไง
--------
รันชุดค่าเดียว (ค่าเริ่มต้น = ค่า v5.00):
    python3 tools/ea_backtest_engine.py ticks.csv --server-gmt 3

กวาดหน้าต่างเวลาทั้ง 24 ชม. ทีละ 15 นาที -- ตอบคำถาม DST:
    python3 tools/ea_backtest_engine.py ticks.csv --server-gmt 3 --sweep-window

ออกไฟล์ deals ให้เอาไปทำกราฟต่อ:
    python3 tools/ea_backtest_engine.py ticks.csv --server-gmt 3 --out-deals deals.csv
    python3 tools/mt5_report_charts.py deals.csv -o charts/   # รับ .csv ได้ด้วย

ข้อจำกัดที่ต้องรู้
-----------------
  * ข้อมูลความละเอียด 1 วินาที ไม่ใช่ทุก tick -- ราคาที่วิ่งผ่านไปมาภายในวินาที
    เดียวกันมองไม่เห็น ตัวเลขจึงไม่เท่ากับ Strategy Tester เป๊ะ
  * ในวินาทีที่ทั้ง SL และไม้กลับด้านโดนพร้อมกัน ตัวจำลองเลือก SL ก่อนเสมอ
    (มองโลกในแง่ร้าย) ปิดด้วย --optimistic ได้ถ้าอยากดูอีกด้าน
  * ใช้เทียบชุดค่ากันเอง (A/B) ได้ดี  แต่เลขกำไรสัมบูรณ์ให้ยึด Strategy Tester
"""
import argparse
import csv
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

BUY, SELL = 1, -1
_UNSET = object()
CONTRACT = 100.0          # XAUUSD 1 ล็อต = 100 ออนซ์


# ------------------------------------------------------------------ ค่าตั้ง
@dataclass
class Params:
    # หน้าต่างเวลา (นาทีของวัน ตาม UTC)
    win_start: int = 19 * 60
    win_end: int = 20 * 60 + 30
    close_at_session_end: bool = True
    # ระยะ (ดอลลาร์ต่อออนซ์)
    straddle_dist: float = 1.00
    stop_loss: float = 12.00
    take_profit: float = 0.0
    reverse_start: float = 2.50
    reverse_gap: float = 2.40
    use_reverse: bool = True
    # เบรก
    cooldown_sec: int = 300
    max_sl_per_day: int = 4
    # ตัวกรอง
    max_spread: float = 0.60
    use_vol_filter: bool = True
    atr_fast: int = 14
    atr_slow: int = 60
    atr_expand_max: float = 0.95
    # ขนาดไม้ + ต้นทุน
    lot: float = 0.01
    commission_per_lot_side: float = 0.0   # Exness Raw = 3.5
    slippage: float = 0.0                  # ดอลลาร์/ออนซ์ ต่อการเข้า-ออก 1 ครั้ง
    start_balance: float = 300.0
    pessimistic: bool = True


# ------------------------------------------------------------- โหลดข้อมูล
def load_ticks(path, server_gmt):
    """อ่าน CSV แล้วแปลงเวลาเซิร์ฟเวอร์ -> UTC  คืนค่าเป็น list ขนาน 3 ชุด"""
    times, bids, asks = [], [], []
    shift = timedelta(hours=server_gmt)
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        rdr = csv.reader(fh)
        head = next(rdr, None)
        if head is None:
            raise SystemExit(f"ไฟล์ว่าง: {path}")
        if head and head[0].strip().lower().startswith("server_time"):
            pass                       # มีหัวตาราง ข้ามไปแล้ว
        else:
            rdr = _prepend(head, rdr)  # ไม่มีหัวตาราง เอาแถวแรกคืน
        for row in rdr:
            if len(row) < 3:
                continue
            t = _parse_time(row[0])
            if t is None:
                continue
            try:
                bid, ask = float(row[1]), float(row[2])
            except ValueError:
                continue
            if bid <= 0 or ask <= 0:
                continue
            times.append(t - shift)
            bids.append(bid)
            asks.append(ask)
    if not times:
        raise SystemExit(
            f"อ่านข้อมูลไม่ได้เลยจาก {path}\n"
            "  -> ต้องเป็น CSV 3 คอลัมน์: server_time,bid,ask\n"
            "     (สร้างจาก MQL5/Scripts/ExportSessionTicks.mq5)"
        )
    print(f"โหลด {len(times):,} แถว  {times[0]:%Y-%m-%d} ถึง {times[-1]:%Y-%m-%d}  (แปลงเป็น UTC แล้ว)")
    return times, bids, asks


def _prepend(row, it):
    yield row
    for r in it:
        yield r


def _parse_time(s):
    s = s.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


# ------------------------------------------------------- ตัวกรองความผันผวน
def build_atr_gate(times, bids, p):
    """สร้างตาราง 'นาทีไหนผ่านตัวกรอง ATR บ้าง' ล่วงหน้า แทนที่จะคำนวณซ้ำทุก tick

    ATR เร็ว ÷ ATR ช้า <= atr_expand_max  =  ความผันผวนกำลังหดตัว = เข้าได้
    """
    if not p.use_vol_filter:
        return None

    # ยุบเป็นแท่ง M1
    bars, cur_min, hi, lo, close = [], None, None, None, None
    for t, b in zip(times, bids):
        m = t.replace(second=0, microsecond=0)
        if m != cur_min:
            if cur_min is not None:
                bars.append((cur_min, hi, lo, close))
            cur_min, hi, lo = m, b, b
        hi = max(hi, b)
        lo = min(lo, b)
        close = b
    if cur_min is not None:
        bars.append((cur_min, hi, lo, close))

    gate, trs = {}, []
    prev_close = None
    fast_sum = slow_sum = 0.0
    for minute, hi, lo, close in bars:
        tr = hi - lo if prev_close is None else max(hi - lo, abs(hi - prev_close),
                                                    abs(lo - prev_close))
        prev_close = close
        trs.append(tr)
        fast_sum += tr
        slow_sum += tr
        if len(trs) > p.atr_fast:
            fast_sum -= trs[-p.atr_fast - 1]
        if len(trs) > p.atr_slow:
            slow_sum -= trs[-p.atr_slow - 1]
        if len(trs) >= p.atr_slow and slow_sum > 0:
            fast = fast_sum / p.atr_fast
            slow = slow_sum / p.atr_slow
            gate[minute] = (fast / slow) <= p.atr_expand_max
        else:
            gate[minute] = False       # ยังคำนวณไม่ได้ = ไม่เข้า
    return gate


# ------------------------------------------------------------------ เครื่อง
def run(times, bids, asks, p, gate=_UNSET):
    """เดินไปข้างหน้าทีละ tick คืน (list ของไม้ที่ปิดแล้ว, เส้นทุน)

    gate: ส่งตาราง ATR ที่คำนวณไว้แล้วเข้ามาได้ ตอนกวาดหลายหน้าต่างจะได้ไม่ต้อง
          คำนวณซ้ำทุกรอบ (ตัวกรองไม่ขึ้นกับหน้าต่างเวลา)
    """
    if gate is _UNSET:
        gate = build_atr_gate(times, bids, p)
    slip = p.slippage
    money = p.lot * CONTRACT                       # กำไร $ ต่อราคาขยับ 1.00
    comm = p.commission_per_lot_side * p.lot * 2   # ไป-กลับ

    pos = None            # dict(side, entry, sl, opened)
    pend = {}             # side -> ราคา trigger  (ตอนคร่อม มี 2 ฝั่ง)
    rev = None            # ราคา trigger ของไม้กลับด้าน
    cooldown_until = None
    sl_today, day = 0, None

    deals, equity = [], []
    balance = p.start_balance

    def close(t, price, reason):
        nonlocal pos, balance, rev, sl_today, cooldown_until
        pnl = (price - pos["entry"]) * pos["side"] * money - comm
        balance += pnl
        deals.append({"open_time": pos["opened"], "time": t, "side": pos["side"],
                      "entry": pos["entry"], "exit": price, "profit": pnl,
                      "reason": reason, "balance": balance})
        equity.append((t, balance))
        if reason == "sl":
            sl_today += 1
            cooldown_until = t + timedelta(seconds=p.cooldown_sec)
        pos = None
        rev = None

    def open_pos(t, side, price):
        nonlocal pos
        sl = price - p.stop_loss * side if p.stop_loss > 0 else None
        pos = {"side": side, "entry": price, "sl": sl, "opened": t}

    for i in range(len(times)):
        t, bid, ask = times[i], bids[i], asks[i]

        if day != t.date():
            day, sl_today = t.date(), 0

        mod = t.hour * 60 + t.minute
        in_session = (p.win_start <= mod < p.win_end if p.win_start <= p.win_end
                      else (mod >= p.win_start or mod < p.win_end))

        # ---------------- มีไม้อยู่ ----------------
        if pos:
            side = pos["side"]
            # ปิดท้ายช่วงเวลา
            if not in_session and p.close_at_session_end:
                close(t, bid if side == BUY else ask, "session_end")
                pend.clear()
                continue

            sl_hit = pos["sl"] is not None and (
                bid <= pos["sl"] if side == BUY else ask >= pos["sl"])
            rev_hit = rev is not None and (
                bid <= rev if side == BUY else ask >= rev)

            if sl_hit and (p.pessimistic or not rev_hit):
                close(t, pos["sl"] - slip * side, "sl")
                continue
            if rev_hit:
                fill = (min(rev, bid) - slip) if side == BUY else (max(rev, ask) + slip)
                close(t, fill, "reverse")
                open_pos(t, -side, fill)
                continue
            if sl_hit:
                close(t, pos["sl"] - slip * side, "sl")
                continue

            # ---- จัดการไม้ดักกลับด้าน ----
            if not p.use_reverse:
                continue
            profit = (bid - pos["entry"]) if side == BUY else (pos["entry"] - ask)
            if rev is None:
                if profit >= p.reverse_start and (ask - bid) <= p.max_spread:
                    rev = (bid - p.reverse_gap) if side == BUY else (ask + p.reverse_gap)
            else:
                # ไล่ตามราคา ขยับเข้าใกล้อย่างเดียว ไม่ถอยกลับ
                cand = (bid - p.reverse_gap) if side == BUY else (ask + p.reverse_gap)
                if (cand > rev) if side == BUY else (cand < rev):
                    rev = cand
            continue

        # ---------------- ไม่มีไม้ ----------------
        if not in_session:
            pend.clear()
            continue
        if cooldown_until and t < cooldown_until:
            pend.clear()
            continue
        if p.max_sl_per_day > 0 and sl_today >= p.max_sl_per_day:
            pend.clear()
            continue

        if pend:
            if BUY in pend and ask >= pend[BUY]:
                open_pos(t, BUY, max(pend[BUY], ask) + slip)
                pend.clear()
                continue
            if SELL in pend and bid <= pend[SELL]:
                open_pos(t, SELL, min(pend[SELL], bid) - slip)
                pend.clear()
                continue
            continue

        if (ask - bid) > p.max_spread:
            continue
        if gate is not None and not gate.get(t.replace(second=0, microsecond=0), False):
            continue
        pend = {BUY: ask + p.straddle_dist, SELL: bid - p.straddle_dist}

    return deals, equity


# ------------------------------------------------------------------ สถิติ
def stats(deals, p):
    if not deals:
        return {"trades": 0, "net": 0.0, "pf": 0.0, "wr": 0.0,
                "avg": 0.0, "dd_pct": 0.0, "end": p.start_balance}
    pnl = [d["profit"] for d in deals]
    wins = [x for x in pnl if x > 0]
    gross_l = -sum(x for x in pnl if x < 0)
    peak, dd = p.start_balance, 0.0
    for d in deals:
        peak = max(peak, d["balance"])
        dd = max(dd, (peak - d["balance"]) / peak * 100 if peak > 0 else 0.0)
    return {"trades": len(pnl), "net": sum(pnl),
            "pf": (sum(wins) / gross_l) if gross_l > 0 else float("inf"),
            "wr": len(wins) / len(pnl) * 100, "avg": sum(pnl) / len(pnl),
            "dd_pct": dd, "end": deals[-1]["balance"]}


def show(s, label=""):
    if label:
        print(f"\n── {label} ──")
    if not s["trades"]:
        print("  ไม่มีไม้เลย")
        return
    print(f"  ไม้ {s['trades']:>5}   สุทธิ ${s['net']:>+9.2f}   PF {s['pf']:>5.2f}   "
          f"ชนะ {s['wr']:>5.1f}%   ต่อไม้ ${s['avg']:>+6.3f}   DD {s['dd_pct']:>5.1f}%")


def write_deals(path, deals):
    """เขียนในรูปแบบเดียวกับตารางดีลของ MT5 เพื่อให้ mt5_report_charts.py อ่านต่อได้"""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Time", "Deal", "Symbol", "Type", "Direction", "Volume",
                    "Price", "Order", "Commission", "Swap", "Profit", "Balance", "Comment"])
        for i, d in enumerate(deals, 1):
            w.writerow([f"{d['time']:%Y.%m.%d %H:%M:%S}", i, "XAUUSD",
                        "sell" if d["side"] == BUY else "buy", "out", "",
                        f"{d['exit']:.3f}", i, "0.00", "0.00",
                        f"{d['profit']:.2f}", f"{d['balance']:.2f}", d["reason"]])
    print(f"เขียนไฟล์ deals: {path}  ({len(deals)} ไม้)")


# -------------------------------------------------------------------- CLI
def sweep(times, bids, asks, base, length, step):
    gate = build_atr_gate(times, bids, base)

    # กวาดเฉพาะนาทีที่ข้อมูลครอบคลุมจริง -- ไฟล์ที่ส่งออกเฉพาะหน้าต่าง
    # จะไม่มีข้อมูลอีก 20 ชั่วโมง การรายงานผลของหน้าต่างเปล่าคือการหลอกตัวเอง
    covered = set()
    for t in times:
        covered.add(t.hour * 60 + t.minute)
    starts = [s for s in range(0, 24 * 60, step)
              if sum(1 for k in range(length) if (s + k) % 1440 in covered) >= length * 0.9]
    if not starts:
        print("!! ข้อมูลไม่ครอบคลุมหน้าต่างใดเลย -- ส่งออก tick ให้กว้างกว่านี้")
        return
    print(f"\nกวาดหน้าต่างยาว {length} นาที ทีละ {step} นาที (เวลา UTC)")
    print(f"ข้อมูลครอบคลุม {min(covered)//60:02d}:{min(covered)%60:02d}-"
          f"{max(covered)//60:02d}:{max(covered)%60:02d} UTC -> ทดสอบได้ {len(starts)} หน้าต่าง")
    print("=" * 78)
    rows = []
    for start in starts:
        p = replace(base, win_start=start, win_end=(start + length) % 1440)
        rows.append((start, stats(run(times, bids, asks, p, gate)[0], p)))
    rows.sort(key=lambda r: r[1]["net"], reverse=True)

    print(f"{'หน้าต่าง UTC':<16}{'ไทย':<16}{'ไม้':>6}{'สุทธิ':>11}{'PF':>7}"
          f"{'ชนะ%':>8}{'ต่อไม้':>9}{'DD%':>7}")
    print("-" * 78)
    for start, s in rows:
        if not s["trades"]:
            continue
        end = (start + length) % 1440
        th_s, th_e = (start + 420) % 1440, (end + 420) % 1440
        print(f"{start//60:02d}:{start%60:02d}-{end//60:02d}:{end%60:02d}       "
              f"{th_s//60:02d}:{th_s%60:02d}-{th_e//60:02d}:{th_e%60:02d}       "
              f"{s['trades']:>6}{s['net']:>+11.2f}{s['pf']:>7.2f}"
              f"{s['wr']:>8.1f}{s['avg']:>+9.3f}{s['dd_pct']:>7.1f}")
    print("=" * 78)
    print("แถวบนสุด = หน้าต่างที่ทำกำไรมากสุด  ถ้าแถวบนๆ ห่างกันไม่มาก แปลว่าขอบไม่ได้")
    print("ผูกกับชั่วโมงใดชั่วโมงหนึ่งจริง (ข่าวดี: ทนต่อ offset ผิด)")


def main():
    a = argparse.ArgumentParser(description="ตัวจำลอง XAU StraddleReverse บนข้อมูลราคาจริง")
    a.add_argument("ticks", help="CSV จาก ExportSessionTicks.mq5 (server_time,bid,ask)")
    a.add_argument("--server-gmt", type=int, required=True,
                   help="เขตเวลาเซิร์ฟเวอร์ของข้อมูล (ดูจาก BrokerProbe)")
    a.add_argument("--win-start", default="19:00", help="เริ่มหน้าต่าง UTC (hh:mm)")
    a.add_argument("--win-end", default="20:30", help="จบหน้าต่าง UTC (hh:mm)")
    a.add_argument("--straddle-dist", type=float, default=1.00)
    a.add_argument("--stop-loss", type=float, default=12.00)
    a.add_argument("--reverse-start", type=float, default=2.50)
    a.add_argument("--reverse-gap", type=float, default=2.40)
    a.add_argument("--max-spread", type=float, default=0.60)
    a.add_argument("--cooldown-sec", type=int, default=300)
    a.add_argument("--max-sl-per-day", type=int, default=4)
    a.add_argument("--lot", type=float, default=0.01)
    a.add_argument("--balance", type=float, default=300.0)
    a.add_argument("--commission", type=float, default=0.0,
                   help="คอมมิชชัน $ ต่อ 1 ล็อต ต่อข้าง (Exness Raw = 3.5)")
    a.add_argument("--slippage", type=float, default=0.0,
                   help="สลิปเพจ $/ออนซ์ ต่อการเข้าหรือออก 1 ครั้ง")
    a.add_argument("--no-vol-filter", action="store_true")
    a.add_argument("--no-reverse", action="store_true")
    a.add_argument("--optimistic", action="store_true",
                   help="วินาทีที่ชนทั้ง SL และไม้กลับ ให้ไม้กลับชนะ (ค่าเริ่มต้นคือ SL ชนะ)")
    a.add_argument("--sweep-window", action="store_true", help="กวาดหน้าต่างเวลาทั้ง 24 ชม.")
    a.add_argument("--sweep-length", type=int, default=90, help="ความยาวหน้าต่างตอนกวาด (นาที)")
    a.add_argument("--sweep-step", type=int, default=15, help="ขยับทีละกี่นาทีตอนกวาด")
    a.add_argument("--out-deals", help="เขียนรายการไม้เป็น CSV (เอาไปทำกราฟต่อได้)")
    args = a.parse_args()

    hm = lambda s: int(s.split(":")[0]) * 60 + int(s.split(":")[1])
    p = Params(win_start=hm(args.win_start), win_end=hm(args.win_end),
               straddle_dist=args.straddle_dist, stop_loss=args.stop_loss,
               reverse_start=args.reverse_start, reverse_gap=args.reverse_gap,
               max_spread=args.max_spread, cooldown_sec=args.cooldown_sec,
               max_sl_per_day=args.max_sl_per_day, lot=args.lot,
               start_balance=args.balance, commission_per_lot_side=args.commission,
               slippage=args.slippage, use_vol_filter=not args.no_vol_filter,
               use_reverse=not args.no_reverse, pessimistic=not args.optimistic)

    times, bids, asks = load_ticks(args.ticks, args.server_gmt)

    if args.sweep_window:
        sweep(times, bids, asks, p, args.sweep_length, args.sweep_step)
        return 0

    deals, _ = run(times, bids, asks, p)
    show(stats(deals, p),
         f"หน้าต่าง {args.win_start}-{args.win_end} UTC  "
         f"(คอมฯ ${args.commission}/ล็อต/ข้าง · สลิป ${args.slippage})")
    if args.out_deals:
        write_deals(args.out_deals, deals)
    return 0


if __name__ == "__main__":
    sys.exit(main())
