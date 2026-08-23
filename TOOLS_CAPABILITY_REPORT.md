# TOOLS_CAPABILITY_REPORT.md

รายงานความสามารถจริงของ Environment และ Repository นี้
(ตรวจจากไฟล์จริงในโค้ดเบส ไม่ใช่การสมมติ) — อัปเดต 2026-08-23

## 0. สรุปสำคัญที่สุด — ต้องอ่านก่อน

**Repository นี้ไม่มี "EA Auto Backtest Engine" (RicardoBarato/ea-auto-backtest-engine)
อยู่จริง** ไม่มี submodule, ไม่มีการอ้างอิงถึงชื่อนี้ในโค้ด, README, หรือ workflow ใดๆ ทั้งสิ้น
(ค้นหาทั้ง repo แล้ว ไม่พบคำว่า "RicardoBarato" หรือ "ea-auto-backtest-engine")

สิ่งที่ repo นี้เรียกว่า **"EA Auto Backtest Engine" คือเครื่องมือของตัวเอง**:
`tools/ea_backtest_engine.py` — สคริปต์ Python ที่ผู้พัฒนาก่อนหน้าเขียนขึ้นมาเอง
เป็นตัวจำลอง (replay simulator) ที่ **ฮาร์ดโค้ดตรรกะของ EA `XAU_StraddleReverse` โดยเฉพาะ**
(straddle, SL, stop-and-reverse, ATR gate) ไม่ใช่ตัวคอมไพล์/รัน MQL5 ทั่วไป และไม่ใช่ตัว
แทน MT5 Strategy Tester

**Environment นี้เป็น Linux container ไม่มี MT5, ไม่มี MetaEditor, ไม่มี Wine**
คำสั่ง compile/backtest/optimize ที่ repo เตรียมไว้ (`workflow/*.bat`) เป็น **Windows batch
script ที่ต้องรันบนเครื่อง Windows ที่ติดตั้ง MT5 จริงเท่านั้น** — รันในเซสชันนี้ไม่ได้

**ไม่มีข้อมูลราคา/tick ใดๆ อยู่ใน repo เลย** (`.gitignore` บล็อก `*.csv`, `*.htm`, `*.html`,
`charts/` ไว้อย่างจงใจ) — ทุกการทดสอบสถิติ/backtest ต้องรอผู้ใช้ export ข้อมูลจาก MT5 เอง
แล้วส่งเข้ามาเป็นไฟล์

**ผลจากข้อเท็จจริงข้างบน**: ขั้นตอน Compile → MT5 Strategy Tester → Backtest → OOS →
Walk-Forward → Monte Carlo ตามที่ MASTER COMMAND กำหนด **ไม่สามารถรันได้จริงในเซสชันนี้
จนกว่าจะมีอย่างใดอย่างหนึ่ง**: (ก) ผู้ใช้รันเองบน VPS/เครื่อง Windows แล้วส่งไฟล์ผลลัพธ์กลับมา
หรือ (ข) ผู้ใช้ส่งไฟล์ราคา OHLC/tick จริงมาให้ แล้วให้ผมเขียนตัวจำลอง Python ทดสอบแทน
(แบบเดียวกับที่ `ea_backtest_engine.py` ทำกับ StraddleReverse — แต่ต้องเขียนเครื่องใหม่
เพราะตัวเดิมผูกกับตรรกะ EA เดิมเท่านั้น ใช้กับ hypothesis ใหม่ไม่ได้ตรงๆ)

ห้ามรายงานผล backtest ที่ไม่ได้รันจริงตามกฎข้อ 18/19 ของ MASTER COMMAND ดังนั้นในรอบนี้
งานที่ทำได้จริงคือ **Research + Hypothesis + เตรียมเครื่องมือ** เท่านั้น ยังไปไม่ถึงขั้น
Backtest/OOS/Walk-Forward — ดูสถานะเต็มใน `EDGE_DISCOVERY_REPORT.md`

---

## 1. Repository location & โครงสร้างจริง

```
/home/user/ai-trading-bot1/
├── MQL5/
│   ├── Experts/XAU_StraddleReverse_v4_40.mq5   EA เดิม source v4.41 (1,315 บรรทัด)
│   ├── Scripts/BrokerProbe.mq5                 ตรวจสเปกโบรก/GMT/DST (รันบน MT5 จริง)
│   ├── Scripts/ExportSessionTicks.mq5          export bid/ask 1 วิ -> CSV (รันบน MT5 จริง)
│   └── Presets/*.set                           3 ไฟล์ preset พารามิเตอร์
├── docs/EXNESS_vs_VTMARKETS.md                 บันทึกปัญหา DST/GMT ของ EA เดิม (สำคัญ)
├── tools/
│   ├── ea_backtest_engine.py                   Python replay simulator เฉพาะ StraddleReverse
│   ├── mt5_report_charts.py                    ทำกราฟจากรายงาน .htm หรือ deals.csv
│   └── fonts/NotoSansThai-Regular.ttf
├── workflow/
│   ├── 00_อ่านก่อนเริ่ม.txt                    คู่มือ (ยืนยันว่าต้องรันเองบน VPS)
│   ├── 01_compile.bat                          เรียก metaeditor64.exe /compile (Windows only)
│   ├── 02_backtest_verify.ini + .bat           เรียก terminal64.exe /config (Windows only)
│   └── 03_optimize.ini + .bat                  Optimization slow-complete (Windows only)
└── .gitignore                                  บล็อก *.csv *.htm *.html charts/
```

## 2. Scripts / Compile workflow

- `workflow/01_compile.bat` เรียก `metaeditor64.exe /compile:<path> /log:compile_log.txt`
  — ต้องมี MetaEditor ติดตั้งจริงบนเครื่อง Windows, ต้องแก้ path เองในไฟล์ (placeholder
  `YOUR_BROKER_MT5`, `YOURNAME`, `YOUR_TERMINAL_ID` ยังไม่ได้กรอก)
- ไม่มี CI/automation ใดๆ ที่รัน compile ได้จากเซสชันนี้ — **ไม่มี MetaEditor ในคอนเทนเนอร์**
  (ตรวจแล้ว: ไม่มี `wine`, ไม่มี `.exe` ใดๆ ในระบบ, เป็น Linux ล้วน)

## 3. Backtest workflow

- `02_run_backtest_verify.bat` + `02_backtest_verify.ini` — รัน MT5 Strategy Tester ผ่าน
  `/config:` แบบ command-line จริง (`Optimization=0`, `Model=1` = "1 Minute OHLC" ไม่ใช่
  every-tick) — **ต้องมี terminal64.exe ของ MT5 จริงบนเครื่อง Windows**
- ไฟล์ `.ini` ต้องเซฟเป็น UTF-16 LE ไม่งั้น MT5 อ่านไม่ออกแล้วใช้ค่า default เงียบๆ (ระบุไว้
  ในคู่มือ 00 เอง — เป็นความเสี่ยงที่ผู้ใช้ต้องระวังเวลาแก้ไฟล์เอง)
- Model=1 (1 Minute OHLC) มีความละเอียดต่ำกว่า "Every tick based on real ticks" — ผล
  backtest จาก workflow นี้จะ optimistic กว่าของจริงในระดับหนึ่ง (ไม่เห็น path ราคาในแท่ง)

## 4. Report output

- ผลออกเป็น `.htm`/`.xml` ใน `Tester\` ของ MT5 Data Folder — ต้องให้ผู้ใช้หาไฟล์เองแล้ว
  ส่งกลับมา (`.gitignore` บล็อกไม่ให้ commit `.htm` เข้า repo)
- `tools/mt5_report_charts.py` อ่านได้ทั้ง `.htm` (Strategy Tester report) และ `deals.csv`
  (จาก `ea_backtest_engine.py --out-deals`) → ออกกราฟ 4 ใบ (equity, monthly, by-hour, dist)
  ต้องการ `matplotlib` + `pip install` เอง (ยังไม่ตรวจว่าติดตั้งในคอนเทนเนอร์นี้หรือไม่)

## 5. Parameter handling / Optimization / Batch testing

- `03_optimize.ini` ใช้ syntax `param=start||start||step||end||Y` ของ MT5 native
  optimization (`OptimizationCriterion=1` = Profit Factor max, algorithm = slow complete
  ตามที่ตั้งใน terminal64 GUI ปกติ ไม่ใช่ genetic — ต้องตั้งเองใน GUI ก่อน)
- ไม่มี batch-testing แบบรันหลาย symbol/timeframe/EA พร้อมกันอัตโนมัติ — ระบบนี้ทำได้ทีละ
  1 EA (StraddleReverse) เท่านั้น, การ "กวาดพารามิเตอร์" ต้องพึ่ง MT5 native optimizer
  ที่รันได้เฉพาะบน Windows

## 6. Tick-data capability

- `ExportSessionTicks.mq5` export **เฉพาะหน้าต่างเวลาที่ EA เดิมเทรด** (ค่าเริ่มต้น
  ~1.5–3 ชม./วัน + กันชน 90 นาที) ความละเอียด **1 วินาที ไม่ใช่ทุก tick จริง** —
  ระบุไว้ในคอมเมนต์ของสคริปต์เองว่าไม่ใช่ตัวแทน Strategy Tester
- ต้องรันบนกราฟ MT5 จริงที่โหลดประวัติ tick ไว้แล้ว แล้ว export ผ่าน `MQL5\Files\`
- **ไม่มีไฟล์ tick/OHLC ใดๆ อยู่ใน repo นี้จริง** — ทุก hypothesis ใหม่ที่ต้องการ
  Statistical Discovery (ข้อ 5 ของ MASTER COMMAND) ต้องรอข้อมูลจากผู้ใช้ก่อนเสมอ

## 7. `tools/ea_backtest_engine.py` — ขีดจำกัดที่ต้องรู้ก่อนใช้ต่อ

- ฮาร์ดโค้ดตรรกะ straddle + SL + stop-and-reverse + ATR-gate ของ EA เดิมเท่านั้น
  (`Params` dataclass มีแต่ field ของกลยุทธ์นี้) — **เอามาทดสอบ hypothesis ใหม่ตรงๆ ไม่ได้**
  ต้องเขียนเอนจินใหม่ (หรือ generalize ตัวนี้) ถ้าจะทดสอบกลไกตลาดแบบอื่น เช่น FVG, BOS,
  liquidity sweep, mean reversion ฯลฯ — งานนี้เป็นงานที่ต้องทำในเฟสถัดไป ยังไม่ได้ทำตอนนี้
- ต้องการ input เป็น CSV `server_time,bid,ask` จาก `ExportSessionTicks.mq5` เท่านั้น
- ผู้เขียนเดิมระบุเองในคอมเมนต์ (บรรทัด 24-30): ความละเอียด 1 วินาทีไม่ใช่ทุก tick, เวลา SL
  กับไม้กลับด้านโดนพร้อมกันเลือก SL ก่อนเสมอ (pessimistic), ตัวเลขกำไรสัมบูรณ์ไม่เท่ากับ
  Strategy Tester จริง — ใช้เทียบ A/B กันเองได้ดีกว่าใช้อ้างอิงตัวเลขเดี่ยว

## 8. ข้อสรุป: จะเดินหน้าต่อยังไงตาม MASTER COMMAND

เพื่อไม่ขัดกับกฎ "ห้ามสร้าง Backtesting Engine ใหม่ถ้าของเดิมทำงานได้อยู่แล้ว" และ
"ห้ามสมมติ/รายงานผลที่ไม่ได้รันจริง" พร้อมกัน แนวทางที่ตรงกับข้อเท็จจริงของ environment นี้
คือ:

1. งานที่ทำได้ทันทีในเซสชันนี้โดยไม่ต้องรอผู้ใช้: EA analysis, Forbidden logic, 30
   hypotheses, ออกแบบ statistical test plan ต่อ hypothesis (ทำแล้วในเอกสารนี้ชุด)
2. งานที่ต้อง **รอข้อมูลจากผู้ใช้ก่อน** ถึงจะเริ่มได้จริง (ไม่ใช่ optional):
   - ไฟล์ราคา XAUUSD M1 (และ/หรือ tick) ช่วงเวลาให้กว้างที่สุดเท่าที่มี ไม่ใช่แค่หน้าต่าง
     ที่ EA เดิมเทรด — เพราะ hypothesis ใหม่จะไม่ได้จำกัดอยู่แค่ 1.5 ชม./วันเดิม
   - ถ้าต้องการทดสอบผ่าน MT5 Strategy Tester จริง (ความละเอียดสูงกว่า) ผู้ใช้ต้องรัน
     `workflow/*.bat` เองบนเครื่อง Windows/VPS แล้วส่งไฟล์ report กลับมา
3. เมื่อมีข้อมูลแล้ว จะขยาย/เขียน Python backtest engine ทั่วไป (ไม่ผูกกับ StraddleReverse)
   ให้รองรับ event-driven entry ตาม hypothesis ใหม่ — เป็นส่วนขยายของเครื่องมือเดิมในตระกูล
   เดียวกัน ไม่ใช่การสร้างเอนจินคู่ขนานที่ซ้ำซ้อนกับ Strategy Tester
