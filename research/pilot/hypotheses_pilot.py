"""Strategy implementations (เวอร์ชัน pilot) สำหรับ hypothesis ที่ทดสอบได้ด้วยข้อมูล
1 สัปดาห์ที่มีอยู่ตอนนี้ — ทุกคลาสเป็นเวอร์ชันตัดทอนจากสเปกเต็มใน
research/hypotheses/*.md ดู research/pilot/common.py หัวไฟล์สำหรับคำอธิบายการ
ประมาณที่ใช้ร่วมกัน (SMA trend proxy แทน BOS/CHOCH, session window UTC ค่าประมาณ ฯลฯ)

ไม่รวม: C3, D1, D2, D3, H1, H2, H3 — ต้องการข้อมูลยาวกว่า 1 สัปดาห์มาก (ดูเหตุผลใน
PILOT_RESULTS_2026-07-01_to_07.md) จึง "ไม่ทดสอบ" แทนที่จะปั้นตัวเลขที่ไม่มีความหมาย
"""
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.hypothesis_backtest_engine import BUY, SELL, Bar, Signal, Strategy  # noqa: E402
from research.pilot.common import (  # noqa: E402
    atr_simple, body_ratio, hour_utc, is_asian, is_london, is_ny, is_overlap,
    last_swing_high, last_swing_low, rolling_std, rolling_vwap, sma_series_at,
    today_session_high_low, trend_state,
)
from research.pilot.run_pilot_2026w27 import (  # noqa: E402
    PilotLiquiditySweepReversal as A1,
    PilotMomentumBurst as G1,
    PilotStreakOverextension as F3,
)


# --------------------------------------------------------------------- A2
class A2_StopRunContinuation(Strategy):
    warmup_bars = 20

    def __init__(self, fractal_n: int = 5, body_min: float = 0.55, r_multiple: float = 1.5):
        self.n = fractal_n
        self.body_min = body_min
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < self.warmup_bars:
            return None
        bar = bars[i]
        if body_ratio(bar) < self.body_min:
            return None
        sh = last_swing_high(bars, i - 1, self.n)
        if sh and bar.close > sh and bar.low > sh - (bar.high - bar.low) * 0.3:
            risk = bar.close - sh
            if risk > 0:
                return Signal(side=BUY, sl=sh - risk * 0.2, tp=bar.close + risk * self.r,
                               max_hold_bars=40, tag="A2_up")
        sl_ = last_swing_low(bars, i - 1, self.n)
        if sl_ and bar.close < sl_ and bar.high < sl_ + (bar.high - bar.low) * 0.3:
            risk = sl_ - bar.close
            if risk > 0:
                return Signal(side=SELL, sl=sl_ + risk * 0.2, tp=bar.close - risk * self.r,
                               max_hold_bars=40, tag="A2_down")
        return None


# --------------------------------------------------------------------- A3
class A3_EqualLevelReclaim(Strategy):
    """ประมาณ equal-high/low ด้วย fractal 2 จุดล่าสุดที่ห่างกันไม่เกิน tolerance"""
    warmup_bars = 30

    def __init__(self, fractal_n: int = 5, tolerance: float = 0.8, r_multiple: float = 1.5):
        self.n = fractal_n
        self.tol = tolerance
        self.r = r_multiple

    def _equal_high(self, bars: List[Bar], i: int) -> Optional[float]:
        h1 = last_swing_high(bars, i, self.n)
        if h1 is None:
            return None
        h2 = last_swing_high(bars, i - self.n - 1, self.n)
        if h2 is not None and abs(h1 - h2) <= self.tol:
            return max(h1, h2)
        return None

    def _equal_low(self, bars: List[Bar], i: int) -> Optional[float]:
        l1 = last_swing_low(bars, i, self.n)
        if l1 is None:
            return None
        l2 = last_swing_low(bars, i - self.n - 1, self.n)
        if l2 is not None and abs(l1 - l2) <= self.tol:
            return min(l1, l2)
        return None

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < self.warmup_bars:
            return None
        bar = bars[i]
        rng = bar.high - bar.low
        if rng <= 0:
            return None
        eqh = self._equal_high(bars, i - 1)
        if eqh and bar.high > eqh and bar.close < eqh:
            risk = bar.high - bar.close
            if risk > 0:
                return Signal(side=SELL, sl=bar.high + risk * 0.2,
                               tp=bar.close - risk * self.r, max_hold_bars=60, tag="A3_high")
        eql = self._equal_low(bars, i - 1)
        if eql and bar.low < eql and bar.close > eql:
            risk = bar.close - bar.low
            if risk > 0:
                return Signal(side=BUY, sl=bar.low - risk * 0.2,
                               tp=bar.close + risk * self.r, max_hold_bars=60, tag="A3_low")
        return None


# --------------------------------------------------------------------- A4
class A4_SessionSweepFail(Strategy):
    """sweep ของ Asian range (00-07 UTC) ตอนชั่วโมงแรกของ London (07-08 UTC) แล้ว fail
    to close outside -> เข้าสวนกลับเข้า range เดิม"""
    warmup_bars = 500

    def __init__(self, r_multiple: float = 1.2):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if hour_utc(bar) != 7:
            return None
        rng = today_session_high_low(bars, i, 0, 7)
        if rng is None:
            return None
        if bar.high > rng.high and bar.close < rng.high:
            risk = bar.high - bar.close
            if risk > 0:
                return Signal(side=SELL, sl=bar.high + risk * 0.2,
                               tp=bar.close - risk * self.r, max_hold_bars=90, tag="A4_high")
        if bar.low < rng.low and bar.close > rng.low:
            risk = bar.close - bar.low
            if risk > 0:
                return Signal(side=BUY, sl=bar.low - risk * 0.2,
                               tp=bar.close + risk * self.r, max_hold_bars=90, tag="A4_low")
        return None


# --------------------------------------------------------------------- B1
class B1_BOSContinuation(Strategy):
    """proxy: เทรนด์ (SMA10/30) + pullback แตะ SMA10 แล้วปิดกลับทิศทางเทรนด์"""
    warmup_bars = 40

    def __init__(self, r_multiple: float = 1.5):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        tr = trend_state(bars, i - 1)
        if tr == 0:
            return None
        f = sma_series_at(bars, i, 10)
        if f is None:
            return None
        bar = bars[i]
        if tr == 1 and bar.low <= f <= bar.high and bar.close > f:
            sw = last_swing_low(bars, i - 1, 5) or bar.low
            risk = bar.close - sw
            if risk > 0:
                return Signal(side=BUY, sl=sw, tp=bar.close + risk * self.r,
                               max_hold_bars=60, tag="B1_up")
        if tr == -1 and bar.low <= f <= bar.high and bar.close < f:
            sw = last_swing_high(bars, i - 1, 5) or bar.high
            risk = sw - bar.close
            if risk > 0:
                return Signal(side=SELL, sl=sw, tp=bar.close - risk * self.r,
                               max_hold_bars=60, tag="B1_down")
        return None


# --------------------------------------------------------------------- B2
class B2_CHOCHReversal(Strategy):
    """proxy: SMA10/30 กลับทิศทางหลังยืนเทรนด์เดิมนาน >= min_trend_bars"""
    warmup_bars = 80

    def __init__(self, min_trend_bars: int = 40, r_multiple: float = 1.8):
        self.min_trend_bars = min_trend_bars
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        cur = trend_state(bars, i)
        prev = trend_state(bars, i - 1)
        if cur == 0 or cur == prev:
            return None
        # เช็คว่า trend ก่อนหน้า (ตรงข้ามกับ cur) ยืนมานานพอ
        streak = 0
        for j in range(i - 1, max(self.warmup_bars, i - 200), -1):
            if trend_state(bars, j) == -cur:
                streak += 1
            else:
                break
        if streak < self.min_trend_bars:
            return None
        bar = bars[i]
        sw = (last_swing_high(bars, i - 1, 8) if cur == -1 else last_swing_low(bars, i - 1, 8))
        if sw is None:
            return None
        risk = abs(bar.close - sw)
        if risk <= 0:
            return None
        side = BUY if cur == 1 else SELL
        sl = sw
        tp = bar.close + risk * self.r * side
        return Signal(side=side, sl=sl, tp=tp, max_hold_bars=120, tag="B2_choch")


# --------------------------------------------------------------------- B3
class B3_DisplacementCompression(Strategy):
    """displacement leg (burst) -> compression (range หด) -> breakout ทิศทางเดิม"""
    warmup_bars = 60

    def __init__(self, burst_n: int = 5, burst_ret: float = 3.0, compress_bars: int = 15,
                 compress_ratio: float = 0.5, r_multiple: float = 1.5):
        self.burst_n = burst_n
        self.burst_ret = burst_ret
        self.compress_bars = compress_bars
        self.compress_ratio = compress_ratio
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        cb = self.compress_bars
        bn = self.burst_n
        start = i - cb
        if start - bn < 0:
            return None
        displacement = bars[start].close - bars[start - bn].close
        if abs(displacement) < self.burst_ret:
            return None
        comp_window = bars[start:i + 1]
        comp_range = max(b.high for b in comp_window) - min(b.low for b in comp_window)
        disp_range = abs(displacement)
        if comp_range > disp_range * self.compress_ratio:
            return None
        bar = bars[i]
        comp_hi = max(b.high for b in comp_window[:-1])
        comp_lo = min(b.low for b in comp_window[:-1])
        if displacement > 0 and bar.close > comp_hi:
            risk = bar.close - comp_lo
            if risk > 0:
                return Signal(side=BUY, sl=comp_lo, tp=bar.close + risk * self.r,
                               max_hold_bars=60, tag="B3_up")
        if displacement < 0 and bar.close < comp_lo:
            risk = comp_hi - bar.close
            if risk > 0:
                return Signal(side=SELL, sl=comp_hi, tp=bar.close - risk * self.r,
                               max_hold_bars=60, tag="B3_down")
        return None


# --------------------------------------------------------------------- B4
class B4_TrendTransitionMTF(Strategy):
    """proxy หยาบมาก: fast pair (10/30) แทน M5 CHOCH, slow pair (60/180) แทน H1 trend
    context — เข้าเมื่อ fast กลับทิศทางขณะ slow เริ่มอ่อนตัว (ยังไม่กลับทิศทางเต็มที่)"""
    warmup_bars = 200

    def __init__(self, r_multiple: float = 1.8):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        fast_cur = trend_state(bars, i, 10, 30)
        fast_prev = trend_state(bars, i - 1, 10, 30)
        if fast_cur == 0 or fast_cur == fast_prev:
            return None
        slow_f = sma_series_at(bars, i, 60)
        slow_s = sma_series_at(bars, i, 180)
        slow_f_prev = sma_series_at(bars, i - 20, 60)
        if None in (slow_f, slow_s, slow_f_prev):
            return None
        # "อ่อนตัว": slow_f ขยับเข้าใกล้ slow_s มากขึ้นในช่วง 20 แท่งหลังนี้
        weakening = abs(slow_f - slow_s) < abs(slow_f_prev - slow_s)
        if not weakening:
            return None
        bar = bars[i]
        sw = (last_swing_high(bars, i - 1, 8) if fast_cur == -1 else last_swing_low(bars, i - 1, 8))
        if sw is None:
            return None
        risk = abs(bar.close - sw)
        if risk <= 0:
            return None
        side = BUY if fast_cur == 1 else SELL
        return Signal(side=side, sl=sw, tp=bar.close + risk * self.r * side,
                       max_hold_bars=150, tag="B4_mtf")


# --------------------------------------------------------------------- C1
class C1_FVGFillReversal(Strategy):
    warmup_bars = 10

    def __init__(self, r_multiple: float = 1.3):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < 3:
            return None
        # FVG เกิดที่ i-1 (แท่งกลาง) จากช่องว่างระหว่าง i-2 กับ i
        b0, b2 = bars[i - 2], bars[i]
        bar = bars[i]
        if b2.low > b0.high:  # bullish FVG กว้าง [b0.high, b2.low]
            mid = (b0.high + b2.low) / 2
            if bar.low <= mid and bar.close > b0.high:
                risk = bar.close - b0.high
                if risk > 0:
                    return Signal(side=BUY, sl=b0.high - risk * 0.3,
                                   tp=bar.close + risk * self.r, max_hold_bars=40, tag="C1_bull")
        if b2.high < b0.low:  # bearish FVG
            mid = (b0.low + b2.high) / 2
            if bar.high >= mid and bar.close < b0.low:
                risk = b0.low - bar.close
                if risk > 0:
                    return Signal(side=SELL, sl=b0.low + risk * 0.3,
                                   tp=bar.close - risk * self.r, max_hold_bars=40, tag="C1_bear")
        return None


# --------------------------------------------------------------------- C2
class C2_FVGContinuation(Strategy):
    """เหมือน C1 แต่กรองด้วยทิศทางเทรนด์ (ต้องสอดคล้องกับทิศทาง FVG)"""
    warmup_bars = 40

    def __init__(self, r_multiple: float = 1.5):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        if i < 3:
            return None
        tr = trend_state(bars, i - 1)
        if tr == 0:
            return None
        b0, b2, bar = bars[i - 2], bars[i], bars[i]
        if tr == 1 and b2.low > b0.high:
            mid = (b0.high + b2.low) / 2
            if bar.low <= mid and bar.close > b0.high:
                risk = bar.close - b0.high
                if risk > 0:
                    return Signal(side=BUY, sl=b0.high - risk * 0.3,
                                   tp=bar.close + risk * self.r, max_hold_bars=60, tag="C2_up")
        if tr == -1 and b2.high < b0.low:
            mid = (b0.low + b2.high) / 2
            if bar.high >= mid and bar.close < b0.low:
                risk = b0.low - bar.close
                if risk > 0:
                    return Signal(side=SELL, sl=b0.low + risk * 0.3,
                                   tp=bar.close - risk * self.r, max_hold_bars=60, tag="C2_down")
        return None


# --------------------------------------------------------------------- E1
class E1_LondonOpenMomentum(Strategy):
    warmup_bars = 50

    def __init__(self, n_bars: int = 15, threshold: float = 2.5, r_multiple: float = 1.3):
        self.n_bars = n_bars
        self.threshold = threshold
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if hour_utc(bar) != 7 or bar.time.minute != self.n_bars:
            return None
        start_idx = i - self.n_bars
        if start_idx < 0 or bars[start_idx].time.date() != bar.time.date():
            return None
        ret = bar.close - bars[start_idx].close
        if abs(ret) < self.threshold:
            return None
        side = BUY if ret > 0 else SELL
        risk = abs(ret)
        return Signal(side=side, sl=bars[start_idx].close,
                       tp=bar.close + risk * self.r * side, max_hold_bars=45, tag="E1")


# --------------------------------------------------------------------- E2
class E2_NYOpenRangeFade(Strategy):
    warmup_bars = 500

    def __init__(self, edge_pct: float = 0.1, r_multiple: float = 1.0):
        self.edge_pct = edge_pct
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if hour_utc(bar) != 12 or bar.time.minute != 0:
            return None
        rng = today_session_high_low(bars, i, 0, 12)
        if rng is None or rng.high <= rng.low:
            return None
        width = rng.high - rng.low
        pos = (bar.close - rng.low) / width
        mid = (rng.high + rng.low) / 2
        if pos >= 1 - self.edge_pct:
            risk = rng.high - mid
            return Signal(side=SELL, sl=rng.high + width * 0.1, tp=mid,
                           max_hold_bars=90, tag="E2_high")
        if pos <= self.edge_pct:
            risk = mid - rng.low
            return Signal(side=BUY, sl=rng.low - width * 0.1, tp=mid,
                           max_hold_bars=90, tag="E2_low")
        return None


# --------------------------------------------------------------------- E3
class E3_OverlapContinuation(Strategy):
    warmup_bars = 60

    def __init__(self, r_multiple: float = 1.5):
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if hour_utc(bar) != 12 or bar.time.minute != 0:
            return None
        tr = trend_state(bars, i - 1)
        if tr == 0:
            return None
        sw = last_swing_low(bars, i - 1, 5) if tr == 1 else last_swing_high(bars, i - 1, 5)
        if sw is None:
            return None
        risk = abs(bar.close - sw)
        if risk <= 0:
            return None
        side = BUY if tr == 1 else SELL
        return Signal(side=side, sl=sw, tp=bar.close + risk * self.r * side,
                       max_hold_bars=240, tag="E3")


# --------------------------------------------------------------------- E4
class E4_AsianRangeBreakoutLondon(Strategy):
    warmup_bars = 500

    def __init__(self, r_multiple: float = 1.5):
        self.r = r_multiple
        self._fired_today = None

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        h = hour_utc(bar)
        if not (7 <= h < 16):
            return None
        day = bar.time.date()
        if self._fired_today == day:
            return None
        rng = today_session_high_low(bars, i, 0, 7)
        if rng is None:
            return None
        if bar.close > rng.high:
            self._fired_today = day
            risk = bar.close - rng.low
            return Signal(side=BUY, sl=rng.low, tp=bar.close + (rng.high - rng.low) * self.r,
                           max_hold_bars=240, tag="E4_up")
        if bar.close < rng.low:
            self._fired_today = day
            risk = rng.high - bar.close
            return Signal(side=SELL, sl=rng.high, tp=bar.close - (rng.high - rng.low) * self.r,
                           max_hold_bars=240, tag="E4_down")
        return None


# --------------------------------------------------------------------- F1
class F1_VWAPExtremeDeviation(Strategy):
    warmup_bars = 60

    def __init__(self, window: int = 240, k_std: float = 2.0, r_multiple: float = 1.0):
        self.window = window
        self.k_std = k_std
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        vwap = rolling_vwap(bars, i, self.window)
        if vwap is None:
            return None
        diffs = []
        for j in range(max(0, i - 60), i):
            v = rolling_vwap(bars, j, self.window)
            if v is not None:
                diffs.append(bars[j].close - v)
        std = rolling_std(diffs)
        if std <= 0:
            return None
        bar = bars[i]
        dev = bar.close - vwap
        if dev >= self.k_std * std and bar.close < bar.open:
            risk = dev
            return Signal(side=SELL, sl=bar.high, tp=vwap, max_hold_bars=90, tag="F1_high")
        if dev <= -self.k_std * std and bar.close > bar.open:
            risk = -dev
            return Signal(side=BUY, sl=bar.low, tp=vwap, max_hold_bars=90, tag="F1_low")
        return None


# --------------------------------------------------------------------- F2
class F2_AsianRangeReversion(Strategy):
    warmup_bars = 500

    def __init__(self, min_range_bars: int = 120, r_multiple: float = 0.6):
        self.min_range_bars = min_range_bars
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if not is_asian(hour_utc(bar)):
            return None
        day = bar.time.date()
        j = i - 1
        count = 0
        hi = lo = None
        while j >= 0 and bars[j].time.date() == day and is_asian(hour_utc(bars[j])):
            hi = bars[j].high if hi is None else max(hi, bars[j].high)
            lo = bars[j].low if lo is None else min(lo, bars[j].low)
            count += 1
            j -= 1
        if count < self.min_range_bars or hi is None:
            return None
        width = hi - lo
        if width <= 0:
            return None
        if bar.high >= hi and bar.close < hi:
            return Signal(side=SELL, sl=hi + width * 0.15, tp=(hi + lo) / 2,
                           max_hold_bars=60, tag="F2_high")
        if bar.low <= lo and bar.close > lo:
            return Signal(side=BUY, sl=lo - width * 0.15, tp=(hi + lo) / 2,
                           max_hold_bars=60, tag="F2_low")
        return None


# --------------------------------------------------------------------- F4
class F4_VWAPBandFade(Strategy):
    warmup_bars = 40

    def __init__(self, window: int = 20, k_std: float = 2.0, no_trend_band: float = 0.0005):
        self.window = window
        self.k_std = k_std
        self.no_trend_band = no_trend_band

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        vwap = rolling_vwap(bars, i, self.window)
        if vwap is None:
            return None
        closes = [b.close for b in bars[max(0, i - self.window + 1):i + 1]]
        std = rolling_std(closes)
        if std <= 0:
            return None
        f = sma_series_at(bars, i, 10)
        s = sma_series_at(bars, i, 30)
        if f is None or s is None or abs(f - s) / s > self.no_trend_band:
            return None  # มีเทรนด์ชัด ไม่ fade
        bar = bars[i]
        upper = vwap + self.k_std * std
        lower = vwap - self.k_std * std
        if bar.high >= upper and bar.close < upper:
            return Signal(side=SELL, sl=upper + std * 0.3, tp=vwap, max_hold_bars=40, tag="F4_up")
        if bar.low <= lower and bar.close > lower:
            return Signal(side=BUY, sl=lower - std * 0.3, tp=vwap, max_hold_bars=40, tag="F4_dn")
        return None


# --------------------------------------------------------------------- G2
class G2_BreakoutRetest(Strategy):
    warmup_bars = 30

    def __init__(self, fractal_n: int = 5, retest_tol: float = 0.4,
                 retest_window: int = 20, r_multiple: float = 1.5):
        self.n = fractal_n
        self.tol = retest_tol
        self.retest_window = retest_window
        self.r = r_multiple
        self._pending = None  # (level, side, break_index)

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        bar = bars[i]
        if self._pending:
            level, side, bidx = self._pending
            if i - bidx > self.retest_window:
                self._pending = None
            else:
                near = abs(bar.close - level) <= self.tol
                if side == BUY and near and bar.close > level:
                    self._pending = None
                    risk = bar.close - level
                    if risk > 0:
                        return Signal(side=BUY, sl=level - risk, tp=bar.close + risk * self.r,
                                       max_hold_bars=60, tag="G2_up")
                elif side == SELL and near and bar.close < level:
                    self._pending = None
                    risk = level - bar.close
                    if risk > 0:
                        return Signal(side=SELL, sl=level + risk, tp=bar.close - risk * self.r,
                                       max_hold_bars=60, tag="G2_dn")
                return None
        sh = last_swing_high(bars, i - 1, self.n)
        if sh and bar.close > sh:
            self._pending = (sh, BUY, i)
            return None
        sl_ = last_swing_low(bars, i - 1, self.n)
        if sl_ and bar.close < sl_:
            self._pending = (sl_, SELL, i)
        return None


# --------------------------------------------------------------------- G3
class G3_ShallowPullback(Strategy):
    warmup_bars = 40

    def __init__(self, retrace_max: float = 0.38, r_multiple: float = 1.3):
        self.retrace_max = retrace_max
        self.r = r_multiple

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        tr = trend_state(bars, i - 1)
        if tr == 0:
            return None
        bar = bars[i]
        if tr == 1:
            sw_lo = last_swing_low(bars, i - 1, 5)
            sw_hi = last_swing_high(bars, i - 2, 5)
            if sw_lo is None or sw_hi is None or sw_hi <= sw_lo:
                return None
            leg = sw_hi - sw_lo
            retrace = (sw_hi - bar.low) / leg
            if 0 < retrace <= self.retrace_max and bar.close > bar.open:
                risk = bar.close - sw_lo
                if risk > 0:
                    return Signal(side=BUY, sl=sw_lo, tp=bar.close + risk * self.r,
                                   max_hold_bars=45, tag="G3_up")
        else:
            sw_hi = last_swing_high(bars, i - 1, 5)
            sw_lo = last_swing_low(bars, i - 2, 5)
            if sw_hi is None or sw_lo is None or sw_hi <= sw_lo:
                return None
            leg = sw_hi - sw_lo
            retrace = (bar.high - sw_lo) / leg
            if 0 < retrace <= self.retrace_max and bar.close < bar.open:
                risk = sw_hi - bar.close
                if risk > 0:
                    return Signal(side=SELL, sl=sw_hi, tp=bar.close - risk * self.r,
                                   max_hold_bars=45, tag="G3_dn")
        return None


# --------------------------------------------------------------------- G4
class G4_VolumeBurstConfirm(G1):
    """G1 + กรองด้วย tick_volume >= 2x rolling average(20)"""

    def entry(self, bars: List[Bar], i: int) -> Optional[Signal]:
        sig = super().entry(bars, i)
        if sig is None:
            return None
        if i < 20:
            return None
        avg_vol = sum(b.volume for b in bars[i - 20:i]) / 20
        if avg_vol <= 0 or bars[i].volume < 2 * avg_vol:
            return None
        sig.tag = "G4_" + sig.tag
        return sig


ALL_PILOT_STRATEGIES = {
    "A1": A1, "A2": A2_StopRunContinuation, "A3": A3_EqualLevelReclaim,
    "A4": A4_SessionSweepFail,
    "B1": B1_BOSContinuation, "B2": B2_CHOCHReversal,
    "B3": B3_DisplacementCompression, "B4": B4_TrendTransitionMTF,
    "C1": C1_FVGFillReversal, "C2": C2_FVGContinuation,
    "E1": E1_LondonOpenMomentum, "E2": E2_NYOpenRangeFade,
    "E3": E3_OverlapContinuation, "E4": E4_AsianRangeBreakoutLondon,
    "F1": F1_VWAPExtremeDeviation, "F2": F2_AsianRangeReversion, "F3": F3,
    "F4": F4_VWAPBandFade,
    "G1": G1, "G2": G2_BreakoutRetest, "G3": G3_ShallowPullback,
    "G4": G4_VolumeBurstConfirm,
}

NOT_TESTABLE = {
    "C3": "Session-Open Gap Fill ต้องการ daily gap หลายสิบวันขึ้นไป มีแค่ 7 วัน (~6 gap) "
          "ไม่พอสร้างข้อสรุป",
    "D1": "Daily ATR percentile ต้องการ 60+ วันย้อนหลังคำนวณ percentile — มีแค่ ~7 daily bar",
    "D2": "Asian-range percentile เทียบ 20 วัน — มีแค่ ~7 วัน ไม่พอคำนวณ percentile",
    "D3": "Opening-range percentile เทียบ 20 วัน — มีแค่ ~7 วัน ไม่พอคำนวณ percentile",
    "H1": "Hour-of-day seasonality ต้องการ 2-3 ปีย้อนหลังกัน false positive จาก "
          "multiple-testing — มีแค่ 1 สัปดาห์ ไม่มีความหมายทางสถิติเลย",
    "H2": "Day-of-week effect ต้องการ 2-3 ปี — มีแค่ 1 ตัวอย่างต่อวันในสัปดาห์นี้",
    "H3": "Daily streak reversal ต้องการ empirical distribution จาก 3-5 ปี — มีแค่ ~7 daily bar",
}
