# ai-trading-bot1 — XAU StraddleReverse toolkit

เครื่องมือประกอบการพัฒนา EA MQL5 **XAU StraddleReverse** (XAUUSD M1, straddle + stop-and-reverse)

## โครงสร้าง

```
docs/
  EXNESS_vs_VTMARKETS.md      วิเคราะห์การย้ายโบรก VT Markets -> Exness
                              (เขตเวลา/DST, ต้นทุนต่อไม้, รายการตรวจก่อนรัน)
MQL5/
  Scripts/
    BrokerProbe.mq5           ตรวจสเปกโบรก + เขตเวลา + DST  <-- รันตัวนี้ก่อน
    ExportSessionTicks.mq5    ส่งออก bid/ask 1 วินาที เฉพาะหน้าต่างที่ EA เทรด -> CSV
  Experts/
    XAU_StraddleReverse_v4_40.mq5   ซอร์ส v4.41 (เก็บไว้อ้างอิง)
  Presets/                    ไฟล์ .set ชุด v4.40
workflow/                     สคริปต์ compile / backtest / optimize ผ่าน command line
tools/
  mt5_report_charts.py        อ่านรายงาน Strategy Tester (.htm) -> กราฟ 4 ใบ + สรุปตัวเลข
  fonts/                      Noto Sans Thai (ให้ป้ายภาษาไทยบนกราฟไม่เพี้ยน)
```

## ทำกราฟจากผล backtest

```bash
pip install matplotlib
python3 tools/mt5_report_charts.py ReportTester-12345.htm -o charts/ --server-gmt 3
```

ได้ `charts/1_equity.png` (เส้นทุน + drawdown), `2_monthly.png` (กำไรรายเดือน),
`3_by_hour.png` (กำไรแยกรายชั่วโมง มีทั้งแกนเวลาเซิร์ฟเวอร์และ UTC) และ
`4_dist.png` (การกระจายกำไรต่อไม้)

`3_by_hour.png` คือใบที่ตอบว่าขอบของ EA มาจากชั่วโมงไหนจริง — ใช้ตรวจปัญหา DST
ในหัวข้อ 1 ของ `docs/EXNESS_vs_VTMARKETS.md`

## เริ่มยังไง

1. อ่าน `docs/EXNESS_vs_VTMARKETS.md` — โดยเฉพาะ **หัวข้อ 1** (backtest เดิมทดสอบ 2 หน้าต่างปนกัน)
2. วาง `MQL5/Scripts/*.mq5` ลงใน Data Folder ของ MT5 → คอมไพล์ใน MetaEditor
3. ลาก `BrokerProbe` ลงกราฟ XAUUSD → อ่านผลในแท็บ Experts

## หมายเหตุเวอร์ชัน

ซอร์ส **v5.00** ยังไม่อยู่ใน repo นี้ (Google Drive มีแต่คู่มือ ไม่มีไฟล์ `.mq5`)
เอกสารในโฟลเดอร์ `docs/` อ้างอิงโค้ดจาก v4.41 — จุดที่อาจต่างระบุไว้ในหัวข้อ 7 ของเอกสาร
