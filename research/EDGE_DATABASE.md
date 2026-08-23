# research/EDGE_DATABASE.md — Research Memory

ฐานข้อมูลกลาง เก็บสถานะของทุก Hypothesis เพื่อไม่ให้ทดลองซ้ำโดยไม่มีเหตุผลใหม่
(กฎข้อ 14 ของ MASTER COMMAND) อัปเดตทุกครั้งที่มีรอบ Discovery/Backtest/OOS/Walk-Forward
/Robustness ใหม่

**สถานะ ณ 2026-08-23**: ยังไม่มี hypothesis ใดถูกทดสอบด้วยข้อมูลจริง — เหตุผลและสิ่งที่
บล็อกอยู่ดูใน `EDGE_DISCOVERY_REPORT.md` และ `TOOLS_CAPABILITY_REPORT.md`

## คอลัมน์

| คอลัมน์ | ความหมาย |
|---|---|
| ID | รหัส hypothesis (ตรงกับไฟล์ใน `research/hypotheses/`) |
| Name | ชื่อสั้น |
| Code Version | เวอร์ชันของ prototype MQL5/Python (ถ้ามี) |
| Dataset | ชุดข้อมูลที่ใช้ทดสอบ + ช่วงวันที่ |
| Backtest Period | ช่วง Discovery/Validation/OOS ที่ใช้จริง |
| Discovery Result | ผล 60% Discovery (win-rate, expectancy, PF, sample size) |
| OOS Result | ผล 20% Out-of-Sample |
| Walk-Forward | ผล walk-forward (stable/unstable) |
| Robustness | ผลทดสอบ stress (spread/slippage/commission/Monte Carlo) |
| Final Score | ตามเกณฑ์ข้อ 13 ของ MASTER COMMAND (0-100) |
| Decision | ACCEPT / REJECT / RESEARCH FURTHER / PENDING DATA |
| Reject Reason | เหตุผลถ้า REJECT — ใช้เป็น input สร้าง hypothesis รอบถัดไป |

## ตารางสถานะ

| ID | Name | Code Version | Dataset | Backtest Period | Discovery | OOS | Walk-Forward | Robustness | Score | Decision | Reject Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Liquidity Sweep Reversal | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้130 สุทธิ-63.18 PF0.61 | - | - | MC+stress รันแล้ว (pilot) | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน + threshold ยังไม่ calibrate ดูรายละเอียด research/pilot/ |
| A2 | Stop Run Continuation | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้276 สุทธิ-203.92 PF0.68 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน ดูรายละเอียด research/pilot/PILOT_RESULTS_ALL30* |
| A3 | Equal High/Low Reclaim | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้332 สุทธิ-180.82 PF0.61 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน ดูรายละเอียด research/pilot/PILOT_RESULTS_ALL30* |
| A4 | Prev Session H/L Sweep-Fail | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้6 สุทธิ-1.56 PF0.84 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | n=6 ไม้ เล็กมาก ดูรายละเอียด research/pilot/PILOT_RESULTS_ALL30* |
| B1 | BOS Continuation | pilot v0 (SMA proxy, ไม่ใช่ swing-based BOS จริง) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้120 สุทธิ-4.09 PF0.99 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | proxy หยาบ + sample เล็กเกิน ต้องเขียน swing-based ใหม่ |
| B2 | CHOCH Reversal | pilot v0 (SMA proxy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้0 (ไม่มีสัญญาณเลยในหน้าต่างนี้) | - | - | - | - | PILOT ONLY — NOT DISCOVERY | เงื่อนไข proxy เข้มงวดเกินสำหรับ 1 สัปดาห์ ไม่ใช่หลักฐานว่าไม่มี edge |
| B3 | Displacement-Compression | pilot v0 (SMA/ATR proxy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้0 (ไม่มีสัญญาณเลยในหน้าต่างนี้) | - | - | - | - | PILOT ONLY — NOT DISCOVERY | เงื่อนไข proxy เข้มงวดเกินสำหรับ 1 สัปดาห์ ไม่ใช่หลักฐานว่าไม่มี edge |
| B4 | Trend Transition MTF | pilot v0 (SMA proxy หยาบมาก) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้41 สุทธิ-55.86 PF0.72 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | proxy หยาบมาก ไม่ใช่ multi-timeframe จริง |
| C1 | FVG Fill Reversal | pilot v0 (3-bar FVG) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้0 (ไม่มีสัญญาณเลยในหน้าต่างนี้) | - | - | - | - | PILOT ONLY — NOT DISCOVERY | เงื่อนไข retest เข้มงวดเกินสำหรับ 1 สัปดาห์ |
| C2 | FVG Retracement Continuation | pilot v0 (3-bar FVG + trend filter) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้0 (ไม่มีสัญญาณเลยในหน้าต่างนี้) | - | - | - | - | PILOT ONLY — NOT DISCOVERY | เงื่อนไข retest เข้มงวดเกินสำหรับ 1 สัปดาห์ |
| C3 | Session-Open Gap Fill | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ daily gap หลายสิบวัน มีแค่ ~6 gap ในข้อมูลปัจจุบัน |
| D1 | Daily Vol Expansion Breakout | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ 60+ วันคำนวณ percentile มีแค่ ~7 daily bar |
| D2 | Asian Compression→London BO | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ 20+ วันคำนวณ percentile มีแค่ ~7 วัน |
| D3 | Range Expansion Day Cont. | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ 20+ วันคำนวณ percentile มีแค่ ~7 วัน |
| E1 | London Open Momentum | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้1 สุทธิ-9.18 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=1 ไม้ ไม่มีความหมายทางสถิติเลย |
| E2 | NY Open Range-Extreme Fade | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้1 สุทธิ-10.61 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=1 ไม้ ไม่มีความหมายทางสถิติเลย |
| E3 | London/NY Overlap Cont. | pilot v0 (SMA proxy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้4 สุทธิ+16.26 PF3.98 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=4 ไม้ ผลบวกเป็น noise ห้ามตีความเป็น edge |
| E4 | Asian Range BO at London | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้4 สุทธิ-86.07 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=4 ไม้ ไม่มีความหมายทางสถิติเลย |
| F1 | VWAP Extreme Deviation | pilot v0 (rolling VWAP proxy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้341 สุทธิ-261.68 PF0.62 winrate 12.3% | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | winrate ต่ำผิดปกติ threshold ต้อง calibrate ใหม่ |
| F2 | Asian Range Reversion | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้7 สุทธิ-25.63 PF0.22 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=7 ไม้ เล็กมาก |
| F3 | Consecutive-Candle Overext. | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้181 สุทธิ-97.75 PF0.52 | - | - | MC+stress รันแล้ว (pilot) | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน + threshold ยังไม่ calibrate ดูรายละเอียด research/pilot/ |
| F4 | VWAP Band Fade | pilot v0 (rolling VWAP±kσ proxy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้528 สุทธิ-397.72 PF0.36 winrate 23.7% | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | winrate ต่ำ over-trigger ต้อง calibrate ใหม่ |
| G1 | Momentum Burst Continuation | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้276 สุทธิ-379.13 PF0.55 | - | - | MC+stress รันแล้ว (pilot) | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน + threshold ยังไม่ calibrate ดูรายละเอียด research/pilot/ |
| G2 | Breakout-and-Retest | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้174 สุทธิ-129.58 PF0.00 winrate 0% | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | winrate 0% ผิดปกติ — สงสัยว่า retest tolerance/logic ต้องทบทวนก่อนเชื่อ |
| G3 | Shallow-Pullback Continuation | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้132 สุทธิ-116.16 PF0.77 | - | - | pilot only, no MC/stress this round | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน ดูรายละเอียด research/pilot/PILOT_RESULTS_ALL30* |
| G4 | Tick-Volume Burst Confirm | pilot v0 (G1 + volume filter) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้2 สุทธิ-9.28 | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=2 ไม้ ไม่มีความหมายทางสถิติเลย |
| H1 | Hour-of-Day Seasonality | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ 2-3 ปีกัน false positive จาก multiple-testing มีแค่ 1 สัปดาห์ |
| H2 | Day-of-Week Effect | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ 2-3 ปี มีแค่ 1 ตัวอย่าง/วันในสัปดาห์นี้ |
| H3 | Daily Streak Reversal | - | - | - | - | - | - | - | - | NOT TESTABLE (data) | ต้องการ empirical distribution จาก 3-5 ปี มีแค่ ~7 daily bar |
| H4 | Prev Session Return Autocorr. | pilot v0 (correlation test เท่านั้น ไม่ใช่ trading strategy) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | correlation=-0.235 (n=5 คู่) | - | - | - | - | PILOT ONLY — NOT DISCOVERY | n=5 คู่ ไม่มีนัยสำคัญทางสถิติเลย |

**หมายเหตุ**: "PENDING DATA" ≠ "REJECT" — เป็นสถานะรอทรัพยากร (ข้อมูลราคาจริง) ไม่ใช่ผลการ
ทดสอบ ห้ามตีความว่า hypothesis เหล่านี้ล้มเหลวแล้ว ตามกฎข้อ 18-19 ของ MASTER COMMAND
(ห้ามรายงานผลที่ไม่ได้รันจริง — แถวเหล่านี้จึงไม่มีตัวเลขผลลัพธ์ใดๆ ใส่ไว้เลย)

**"PILOT ONLY — NOT DISCOVERY" ≠ "REJECT" เช่นกัน** — ทั้ง 23 hypotheses ที่ทดสอบได้
รันจริงบนข้อมูล 1 สัปดาห์แล้ว (ไม่ใช่สมมติ) แต่ sample เล็กเกินไปและ implementation เป็น
เวอร์ชันตัดทอน (โดยเฉพาะหมวด B ที่ใช้ SMA proxy แทน BOS/CHOCH จริง) ผลขาดทุนที่เห็นไม่ใช่
หลักฐานเพียงพอจะ REJECT hypothesis เต็มรูปแบบ — รายละเอียดที่
`research/pilot/PILOT_RESULTS_ALL30_2026-07-01_to_07.md`

**"NOT TESTABLE (data)"** — C3, D1-D3, H1-H3 (7 ข้อ) ข้ามไปทั้งหมด ไม่ได้พยายามรันด้วยซ้ำ
เพราะต้องการ sample size ระดับสัปดาห์-ปีที่ข้อมูลปัจจุบัน (1 สัปดาห์) ไม่มีทางให้ได้เลย
การพยายามรันจะได้ตัวเลขที่ไม่มีความหมายทางสถิติใดๆ (เช่น percentile จาก 7 จุดข้อมูล)
จึงเลือกไม่รันแทนที่จะรันแล้วรายงานตัวเลขที่หลอกตัวเอง

## Log การอัปเดต

- **2026-08-23**: สร้างฐานข้อมูลครั้งแรก ลงทะเบียน 30 hypotheses (หมวด A-H) สถานะ PENDING
  DATA ทั้งหมด — ยังไม่มีข้อมูลราคาจริงในเซสชันนี้ (ดูรายละเอียดใน `TOOLS_CAPABILITY_REPORT.md`)
- **2026-08-23** (รอบ 2): ผู้ใช้ส่งไฟล์ M1 OHLC จริงของ XAUUSD (VT Markets VIP, 1 สัปดาห์
  2026-06-30→07-07) ผ่าน Google Drive — ขยาย `hypothesis_backtest_engine.py` ให้อ่าน
  รูปแบบ MT5 native export ได้ แล้วรัน pilot บน A1/G1/F3 (เวอร์ชันตัดทอน) จริง สถานะ
  เปลี่ยนเป็น `PILOT ONLY — NOT DISCOVERY` ยังต้องการข้อมูลยาวกว่านี้มาก (12-24 เดือน)
  ก่อนเริ่ม Discovery จริงตามข้อ 5 ของ MASTER COMMAND
- **2026-08-23** (รอบ 3): ผู้ใช้ขอให้ pilot ครบทั้ง 30 hypotheses บนข้อมูลชุดเดียวกัน —
  implement เวอร์ชันตัดทอนเพิ่มอีก 20 ตัว (`research/pilot/hypotheses_pilot.py`,
  `research/pilot/common.py`) รันจริงได้ 23/30 (7 ข้อคือ C3/D1-D3/H1-H3 ข้ามเพราะข้อมูล
  ไม่พอจริงๆ ไม่ใช่ error) ผลทุกตัวยังเป็น `PILOT ONLY — NOT DISCOVERY` เหมือนเดิม
  รายละเอียดที่ `research/pilot/PILOT_RESULTS_ALL30_2026-07-01_to_07.md`
