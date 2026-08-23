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
| A2 | Stop Run Continuation | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M1/M5 จริง |
| A3 | Equal High/Low Reclaim | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M5/M15 จริง |
| A4 | Prev Session H/L Sweep-Fail | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M1/M15 จริง |
| B1 | BOS Continuation | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M5/M15 จริง |
| B2 | CHOCH Reversal | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M15 จริง |
| B3 | Displacement-Compression | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M5 จริง |
| B4 | Trend Transition MTF | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M5+H1 จริง |
| C1 | FVG Fill Reversal | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M1/M5 จริง |
| C2 | FVG Retracement Continuation | - | - | - | - | - | - | - | - | PENDING DATA | รอ OHLC M5 จริง |
| C3 | Session-Open Gap Fill | - | - | - | - | - | - | - | - | PENDING DATA | รอ Daily+M5 จริง |
| D1 | Daily Vol Expansion Breakout | - | - | - | - | - | - | - | - | PENDING DATA | รอ Daily OHLC 2-3 ปี |
| D2 | Asian Compression→London BO | - | - | - | - | - | - | - | - | PENDING DATA | รอ M15 จริง |
| D3 | Range Expansion Day Cont. | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5/M15 จริง |
| E1 | London Open Momentum | - | - | - | - | - | - | - | - | PENDING DATA | รอ M1/M5 จริง |
| E2 | NY Open Range-Extreme Fade | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5/M15 จริง |
| E3 | London/NY Overlap Cont. | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5/M15 จริง |
| E4 | Asian Range BO at London | - | - | - | - | - | - | - | - | PENDING DATA | รอ M15 จริง |
| F1 | VWAP Extreme Deviation | - | - | - | - | - | - | - | - | PENDING DATA | รอ M1+tick-volume จริง |
| F2 | Asian Range Reversion | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5 จริง |
| F3 | Consecutive-Candle Overext. | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้181 สุทธิ-97.75 PF0.52 | - | - | MC+stress รันแล้ว (pilot) | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน + threshold ยังไม่ calibrate ดูรายละเอียด research/pilot/ |
| F4 | VWAP Band Fade | - | - | - | - | - | - | - | - | PENDING DATA | รอ M1/M5+volume จริง |
| G1 | Momentum Burst Continuation | pilot v0 (simplified) | XAUUSDVIP M1, 1wk real | 2026-06-30→07-07 (pilot only) | ไม้276 สุทธิ-379.13 PF0.55 | - | - | MC+stress รันแล้ว (pilot) | - | PILOT ONLY — NOT DISCOVERY | sample เล็กเกิน + threshold ยังไม่ calibrate ดูรายละเอียด research/pilot/ |
| G2 | Breakout-and-Retest | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5 จริง |
| G3 | Shallow-Pullback Continuation | - | - | - | - | - | - | - | - | PENDING DATA | รอ M5 จริง |
| G4 | Tick-Volume Burst Confirm | - | - | - | - | - | - | - | - | PENDING DATA | รอ M1+tick-volume จริง |
| H1 | Hour-of-Day Seasonality | - | - | - | - | - | - | - | - | PENDING DATA | รอ H1/M15 2-3 ปี |
| H2 | Day-of-Week Effect | - | - | - | - | - | - | - | - | PENDING DATA | รอ Daily 2-3 ปี |
| H3 | Daily Streak Reversal | - | - | - | - | - | - | - | - | PENDING DATA | รอ Daily 3-5 ปี |
| H4 | Prev Session Return Autocorr. | - | - | - | - | - | - | - | - | PENDING DATA | รอ M15 จริง |

**หมายเหตุ**: "PENDING DATA" ≠ "REJECT" — เป็นสถานะรอทรัพยากร (ข้อมูลราคาจริง) ไม่ใช่ผลการ
ทดสอบ ห้ามตีความว่า hypothesis เหล่านี้ล้มเหลวแล้ว ตามกฎข้อ 18-19 ของ MASTER COMMAND
(ห้ามรายงานผลที่ไม่ได้รันจริง — แถวเหล่านี้จึงไม่มีตัวเลขผลลัพธ์ใดๆ ใส่ไว้เลย)

**"PILOT ONLY — NOT DISCOVERY" ≠ "REJECT" เช่นกัน** — A1/G1/F3 รันจริงบนข้อมูล 1 สัปดาห์
แล้ว (ไม่ใช่สมมติ) แต่ sample เล็กเกินไปและ implementation เป็นเวอร์ชันตัดทอน ผลขาดทุน
ที่เห็นไม่ใช่หลักฐานเพียงพอจะ REJECT hypothesis เต็มรูปแบบ — รายละเอียดที่
`research/pilot/PILOT_RESULTS_2026-07-01_to_07.md`

## Log การอัปเดต

- **2026-08-23**: สร้างฐานข้อมูลครั้งแรก ลงทะเบียน 30 hypotheses (หมวด A-H) สถานะ PENDING
  DATA ทั้งหมด — ยังไม่มีข้อมูลราคาจริงในเซสชันนี้ (ดูรายละเอียดใน `TOOLS_CAPABILITY_REPORT.md`)
- **2026-08-23** (รอบ 2): ผู้ใช้ส่งไฟล์ M1 OHLC จริงของ XAUUSD (VT Markets VIP, 1 สัปดาห์
  2026-06-30→07-07) ผ่าน Google Drive — ขยาย `hypothesis_backtest_engine.py` ให้อ่าน
  รูปแบบ MT5 native export ได้ แล้วรัน pilot บน A1/G1/F3 (เวอร์ชันตัดทอน) จริง สถานะ
  เปลี่ยนเป็น `PILOT ONLY — NOT DISCOVERY` ยังต้องการข้อมูลยาวกว่านี้มาก (12-24 เดือน)
  ก่อนเริ่ม Discovery จริงตามข้อ 5 ของ MASTER COMMAND
