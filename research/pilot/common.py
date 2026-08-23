"""Helper functions shared by pilot Strategy implementations.

ทุกฟังก์ชันในไฟล์นี้เป็น "ตัวช่วยระดับ pilot" ไม่ใช่ตัวสร้าง signal สมบูรณ์แบบตามสเปกใน
research/hypotheses/*.md เต็มรูปแบบ — ที่ต้องประมาณลงแบบนี้เพราะข้อมูลตอนนี้มีแค่ ~1
สัปดาห์ (ดู research/pilot/PILOT_RESULTS_2026-07-01_to_07.md หัวข้อเหตุผล) เช่น:
  - "แนวโน้ม" ในที่นี้ใช้ SMA fast/slow แทน swing-based BOS/CHOCH tracking เต็มรูปแบบ
    (สเปกจริงในหมวด B ต้องการ fractal swing state machine ซึ่งต้องข้อมูลยาวกว่านี้มาก
    ถึงจะ calibrate parameter ได้อย่างมีความหมาย)
  - Session window เป็นตัวเลข UTC ค่าประมาณทั่วไป (Asian/London/NY) ไม่ได้ปรับ DST
    ตามวันที่จริง เพราะช่วงข้อมูล pilot สั้นเกินกว่าจะกระทบ DST อยู่แล้ว
"""
from dataclasses import dataclass
from typing import List, Optional

from tools.hypothesis_backtest_engine import Bar


def sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def sma_series_at(bars: List[Bar], i: int, period: int) -> Optional[float]:
    if i + 1 < period:
        return None
    return sum(b.close for b in bars[i + 1 - period:i + 1]) / period


def trend_state(bars: List[Bar], i: int, fast: int = 10, slow: int = 30) -> int:
    """ตัวแทนแนวโน้มแบบง่าย (proxy แทน BOS/CHOCH เต็มรูปแบบ): 1=ขึ้น, -1=ลง, 0=ไม่ชัด"""
    f = sma_series_at(bars, i, fast)
    s = sma_series_at(bars, i, slow)
    if f is None or s is None:
        return 0
    if f > s * 1.0003:
        return 1
    if f < s * 0.9997:
        return -1
    return 0


def last_swing_high(bars: List[Bar], upto_i: int, n: int = 5) -> Optional[float]:
    for j in range(upto_i - n, n, -1):
        window = bars[j - n:j + n + 1]
        if window and bars[j].high == max(b.high for b in window):
            return bars[j].high
    return None


def last_swing_low(bars: List[Bar], upto_i: int, n: int = 5) -> Optional[float]:
    for j in range(upto_i - n, n, -1):
        window = bars[j - n:j + n + 1]
        if window and bars[j].low == min(b.low for b in window):
            return bars[j].low
    return None


def body_ratio(bar: Bar) -> float:
    rng = bar.high - bar.low
    if rng <= 0:
        return 0.0
    return abs(bar.close - bar.open) / rng


def atr_simple(bars: List[Bar], i: int, period: int = 14) -> Optional[float]:
    if i + 1 < period + 1:
        return None
    trs = []
    for k in range(i - period + 1, i + 1):
        prev_close = bars[k - 1].close
        tr = max(bars[k].high - bars[k].low,
                  abs(bars[k].high - prev_close),
                  abs(bars[k].low - prev_close))
        trs.append(tr)
    return sum(trs) / len(trs)


def rolling_vwap(bars: List[Bar], i: int, window: int = 240) -> Optional[float]:
    """VWAP แบบ rolling window (ไม่ได้ reset รายวันแบบ session-VWAP เต็มรูปแบบ เพื่อความ
    ง่ายในระดับ pilot — window เริ่มต้น 240 แท่ง M1 = ราว 4 ชม.)"""
    start = max(0, i - window + 1)
    seg = bars[start:i + 1]
    vol = sum(max(b.volume, 1) for b in seg)
    if vol <= 0:
        return None
    return sum(b.close * max(b.volume, 1) for b in seg) / vol


def rolling_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    var = sum((v - m) ** 2 for v in values) / len(values)
    return var ** 0.5


# ---------------------------------------------------------------- session (UTC, ประมาณ)
def hour_utc(bar: Bar) -> int:
    return bar.time.hour


def is_asian(h: int) -> bool:
    return 0 <= h < 7


def is_london(h: int) -> bool:
    return 7 <= h < 16


def is_ny(h: int) -> bool:
    return 12 <= h < 21


def is_overlap(h: int) -> bool:
    return 12 <= h < 16


@dataclass
class SessionRange:
    high: float
    low: float


def today_session_high_low(bars: List[Bar], i: int, start_h: int, end_h: int
                            ) -> Optional[SessionRange]:
    """High/low ของ session (ตาม UTC hour [start_h,end_h)) ของ "วันเดียวกับแท่ง i"
    เฉพาะแท่งที่เกิดขึ้นก่อนแท่ง i เท่านั้น (กัน look-ahead) คืน None ถ้ายังไม่มีแท่งใน
    session นั้นเลย (เช่น session ยังไม่เริ่ม หรือข้อมูลไม่ครอบคลุมวันนั้น)
    """
    day = bars[i].time.date()
    hi = lo = None
    j = i - 1
    while j >= 0 and bars[j].time.date() == day:
        h = bars[j].time.hour
        if start_h <= h < end_h:
            hi = bars[j].high if hi is None else max(hi, bars[j].high)
            lo = bars[j].low if lo is None else min(lo, bars[j].low)
        j -= 1
    if hi is None:
        return None
    return SessionRange(high=hi, low=lo)
