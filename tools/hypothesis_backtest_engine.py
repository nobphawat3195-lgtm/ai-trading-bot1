#!/usr/bin/env python3
"""Hypothesis Backtest Engine — เอนจินทดสอบ hypothesis ใหม่บน OHLC จริง

ทำไมต้องมีตัวนี้แยกจาก ea_backtest_engine.py:
  ea_backtest_engine.py ฮาร์ดโค้ดตรรกะของ EA StraddleReverse ตัวเดียว (straddle,
  SL, stop-and-reverse, ATR gate) ใช้ทดสอบ hypothesis 30 ข้อใน
  research/hypotheses/ ไม่ได้ตรงๆ เพราะแต่ละข้อมี entry/exit ต่างกันโดยสิ้นเชิง

  ตัวนี้เป็นเอนจินทั่วไป: รับ "Strategy" (entry rule + optional custom exit rule)
  เป็น plug-in แล้วรันบนแท่ง OHLC เดียวกันได้กับทุก hypothesis — ไม่ต้องเขียนเอนจิน
  ใหม่ทุกครั้งที่มี hypothesis ใหม่ และไม่ซ้ำซ้อนกับ MT5 Strategy Tester (engine นี้
  เสริมจุดที่ Strategy Tester ทำไม่สะดวก: กวาดพารามิเตอร์/walk-forward/Monte Carlo
  แบบ batch โดยไม่ต้องรัน MT5 ทีละรอบ เหมือนที่ ea_backtest_engine.py ทำกับ
  StraddleReverse)

ข้อมูลเข้า:
  CSV จาก MQL5/Scripts/ExportOHLC.mq5  ->  server_time,open,high,low,close,
  tick_volume,spread (มี header metadata บรรทัดแรกขึ้นต้นด้วย # บอก
  server_gmt_offset ให้แปลงเป็น UTC อัตโนมัติ)

ข้อจำกัดที่ต้องรู้ก่อนใช้
-------------------------
  * ทำงานบนแท่ง OHLC ไม่ใช่ tick จริง — เข้า/ออกที่ open ของแท่งถัดไปเสมอ (กัน
    look-ahead: สัญญาณคำนวณจากแท่งที่ "ปิดแล้ว" เท่านั้น) แต่มองไม่เห็น path ราคา
    ภายในแท่งเดียวกัน เหมือนข้อจำกัดของ Model=1 "1 Minute OHLC" ใน MT5 Tester
  * วินาทีที่ทั้ง SL และ TP โดนพร้อมกันในแท่งเดียว ค่าเริ่มต้นเลือก SL ก่อนเสมอ
    (pessimistic=True) ปิดได้ด้วย cost.pessimistic=False ถ้าต้องการดูอีกด้าน
  * ใช้เทียบ hypothesis กันเอง (A/B) และหาสัญญาณเบื้องต้นได้ดี แต่ตัวเลขกำไร
    สัมบูรณ์ไม่เท่ากับ MT5 Strategy Tester (every-tick) เป๊ะ — เหตุผลเดียวกับที่
    ea_backtest_engine.py ระบุไว้ในตัวเอง

วิธีใช้ (เป็น library เป็นหลัก)
-------------------------------
    from tools.hypothesis_backtest_engine import (
        Bar, Signal, Strategy, load_ohlc_csv, run, stats,
        split_discovery_validation_oos, walk_forward_windows,
        monte_carlo_trade_order, stress_test, CostModel,
    )

    class MyHypothesis(Strategy):
        warmup_bars = 50
        def entry(self, bars, i):
            ...  # อ่านได้แค่ bars[0..i] เท่านั้น ห้ามอ่าน bars[i+1:] (look-ahead)
            return Signal(side=BUY, sl=..., tp=...) หรือ None
        def manage(self, bars, i, pos):
            return None  # หรือ (exit_price, reason) ถ้าต้องการปิดก่อน SL/TP

    bars = load_ohlc_csv("xau_ohlc_XAUUSD_PERIOD_M5.csv")
    disc, val, oos = split_discovery_validation_oos(bars)
    deals, equity = run(disc, MyHypothesis(), CostModel(spread_points=0.20))
    print(stats(deals, start_balance=10_000))

รัน self-test ด้วยข้อมูลสังเคราะห์ (ไม่ใช้ข้อมูลจริง แค่ตรวจว่าเอนจินทำงานถูกต้อง):
    python3 tools/hypothesis_backtest_engine.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, List, Optional, Tuple

BUY, SELL = 1, -1


# ------------------------------------------------------------------ ข้อมูล
@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    spread: float = 0.0


def _parse_meta(line: str) -> dict:
    """แยก key=value จากบรรทัด metadata (# symbol=... timeframe=... ...)"""
    meta = {}
    for tok in line.lstrip("#").split(","):
        tok = tok.strip()
        if "=" in tok:
            k, v = tok.split("=", 1)
            meta[k.strip()] = v.strip()
    return meta


def _parse_time(s: str) -> Optional[datetime]:
    s = s.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def load_ohlc_csv(path: str, server_gmt_offset: Optional[int] = None) -> List[Bar]:
    """โหลด CSV จาก ExportOHLC.mq5 แล้วแปลงเวลาเซิร์ฟเวอร์ -> UTC

    server_gmt_offset: ถ้าระบุ จะใช้แทนค่าที่อ่านได้จาก metadata ในไฟล์ (ไว้แก้กรณี
    BrokerProbe ให้ค่าจริงต่างจากที่ตั้งไว้ตอน export)
    """
    bars: List[Bar] = []
    meta = {}
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        rdr = csv.reader(fh)
        rows = list(rdr)
    idx = 0
    if rows and rows[0] and rows[0][0].strip().startswith("#"):
        meta = _parse_meta(",".join(rows[0]))
        idx = 1
    if idx < len(rows) and rows[idx] and rows[idx][0].strip().lower().startswith("server_time"):
        idx += 1

    gmt = server_gmt_offset
    if gmt is None:
        gmt = int(meta.get("server_gmt_offset", 0))
    shift = timedelta(hours=gmt)

    for row in rows[idx:]:
        if len(row) < 5:
            continue
        t = _parse_time(row[0])
        if t is None:
            continue
        try:
            o, h, l, c = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
        except ValueError:
            continue
        vol = int(float(row[5])) if len(row) > 5 and row[5].strip() else 0
        spr = float(row[6]) if len(row) > 6 and row[6].strip() else 0.0
        bars.append(Bar(time=t - shift, open=o, high=h, low=l, close=c,
                         volume=vol, spread=spr))

    if not bars:
        raise SystemExit(
            f"อ่านข้อมูลไม่ได้เลยจาก {path}\n"
            "  -> ต้องเป็น CSV จาก MQL5/Scripts/ExportOHLC.mq5 "
            "(server_time,open,high,low,close,tick_volume,spread)"
        )
    bars.sort(key=lambda b: b.time)
    print(f"โหลด {len(bars):,} แท่ง  {bars[0].time:%Y-%m-%d %H:%M} ถึง "
          f"{bars[-1].time:%Y-%m-%d %H:%M}  (UTC, gmt_offset ที่ใช้แปลง={gmt})")
    return bars


# --------------------------------------------------------- กลยุทธ์ (plug-in)
@dataclass
class Signal:
    side: int                 # BUY หรือ SELL
    sl: float                 # ราคา SL เด็ดขาด — ต้องระบุเสมอ (บังคับมี risk unit
                               # ชัดเจนสำหรับคำนวณ R-multiple ใน stats())
    tp: float = 0.0            # 0 = ไม่ตั้ง TP ตายตัว ปล่อยให้ manage()/time-stop จัดการ
    max_hold_bars: int = 0    # 0 = ไม่จำกัดเวลาถือ
    tag: str = ""


@dataclass
class Position:
    side: int
    entry_price: float
    entry_time: datetime
    entry_index: int
    sl: float
    tp: float
    max_hold_bars: int
    tag: str
    mae: float = 0.0          # ระยะขาดทุนสูงสุดระหว่างถือ (price units, ค่าบวก)
    mfe: float = 0.0          # ระยะกำไรสูงสุดระหว่างถือ (price units, ค่าบวก)


@dataclass
class Deal:
    open_time: datetime
    close_time: datetime
    side: int
    entry: float
    exit: float
    profit: float
    reason: str
    bars_held: int
    mae: float
    mfe: float
    risk: float                # |entry-sl| * money_per_point ตอนเปิดไม้
    tag: str = ""

    @property
    def r_multiple(self) -> float:
        return self.profit / self.risk if self.risk > 0 else 0.0


class Strategy(ABC):
    """ทุก hypothesis ใน research/hypotheses/ implement คลาสนี้ 1 ตัว

    กติกาป้องกัน look-ahead: entry()/manage() รับ `bars` เต็มลิสต์เพื่อความสะดวก
    ในการทำ indicator แบบ vectorized แต่ **ห้ามอ่านค่าที่ index > i เด็ดขาด**
    (แท่ง i คือแท่งล่าสุดที่ "ปิดแล้ว" ณ เวลาตัดสินใจ) engine จะเข้าไม้ที่ open ของ
    แท่ง i+1 เสมอ ไม่ใช่ที่ close ของแท่ง i เพื่อจำลองว่าออเดอร์ส่งได้เร็วสุดคือแท่ง
    ถัดไปเท่านั้น
    """
    warmup_bars: int = 50

    @abstractmethod
    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        ...

    def manage(self, bars: List[Bar], i: int, pos: Position) -> Optional[Tuple[float, str]]:
        """คืน (exit_price, reason) ถ้าต้องการปิดไม้ด้วยเหตุผลของ hypothesis เอง
        (เช่น CHOCH invalidate, structure เปลี่ยน) ก่อนที่ SL/TP/time-stop จะทำงาน
        คืน None ถ้าไม่มีอะไรต้องทำ (ปล่อยให้ engine เช็ค SL/TP/time-stop ต่อ)
        """
        return None


# ------------------------------------------------------------------ ต้นทุน
@dataclass
class CostModel:
    spread_points: float = 0.0        # ครึ่งสเปรดคิดเป็นต้นทุนตอนเข้า+ออก (price units)
    commission_round_trip: float = 0.0  # $ ต่อไม้ ไป-กลับ (ที่ money_per_point=1
                                         # หมายถึง $ ต่อ 1 หน่วยราคาที่ขยับ)
    slippage: float = 0.0             # price units ต่อการเข้าหรือออก 1 ครั้ง
    entry_delay_bars: int = 0         # หน่วง N แท่งก่อนเข้าจริง (จำลอง latency)
    pessimistic: bool = True          # SL/TP โดนพร้อมกันในแท่งเดียว -> SL ชนะ


# ------------------------------------------------------------------ เครื่อง
def run(bars: List[Bar], strategy: Strategy, cost: CostModel,
        money_per_point: float = 1.0) -> Tuple[List[Deal], List[Tuple[datetime, float]]]:
    """เดินหน้าทีละแท่ง คืน (รายการไม้ที่ปิดแล้ว, เส้น equity)"""
    n = len(bars)
    pos: Optional[Position] = None
    deals: List[Deal] = []
    equity: List[Tuple[datetime, float]] = []
    balance = 0.0
    half_cost = cost.spread_points + cost.slippage

    i = strategy.warmup_bars
    while i < n:
        bar = bars[i]

        if pos is not None:
            fav = (bar.high - pos.entry_price) if pos.side == BUY else (pos.entry_price - bar.low)
            adv = (pos.entry_price - bar.low) if pos.side == BUY else (bar.high - pos.entry_price)
            pos.mfe = max(pos.mfe, fav)
            pos.mae = max(pos.mae, adv)

            exit_price, reason = None, None
            custom = strategy.manage(bars, i, pos)
            if custom is not None:
                exit_price, reason = custom
            else:
                sl_hit = (bar.low <= pos.sl) if pos.side == BUY else (bar.high >= pos.sl)
                tp_hit = (pos.tp > 0) and (
                    (bar.high >= pos.tp) if pos.side == BUY else (bar.low <= pos.tp))
                if sl_hit and (cost.pessimistic or not tp_hit):
                    exit_price, reason = pos.sl, "sl"
                elif tp_hit:
                    exit_price, reason = pos.tp, "tp"
                elif pos.max_hold_bars and (i - pos.entry_index) >= pos.max_hold_bars:
                    exit_price, reason = bar.close, "time_stop"

            if exit_price is not None:
                fill = exit_price - cost.slippage * pos.side
                risk = abs(pos.entry_price - pos.sl) * money_per_point
                pnl = ((fill - pos.entry_price) * pos.side * money_per_point
                       - cost.commission_round_trip - cost.spread_points * money_per_point)
                balance += pnl
                deals.append(Deal(open_time=pos.entry_time, close_time=bar.time,
                                   side=pos.side, entry=pos.entry_price, exit=fill,
                                   profit=pnl, reason=reason,
                                   bars_held=i - pos.entry_index, mae=pos.mae, mfe=pos.mfe,
                                   risk=risk, tag=pos.tag))
                pos = None

        if pos is None:
            sig = strategy.entry(bars, i)
            if sig is not None:
                fill_index = i + 1 + cost.entry_delay_bars
                if fill_index < n:
                    entry_bar = bars[fill_index]
                    fill = entry_bar.open + (cost.slippage + cost.spread_points / 2.0) * sig.side
                    pos = Position(side=sig.side, entry_price=fill, entry_time=entry_bar.time,
                                    entry_index=fill_index, sl=sig.sl, tp=sig.tp,
                                    max_hold_bars=sig.max_hold_bars, tag=sig.tag)

        equity.append((bar.time, balance))
        i += 1

    return deals, equity


# ------------------------------------------------------------------ สถิติ
def stats(deals: List[Deal], start_balance: float = 10_000.0) -> dict:
    if not deals:
        return {"trades": 0, "net": 0.0, "pf": 0.0, "wr": 0.0, "avg": 0.0,
                "avg_r": 0.0, "dd_pct": 0.0, "expectancy": 0.0}
    pnl = [d.profit for d in deals]
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x < 0]
    gross_l = -sum(losses)
    balance = start_balance
    peak, dd = start_balance, 0.0
    for p in pnl:
        balance += p
        peak = max(peak, balance)
        dd = max(dd, (peak - balance) / peak * 100 if peak > 0 else 0.0)
    r_multiples = [d.r_multiple for d in deals]
    return {
        "trades": len(pnl),
        "net": sum(pnl),
        "pf": (sum(wins) / gross_l) if gross_l > 0 else float("inf"),
        "wr": len(wins) / len(pnl) * 100,
        "avg": sum(pnl) / len(pnl),
        "avg_win": (sum(wins) / len(wins)) if wins else 0.0,
        "avg_loss": (sum(losses) / len(losses)) if losses else 0.0,
        "avg_r": sum(r_multiples) / len(r_multiples),
        "expectancy": sum(pnl) / len(pnl),
        "dd_pct": dd,
        "avg_mae": sum(d.mae for d in deals) / len(deals),
        "avg_mfe": sum(d.mfe for d in deals) / len(deals),
        "avg_bars_held": sum(d.bars_held for d in deals) / len(deals),
        "end_balance": start_balance + sum(pnl),
    }


def show(s: dict, label: str = "") -> None:
    if label:
        print(f"\n── {label} ──")
    if not s["trades"]:
        print("  ไม่มีไม้เลย")
        return
    print(f"  ไม้ {s['trades']:>5}   สุทธิ {s['net']:>+10.2f}   PF {s['pf']:>5.2f}   "
          f"ชนะ {s['wr']:>5.1f}%   R เฉลี่ย {s['avg_r']:>+5.2f}   DD {s['dd_pct']:>5.1f}%")


# ------------------------------------------------------- แบ่งข้อมูล (ข้อ 9)
def split_discovery_validation_oos(
        bars: List[Bar], discovery: float = 0.6, validation: float = 0.2
        ) -> Tuple[List[Bar], List[Bar], List[Bar]]:
    """แบ่งตามเวลาล้วนๆ (ห้าม shuffle) — 60% Discovery / 20% Validation / 20% OOS
    ตามข้อ 9 ของ MASTER COMMAND OOS ต้องเป็นช่วงเวลาล่าสุดเสมอ ห้ามใช้สร้าง/optimize
    """
    n = len(bars)
    i1 = int(n * discovery)
    i2 = int(n * (discovery + validation))
    return bars[:i1], bars[i1:i2], bars[i2:]


# --------------------------------------------------------- Walk-Forward (ข้อ 10)
def walk_forward_windows(bars: List[Bar], train_bars: int, test_bars: int,
                          step_bars: int) -> Iterator[Tuple[List[Bar], List[Bar]]]:
    """Train -> Test -> เลื่อนหน้าต่าง -> Train -> Test -> ... (ไม่ shuffle เวลา)"""
    start = 0
    n = len(bars)
    while start + train_bars + test_bars <= n:
        yield (bars[start:start + train_bars],
               bars[start + train_bars:start + train_bars + test_bars])
        start += step_bars


# ------------------------------------------------ Robustness: Monte Carlo (ข้อ 11)
def monte_carlo_trade_order(deals: List[Deal], start_balance: float = 10_000.0,
                             n_runs: int = 2000, seed: Optional[int] = None) -> dict:
    """สลับลำดับไม้ (trade order randomization) วัดการกระจายของ max-drawdown/
    final-balance — ตรวจว่าผลลัพธ์ไม่ได้ขึ้นกับ "โชคของลำดับไม้" เท่านั้น
    """
    if not deals:
        return {"runs": 0}
    rng = random.Random(seed)
    pnl = [d.profit for d in deals]
    finals, dds = [], []
    for _ in range(n_runs):
        order = pnl[:]
        rng.shuffle(order)
        balance = start_balance
        peak = start_balance
        max_dd = 0.0
        for p in order:
            balance += p
            peak = max(peak, balance)
            max_dd = max(max_dd, (peak - balance) / peak * 100 if peak > 0 else 0.0)
        finals.append(balance)
        dds.append(max_dd)
    finals.sort()
    dds.sort()

    def pct(sorted_vals, p):
        idx = min(len(sorted_vals) - 1, max(0, int(len(sorted_vals) * p)))
        return sorted_vals[idx]

    return {
        "runs": n_runs,
        "final_balance_p5": pct(finals, 0.05),
        "final_balance_p50": pct(finals, 0.50),
        "final_balance_p95": pct(finals, 0.95),
        "max_dd_p50": pct(dds, 0.50),
        "max_dd_p95": pct(dds, 0.95),
    }


# ---------------------------------------------------- Robustness: Stress (ข้อ 11)
def stress_test(bars: List[Bar], strategy_factory, base_cost: CostModel,
                 money_per_point: float = 1.0, start_balance: float = 10_000.0) -> dict:
    """รันซ้ำภายใต้สถานการณ์ต้นทุน/latency ที่แย่ลง ดูว่า edge ยังอยู่หรือหายไป
    strategy_factory: callable() -> Strategy instance ใหม่ (กันสถานะค้างข้ามรอบ)
    """
    scenarios = {
        "base": base_cost,
        "spread_x2": CostModel(**{**base_cost.__dict__,
                                   "spread_points": base_cost.spread_points * 2}),
        "slippage_x3": CostModel(**{**base_cost.__dict__,
                                     "slippage": max(base_cost.slippage, 0.01) * 3}),
        "commission_x2": CostModel(**{**base_cost.__dict__,
                                       "commission_round_trip":
                                           max(base_cost.commission_round_trip, 0.01) * 2}),
        "entry_delay_1bar": CostModel(**{**base_cost.__dict__,
                                          "entry_delay_bars": base_cost.entry_delay_bars + 1}),
        "optimistic_tie_break": CostModel(**{**base_cost.__dict__, "pessimistic": False}),
    }
    out = {}
    for name, cost in scenarios.items():
        deals, _ = run(bars, strategy_factory(), cost, money_per_point)
        out[name] = stats(deals, start_balance)
    return out


# -------------------------------------------------------------------- Self-test
class _SelfTestStrategy(Strategy):
    """กลยุทธ์ trivial สำหรับ self-test เท่านั้น: เข้า BUY ทุกครั้งที่แท่งปิดสูงกว่า
    แท่งก่อนหน้า 3 แท่งติด (ไม่ใช่ hypothesis จริง — แค่พิสูจน์ว่าเอนจินไม่ crash และ
    ตัวเลขออกมาสมเหตุสมผล)
    """
    warmup_bars = 10

    def entry(self, bars, i):
        if i < 3:
            return None
        if bars[i].close > bars[i - 1].close > bars[i - 2].close > bars[i - 3].close:
            sl = bars[i].close - 2.0
            tp = bars[i].close + 4.0
            return Signal(side=BUY, sl=sl, tp=tp, max_hold_bars=20, tag="selftest")
        return None


def _make_synthetic_bars(n: int = 2000, seed: int = 42) -> List[Bar]:
    """สร้างแท่งราคาสังเคราะห์แบบ random-walk (ไม่ใช่ข้อมูลตลาดจริง) เพื่อทดสอบกลไก
    ของเอนจินล้วนๆ (load/split/run/stats/walk-forward/Monte Carlo/stress) โดยไม่ต้อง
    รอข้อมูล XAUUSD จริง — ห้ามใช้ผลจาก self-test นี้อ้างอิงเป็น "หลักฐาน edge" เด็ดขาด
    """
    rng = random.Random(seed)
    bars = []
    t = datetime(2025, 1, 1)
    price = 2000.0
    for _ in range(n):
        o = price
        drift = rng.gauss(0, 0.6)
        h = o + abs(rng.gauss(0.4, 0.3))
        l = o - abs(rng.gauss(0.4, 0.3))
        c = max(l, min(h, o + drift))
        h = max(h, o, c)
        l = min(l, o, c)
        bars.append(Bar(time=t, open=o, high=h, low=l, close=c,
                         volume=rng.randint(50, 500)))
        price = c
        t += timedelta(minutes=5)
    return bars


def _selftest() -> int:
    print("=== Self-test: ข้อมูลสังเคราะห์ (synthetic random-walk) ไม่ใช่ข้อมูลตลาดจริง ===")
    bars = _make_synthetic_bars()

    disc, val, oos = split_discovery_validation_oos(bars)
    print(f"แบ่งข้อมูล: Discovery={len(disc)} Validation={len(val)} OOS={len(oos)} แท่ง")
    assert len(disc) + len(val) + len(oos) == len(bars)
    assert disc[-1].time < val[0].time < oos[0].time, "การแบ่งข้อมูลข้ามเวลาไม่ถูกต้อง"

    cost = CostModel(spread_points=0.05, commission_round_trip=0.05, slippage=0.02)
    deals, equity = run(disc, _SelfTestStrategy(), cost)
    s = stats(deals, start_balance=10_000)
    show(s, "Discovery (synthetic)")
    assert s["trades"] > 0, "self-test ควรมีไม้อย่างน้อย 1 ไม้ ถ้าไม่มี เอนจินมีปัญหา"
    for d in deals:
        assert d.close_time > d.open_time
        assert d.mae >= 0 and d.mfe >= 0

    oos_deals, _ = run(oos, _SelfTestStrategy(), cost)
    show(stats(oos_deals, start_balance=10_000), "OOS (synthetic)")

    wf_runs = 0
    for train, test in walk_forward_windows(bars, train_bars=500, test_bars=200, step_bars=200):
        d, _ = run(test, _SelfTestStrategy(), cost)
        wf_runs += 1
    print(f"\nWalk-forward: รันได้ {wf_runs} หน้าต่าง (train=500,test=200,step=200 แท่ง)")
    assert wf_runs > 0

    mc = monte_carlo_trade_order(deals, start_balance=10_000, n_runs=500, seed=1)
    print(f"\nMonte Carlo (trade-order shuffle, {mc['runs']} รอบ):")
    print(f"  final_balance p5/p50/p95 = {mc['final_balance_p5']:.2f} / "
          f"{mc['final_balance_p50']:.2f} / {mc['final_balance_p95']:.2f}")
    print(f"  max_dd p50/p95 = {mc['max_dd_p50']:.1f}% / {mc['max_dd_p95']:.1f}%")

    stress = stress_test(disc, _SelfTestStrategy, cost)
    print("\nStress test (spread/slippage/commission/latency):")
    for name, st in stress.items():
        print(f"  {name:<22} trades={st['trades']:>4}  net={st['net']:>+9.2f}  "
              f"pf={st['pf']:>5.2f}")

    print("\n=== Self-test ผ่านทั้งหมด — เอนจินพร้อมรับข้อมูล XAUUSD จริงจาก "
          "ExportOHLC.mq5 ===")
    return 0


def main() -> int:
    a = argparse.ArgumentParser(description="Hypothesis Backtest Engine")
    a.add_argument("--selftest", action="store_true",
                   help="รันด้วยข้อมูลสังเคราะห์เพื่อตรวจกลไกเอนจิน (ไม่ใช่ผล backtest จริง)")
    a.add_argument("ticks", nargs="?", help="CSV จาก ExportOHLC.mq5 (ยังไม่มี CLI สำเร็จรูป "
                   "สำหรับ hypothesis ใดโดยเฉพาะ — import เป็น library แทน)")
    args = a.parse_args()

    if args.selftest or not args.ticks:
        return _selftest()

    print("โหมดนี้ยังไม่มี strategy สำเร็จรูปให้รันจาก CLI โดยตรง — import โมดูลนี้เป็น "
          "library แล้วเขียนคลาส Strategy ย่อยตาม hypothesis ที่ต้องการทดสอบ")
    load_ohlc_csv(args.ticks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
