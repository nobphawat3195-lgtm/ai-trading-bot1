# EDGE_DISCOVERY_REPORT.md

## สถานะ: **NO VALID EDGE FOUND — TESTING BLOCKED (ไม่ใช่ REJECT)**

Top 5 New Edges ยังไม่มีให้รายงานในรอบนี้ เพราะยังไม่มี hypothesis ใดถูกทดสอบด้วยข้อมูลราคา
จริงเลยแม้แต่ตัวเดียว การรายงานตัวเลข backtest/OOS/walk-forward/Monte Carlo ใดๆ ในตอนนี้จะ
เป็นการ**สมมติผลลัพธ์ที่ไม่ได้รันจริง** ซึ่งขัดกับกฎข้อ 18-19 ของ MASTER COMMAND โดยตรง
ดังนั้นรายงานฉบับนี้จึงต้องบอกสถานะจริงแทนการ "หาผู้ชนะให้ได้" ตามกฎข้อ 19

---

## ทำไมถึงหยุดอยู่ตรงนี้ (สรุปจาก TOOLS_CAPABILITY_REPORT.md)

1. **ไม่มีข้อมูลราคา/tick ใดๆ อยู่ใน repository นี้จริง** — `.gitignore` บล็อก `*.csv`,
   `*.htm`, `*.html` ไว้อย่างจงใจ ทุกไฟล์ข้อมูลต้อง export จาก MT5 โดยผู้ใช้แล้วส่งเข้ามาเอง
2. **ไม่มี MT5 / MetaEditor ในเซสชันนี้** — เป็น Linux container ล้วน `workflow/*.bat`
   ต้องรันบนเครื่อง Windows/VPS ของผู้ใช้เท่านั้น
3. **"EA Auto Backtest Engine" ที่ MASTER COMMAND อ้างถึง (RicardoBarato/
   ea-auto-backtest-engine) ไม่มีอยู่ใน repo/environment นี้จริง** — เครื่องมือที่มีจริง
   (`tools/ea_backtest_engine.py`) เป็นตัวจำลอง Python ที่เขียนขึ้นมาเองเฉพาะ EA
   `XAU_StraddleReverse` เท่านั้น ใช้ทดสอบ hypothesis ใหม่ทั้ง 30 ข้อตรงๆ ไม่ได้ ต้องขยาย/
   เขียนเอนจินใหม่ให้ generalize ก่อน (เป็นงานเฟสถัดไป ยังไม่ได้ทำ)

ผลคือ **ทุกขั้นตอนตั้งแต่ Statistical Discovery (ข้อ 5) เป็นต้นไปของ MASTER COMMAND ยังเริ่ม
ไม่ได้จริง** — สิ่งที่ทำได้และทำเสร็จแล้วในรอบนี้คือขั้นตอน 1-6 ของลำดับข้อ 20 เท่านั้น
(ตรวจ environment, ตรวจ EA เดิม, Forbidden Logic, 30 Hypotheses)

## งานที่เสร็จแล้วในรอบนี้

| ไฟล์ | สถานะ |
|---|---|
| `TOOLS_CAPABILITY_REPORT.md` | เสร็จ — ตรวจ environment จริงแล้ว |
| `CURRENT_EA_ANALYSIS.md` | เสร็จ — วิเคราะห์ EA เดิมครบทุกหัวข้อที่ MASTER COMMAND กำหนด |
| `FORBIDDEN_LOGIC.md` | เสร็จ — ระบุ 6 กลไกที่ห้ามใช้เป็นแกนหลักของ hypothesis ใหม่ |
| `research/hypotheses/*.md` (8 ไฟล์, 30 hypotheses, หมวด A-H) | เสร็จ — ครบทุก field
  ตามฟอร์แมตข้อ 4 พร้อม Test Method ต่อข้อ |
| `research/EDGE_DATABASE.md` | เสร็จ — ลงทะเบียนทั้ง 30 ข้อ สถานะ PENDING DATA |
| `MQL5/Scripts/ExportOHLC.mq5` | เสร็จ — สคริปต์ export OHLC เต็มวันทุก session (ใหม่) |
| `tools/hypothesis_backtest_engine.py` | เสร็จ — เอนจินทั่วไป รองรับ split/walk-forward/
  Monte Carlo/stress test ผ่าน self-test ด้วยข้อมูลสังเคราะห์แล้ว (ยังไม่มี Strategy
  ของ hypothesis ใด implement จริง — รอข้อมูลก่อนเขียนเพื่อกัน bug เงียบ) |

**สำคัญ**: ตัวเลขใดๆ ที่ปรากฏใน self-test ของ `hypothesis_backtest_engine.py` มาจาก
random-walk สังเคราะห์ ไม่ใช่ตลาดจริง และไม่ใช่ผล backtest ของ hypothesis ใดทั้งสิ้น —
ใช้ตรวจกลไกเอนจินเท่านั้น ห้ามนำไปอ้างเป็นหลักฐาน edge เด็ดขาด

## สิ่งที่ต้องการจากผู้ใช้เพื่อเดินหน้าต่อ (บล็อกอยู่จริง ไม่ใช่ทางเลือก)

ต้องมีอย่างน้อย 1 ใน 2 ทางนี้ก่อน Statistical Discovery จะเริ่มได้:

**ทาง A — ส่งข้อมูลราคาจริงเข้ามา** (แนะนำ เพราะทำต่อในเซสชันนี้ได้ทันที)
- รัน **`MQL5/Scripts/ExportOHLC.mq5`** (สร้างเสร็จแล้วในรอบนี้) บนกราฟ XAUUSD ของ MT5 —
  ตั้ง `InpTF` เลือก timeframe (แนะนำรัน M5 อย่างน้อย 1 รอบสำหรับ execution + H1 อีก 1 รอบ
  สำหรับบริบท market-structure ของหมวด B/D) ตั้งช่วงวันที่ให้ยาวที่สุดเท่าที่มีประวัติ แล้ว
  ส่งไฟล์ `xau_ohlc_*.csv` ที่ได้กลับมา — ครอบคลุม **ทั้งวัน ไม่ใช่แค่หน้าต่าง 1.5-3 ชม./วัน
  ที่ EA เดิมเทรด** เพราะ hypothesis ใหม่ทั้ง 30 ข้อกระจายอยู่ทุก session (Asian/London/NY/
  Overlap)
- ยิ่งย้อนหลังได้นานยิ่งดี (ควรได้อย่างน้อย 12-24 เดือนสำหรับ M1/M5 discovery, 2-3 ปีสำหรับ
  hypothesis หมวด H ที่ต้องการ sample size ระดับปีเพื่อแยก seasonality จริงจาก noise)
- ไฟล์ที่ได้จะมี tick-volume ติดมาด้วยอัตโนมัติ ใช้กับหมวด F1/F4/G4 ได้ (VWAP, volume-burst)
- ถ้าใช้ script/data source อื่นแทนก็ได้ ขอแค่รูปแบบ
  timestamp,open,high,low,close(,volume) ที่ระบุ timezone ชัดเจน — โหลดผ่าน
  `tools/hypothesis_backtest_engine.py:load_ohlc_csv()` ได้เหมือนกัน

**ทาง B — รัน MT5 Strategy Tester เองแล้วส่งผลกลับมา** (ใช้ตรวจ EA เดิมต่อ ไม่ใช้ทดสอบ
hypothesis ใหม่ เพราะ hypothesis ใหม่ยังไม่มี MQL5 prototype)
- ใช้ `workflow/*.bat` ตามคู่มือ `workflow/00_อ่านก่อนเริ่ม.txt` แก้ path ให้ตรงเครื่องตัวเอง
  ก่อนรัน

เมื่อมีข้อมูลจากทาง A แล้ว งานขั้นถัดไปคือ (เอนจินข้อ 1 เตรียมพร้อมแล้ว):
1. ~~เขียน generic Python OHLC backtest engine~~ **เสร็จแล้ว** —
   `tools/hypothesis_backtest_engine.py` (ผ่าน self-test ด้วยข้อมูลสังเคราะห์)
2. implement แต่ละ hypothesis เป็นคลาส `Strategy` (entry/exit ตาม field ที่นิยามไว้ใน
   `research/hypotheses/*.md`) แล้วรัน Statistical Discovery บน 60% แรกของข้อมูลจริง
   (แบ่งด้วย `split_discovery_validation_oos()`) — ยังทำไม่ได้จนกว่าจะมีข้อมูลจริง
3. คัด candidate ที่ผ่านเกณฑ์สถิติเบื้องต้น → เขียน MQL5 prototype (เฉพาะที่ผ่านเท่านั้น)
4. Validation (20%) → Out-of-Sample (20%) → Walk-Forward (`walk_forward_windows()`) →
   Robustness (`monte_carlo_trade_order()` + `stress_test()`) → Scoring ตามข้อ 9-13
5. อัปเดต `research/EDGE_DATABASE.md` และรายงานผลจริงในไฟล์นี้ทุกรอบ

## คำมั่นสัญญาต่อกฎข้อ 16, 18, 19

- จะไม่เลือกกลยุทธ์จาก highest-profit/win-rate เพียงอย่างเดียวเมื่อถึงขั้นทดสอบจริง
- จะไม่รายงานตัวเลข backtest ที่ไม่ได้รันจริง แม้จะช่วยให้ดูมีความคืบหน้า
- เมื่อมีข้อมูลและทดสอบแล้วพบว่า hypothesis ใดล้มเหลว จะบันทึกเหตุผลความล้มเหลวลง
  `research/EDGE_DATABASE.md` และใช้เป็น input สร้าง hypothesis รอบถัดไปตามข้อ 15 ไม่ใช่
  ปิดจบแค่นั้น
