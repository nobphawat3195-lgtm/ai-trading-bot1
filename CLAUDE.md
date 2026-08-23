# CLAUDE.md — บริบทสำหรับ engineering plugin

โปรเจกต์นี้เป็นงานเดี่ยว (solo developer) ไม่มีทีม ไม่มีใครอื่นเชื่อมกับ repo นี้
เอกสารนี้ใช้ปรับพฤติกรรม engineering plugin (standup / code review /
architecture decision / incident response / technical docs) ให้ตรงกับ
โปรเจกต์นี้จริง แทนค่า default ที่ออกแบบมาสำหรับทีม

## บริบทโปรเจกต์

- คนเดียว → ข้าม feature ที่ออกแบบมาสำหรับทีม (daily standup แบบหลายคน,
  on-call rotation, สรุปทีมประจำสัปดาห์)
- Stack: MQL5 (Expert Advisor บน MetaTrader 5) + Python (backtest engine,
  chart report) ไม่มี CI/CD และไม่มี unit test framework ทั่วไป — "test"
  หลักคือ Strategy Tester backtest บนข้อมูลจริง กับสคริปต์จำลอง
  `tools/ea_backtest_engine.py`
- ไม่มีการรันจริงบน VPS/MT5 จากตรงนี้ได้ — งานที่ต้องรันบน MT5/VPS ต้องส่ง
  เป็นสคริปต์ให้รันเอง (ดูรูปแบบที่ใช้อยู่แล้วใน `workflow/00_อ่านก่อนเริ่ม.txt`
  และ `workflow/01_compile.bat` … `03_run_optimize.bat`)
- ภาษาเอกสาร: ไทยเป็นหลัก (README, `docs/`, `workflow/`) — คงรูปแบบนี้เมื่อ
  สร้างเอกสารใหม่ เว้นแต่จะขอเป็นภาษาอังกฤษ

## Standups

ไม่ต้องสร้าง/สรุป standup แบบทีม ถ้าต้องการสรุปความคืบหน้าให้สรุปแบบ
"เปลี่ยนอะไรไปนับจาก commit ล่าสุด / backtest รอบล่าสุด" แทน

## Code review

เช็คลิสต์ที่สำคัญกว่า style เพราะ EA นี้เทรดเงินจริง:

1. การเปลี่ยน logic ใน `.mq5` ต้อง compile ผ่าน 0 error/0 warning ก่อนเสมอ
   (`workflow/01_compile.bat`)
2. ทุกการเปลี่ยนที่กระทบ entry/exit/SL ต้อง backtest verify เทียบผล
   ก่อน-หลัง (`workflow/02_run_backtest_verify.bat` หรือ
   `tools/ea_backtest_engine.py`) ก่อนถือว่า "เสร็จ"
3. เช็คผลกระทบเรื่อง timezone/DST ทุกครั้งที่แก้อะไรเกี่ยวกับเวลาเปิด/ปิดไม้
   (จุดที่เคยพลาดมาแล้ว — ดู `docs/EXNESS_vs_VTMARKETS.md` หัวข้อ 1)
4. ระวัง hardcoded path/บัญชี/ค่าเฉพาะโบรก (เช่น symbol suffix `XAUUSD-VIP`)
   — ทำให้ portable ข้ามโบรกเมื่อทำได้

## Architecture decisions

บันทึกการตัดสินใจสำคัญ (เปลี่ยนโบรก, เปลี่ยนวิธีจัดการ timezone, เปลี่ยน
risk model) เป็นไฟล์แยกใน `docs/` ตามรูปแบบ `EXNESS_vs_VTMARKETS.md` —
ไม่ต้องใช้ ADR template ทางการ เขียนสั้น ตรงประเด็น มีหัวข้อ + เหตุผล +
รายการที่ต้องเช็คก่อนรันจริง

## Incident response

"Incident" ที่สำคัญสุดของโปรเจกต์นี้คือความผิดปกติตอนเทรดเงินจริง ไม่ใช่
downtime ของ service:

- Spread กระโดดผิดปกติ / โบรก requote บ่อย
- EA เปิดไม้ผิดช่วงเวลา (DST เพี้ยน, server time ไม่ตรงที่คาด)
- ผลขาดทุนเบี่ยงจาก backtest อย่างมีนัยสำคัญ

เมื่อเจอเคสแบบนี้ ให้ export tick ช่วงที่มีปัญหาด้วย
`MQL5/Scripts/ExportSessionTicks.mq5` แล้ววิเคราะห์ย้อนกับ
`tools/ea_backtest_engine.py` ก่อนสรุปสาเหตุ ไม่ต้องมี on-call/paging
เพราะไม่มีทีม

## Technical documentation

ตามรูปแบบเดิมของ repo: `README.md`/`docs/*.md` เป็นภาษาไทย โครงสร้างชัด
มี code block ของคำสั่งที่รันได้จริง และระบุว่า "รันตัวไหนก่อน" เหมือนที่
README ทำอยู่ตอนนี้
