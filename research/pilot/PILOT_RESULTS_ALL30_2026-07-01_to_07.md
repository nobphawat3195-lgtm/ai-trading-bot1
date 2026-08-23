# Pilot Run — ทั้ง 30 Hypotheses — 2026-06-30 22:00 to 2026-07-07 18:51 UTC

**สถานะ: PILOT — ไม่ใช่ Statistical Discovery ตามข้อ 5 ของ MASTER COMMAND**

ทุกตัวเลขด้านล่างมาจากการรันจริงบนข้อมูลราคาจริง (XAUUSD VT Markets VIP, M1, ~6,526 แท่ง,
~1 สัปดาห์) แต่ **ห้ามใช้ตัดสิน ACCEPT/REJECT ของ hypothesis ใดทั้งสิ้น** — เหตุผลเดียวกับ
`PILOT_RESULTS_2026-07-01_to_07.md`:

1. Sample size เล็กเกินไปมาก (1 สัปดาห์ vs. ที่สเปกต้องการระดับเดือน-ปี)
2. Strategy ทุกตัวเป็นเวอร์ชันตัดทอน — โดยเฉพาะหมวด B (Market Structure) ที่ใช้ SMA
   fast/slow เป็น **proxy แทน BOS/CHOCH แบบ swing-tracking เต็มรูปแบบ** (ดูเหตุผลหัวไฟล์
   `research/pilot/common.py`) ต่างจากสเปกในเอกสาร hypothesis ค่อนข้างมาก
3. Threshold หลายตัว (percentile ของ burst/streak) ใช้ค่าคงที่แทนการ calibrate จาก
   empirical distribution จริง เพราะ 1 สัปดาห์ไม่พอสร้าง distribution ที่เชื่อถือได้
4. GMT offset สมมติ +3 (VT Markets ฤดูร้อนตามเอกสาร) ยังไม่ยืนยันด้วย BrokerProbe.mq5 จริง

## ผลลัพธ์ (สุทธิที่ทุน $10,000 เริ่มต้น, ต้นทุนสเปรดเฉลี่ยจากไฟล์จริง + คอมมิชชัน/สลิปเพจ
ประมาณ — ไม่ผูก lot sizing จริง)

| ID | Hypothesis | ไม้ | สุทธิ | PF | ชนะ% | R เฉลี่ย | Max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| A1 | Liquidity Sweep Reversal | 130 | -63.18 | 0.61 | 46.9% | -0.31 | 0.7% |
| A2 | Stop Run Continuation | 276 | -203.92 | 0.68 | 39.1% | -0.39 | 2.6% |
| A3 | Equal High/Low Reclaim | 332 | -180.82 | 0.61 | 42.5% | -0.39 | 1.9% |
| A4 | Prev Session H/L Sweep-Fail | 6 | -1.56 | 0.84 | 50.0% | -0.19 | 0.1% |
| B1 | BOS Continuation (proxy) | 120 | -4.09 | 0.99 | 49.2% | -0.02 | 1.2% |
| B2 | CHOCH Reversal (proxy) | 0 | — | — | — | — | — |
| B3 | Displacement-Compression (proxy) | 0 | — | — | — | — | — |
| B4 | Trend Transition MTF (proxy) | 41 | -55.86 | 0.72 | 36.6% | -0.17 | 1.1% |
| C1 | FVG Fill Reversal | 0 | — | — | — | — | — |
| C2 | FVG Retracement Continuation | 0 | — | — | — | — | — |
| C3 | Session-Open Gap Fill | **ไม่ทดสอบ** | — | — | — | — | — |
| D1 | Daily Vol Expansion Breakout | **ไม่ทดสอบ** | — | — | — | — | — |
| D2 | Asian Compression→London BO | **ไม่ทดสอบ** | — | — | — | — | — |
| D3 | Range Expansion Day Cont. | **ไม่ทดสอบ** | — | — | — | — | — |
| E1 | London Open Momentum | 1 | -9.18 | 0.00 | 0.0% | -1.05 | 0.1% |
| E2 | NY Open Range-Extreme Fade | 1 | -10.61 | 0.00 | 0.0% | -1.04 | 0.1% |
| E3 | London/NY Overlap Cont. | 4 | +16.26 | 3.98 | 50.0% | +0.07 | 0.1% |
| E4 | Asian Range BO at London | 4 | -86.07 | 0.00 | 25.0% | -0.42 | 0.9% |
| F1 | VWAP Extreme Deviation | 341 | -261.68 | 0.62 | 12.3% | -0.46 | 2.7% |
| F2 | Asian Range Reversion | 7 | -25.63 | 0.22 | 28.6% | -0.47 | 0.3% |
| F3 | Consecutive-Candle Overext. | 181 | -97.75 | 0.52 | 27.1% | -0.55 | 1.1% |
| F4 | VWAP Band Fade | 528 | -397.72 | 0.36 | 23.7% | -0.68 | 4.0% |
| G1 | Momentum Burst Continuation | 276 | -379.13 | 0.55 | 37.3% | -0.27 | 3.9% |
| G2 | Breakout-and-Retest | 174 | -129.58 | 0.00 | 0.0% | -1.37 | 1.3% |
| G3 | Shallow-Pullback Continuation | 132 | -116.16 | 0.77 | 44.7% | -0.11 | 1.8% |
| G4 | Tick-Volume Burst Confirm | 2 | -9.28 | 0.00 | 0.0% | -0.78 | 0.1% |
| H1 | Hour-of-Day Seasonality | **ไม่ทดสอบ** | — | — | — | — | — |
| H2 | Day-of-Week Effect | **ไม่ทดสอบ** | — | — | — | — | — |
| H3 | Daily Streak Reversal | **ไม่ทดสอบ** | — | — | — | — | — |
| H4 | Prev Session Return Autocorr. | correlation = -0.235 (n=5 คู่ — ไม่มีนัยสำคัญ) | | | | | |

## อ่านผลยังไงให้ไม่หลอกตัวเอง

- **แทบทุกตัวขาดทุน** — คาดไว้แล้ว เพราะ (ก) threshold ยังไม่ calibrate (ข) ต้นทุนธุรกรรม
  (สเปรด+คอมมิชชัน+สลิปเพจ) กินขอบเล็กๆ ที่ยังไม่ผ่านการปรับแต่งจริง (ค) 1 สัปดาห์อาจตรงกับ
  สภาพตลาดที่ไม่เหมาะกับกลไกเหล่านี้พอดี — **ไม่ใช่หลักฐานเพียงพอจะ REJECT hypothesis เต็ม
  รูปแบบตามเกณฑ์ข้อ 12 ของ MASTER COMMAND**
- **E3 (Overlap Continuation) เป็นบวก** (+16.26, PF 3.98) — แต่ n=4 ไม้เท่านั้น เป็น noise
  ล้วนๆ ไม่ใช่สัญญาณ ห้ามตื่นเต้นกับตัวเลขนี้เด็ดขาด
- **B2/B3/C1/C2 ไม่มีไม้เลย** — เงื่อนไข proxy ที่ตั้งไว้ (SMA trend + streak ยาวสำหรับ B2,
  displacement+compression สำหรับ B3, FVG 3-bar pattern สำหรับ C1/C2) เข้มงวดเกินไปสำหรับ
  หน้าต่าง 1 สัปดาห์ — ไม่ได้แปลว่ากลไกไม่มีอยู่จริง แค่หายากในช่วงสั้นๆ นี้
- **A2/A3/F1/F4 มีไม้เยอะแต่ win rate ต่ำมาก (12-43%)** — เงื่อนไข entry อาจกว้างเกินไป
  (over-trigger) หรือ target/SL ไม่สมดุลกับ noise ของ M1 — เป็นสัญญาณว่าเวอร์ชัน pilot
  เหล่านี้ต้องการ calibrate เพิ่มเติมเมื่อมีข้อมูลมากพอ ไม่ใช่ข้อสรุปเรื่อง edge

## สิ่งที่ต้องทำต่อ (เหมือนเดิม ไม่เปลี่ยนจากรอบก่อน)

1. ข้อมูลยาวขึ้นมาก (12-24 เดือน) เพื่อ calibrate threshold และมี sample size พอสรุปได้
2. ยืนยัน GMT offset จริงด้วย BrokerProbe.mq5
3. เขียน B1-B4 ใหม่ด้วย swing-based BOS/CHOCH state machine เต็มรูปแบบแทน SMA proxy
   เมื่อมีข้อมูลพอ calibrate fractal parameters
4. implement C3/D1-D3/H1-H3 เมื่อมีข้อมูลยาวพอ (ตอนนี้ข้ามไปเพราะข้อมูลไม่พอจริงๆ)

โค้ดทั้งหมด: `research/pilot/common.py` (helper), `research/pilot/hypotheses_pilot.py`
(strategy classes), `research/pilot/run_pilot_all30.py` (runner)
