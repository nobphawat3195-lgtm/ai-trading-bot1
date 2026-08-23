# Pilot Run Results — 2026-06-30 22:00 to 2026-07-07 18:51 UTC

**สถานะ: PILOT — ไม่ใช่ Statistical Discovery ตามข้อ 5 ของ MASTER COMMAND**

ตัวเลขในเอกสารนี้มาจากการรันจริงบนข้อมูลราคาจริง (ไม่ได้สมมติ) แต่ **ห้ามใช้ตัดสิน
ACCEPT/REJECT ของ hypothesis ใดทั้งสิ้น** ด้วยเหตุผล 3 ข้อ:

1. **Sample size เล็กเกินไป** — ข้อมูลมีแค่ ~6,526 แท่ง M1 (ประมาณ 1 สัปดาห์) ขณะที่
   `research/hypotheses/*.md` ทุกข้อระบุไว้ชัดเจนว่าต้องการข้อมูลระดับเดือน-ปี
2. **Strategy ที่ใช้เป็นเวอร์ชันย่อ** — A1/G1/F3 implement แบบตัดทอนจากสเปกเต็ม (ดู
   docstring ในแต่ละคลาสที่ `research/pilot/run_pilot_2026w27.py`) โดยเฉพาะ threshold
   ที่ควรมาจาก empirical percentile (ต้องใช้ข้อมูลยาว) ถูกแทนด้วยค่าคงที่ชั่วคราว
3. **GMT offset ยังไม่ยืนยัน** — สมมติ GMT+3 ตามเอกสาร `docs/EXNESS_vs_VTMARKETS.md`
   (VT Markets ฤดูร้อน) เพราะชื่อไฟล์ตรงกับสัญลักษณ์ `XAUUSD-VIP` แต่ยังไม่ได้ตรวจสอบ
   ด้วย `BrokerProbe.mq5` จริงบนบัญชีที่ export ข้อมูลนี้มา

**วัตถุประสงค์ของ pilot รอบนี้คือพิสูจน์ว่า pipeline ทำงานถูกต้องบนข้อมูลจริง** (โหลด
ไฟล์ MT5 native export ได้, แปลงเวลาไม่ผิด, เข้า/ออกไม่มี look-ahead, คิดต้นทุนจริงจาก
คอลัมน์ spread ในไฟล์, Monte Carlo/Stress test รันได้) — บรรลุวัตถุประสงค์นี้แล้ว

## ข้อมูลที่ใช้

| รายการ | ค่า |
|---|---|
| ไฟล์ | `research/data/XAUUSDVIP_M1_202607010100_202607072151.csv` |
| แหล่งที่มา | Google Drive ของผู้ใช้ (ไฟล์ export จาก MT5 อยู่แล้ว) |
| รูปแบบ | MT5 native "Export Bars" (tab-delimited, ไม่มี metadata เขตเวลา) |
| จำนวนแท่ง | 6,526 แท่ง M1 |
| ช่วงเวลา (UTC หลังแปลง) | 2026-06-30 22:00 ถึง 2026-07-07 18:51 |
| GMT offset ที่ใช้แปลง | +3 (สมมติจากเอกสาร VT Markets ฤดูร้อน — ยังไม่ยืนยัน) |
| ต้นทุนที่ใช้ | สเปรดเฉลี่ยจากคอลัมน์จริงในไฟล์ ≈ $0.30, คอมมิชชัน $0.07, สลิปเพจ $0.05 (ประมาณ) |

## ผลลัพธ์ (สุทธิที่ทุน $10,000 เริ่มต้น, ไม่ผูก lot sizing จริง)

| Hypothesis (เวอร์ชันย่อ) | ไม้ | สุทธิ | PF | ชนะ% | R เฉลี่ย | Max DD | Stress net (x2 spread / x3 slip / x2 comm) |
|---|---|---|---|---|---|---|---|
| A1 Liquidity Sweep Reversal | 130 | -63.18 | 0.61 | 46.9% | -0.31 | 0.7% | -121.68 / -89.18 / -72.28 |
| G1 Momentum Burst Continuation | 276 | -379.13 | 0.55 | 37.3% | -0.27 | 3.9% | -503.33 / -434.33 / -398.45 |
| F3 Streak Overextension | 181 | -97.75 | 0.52 | 27.1% | -0.55 | 1.1% | -179.20 / -133.95 / -110.42 |

ทั้งสามเวอร์ชันย่อขาดทุนบนหน้าต่าง 1 สัปดาห์นี้ — **นี่ไม่ใช่หลักฐานว่า hypothesis เต็ม
รูปแบบไม่มี edge** ด้วยเหตุผลข้างต้น (sample เล็ก, implementation ตัดทอน, threshold ยัง
ไม่ calibrate) เป็นเพียงผลของเวอร์ชัน pilot บนช่วงเวลาสั้นช่วงเดียวเท่านั้น

## สิ่งที่ต้องทำต่อก่อนจะเรียกว่า Discovery ได้จริง

1. **ข้อมูลยาวขึ้นมาก** (อย่างน้อย 12-24 เดือน) — ผู้ใช้มีไฟล์ zip ข้อมูล ม.ค. 2026 ใน
   Google Drive อยู่แล้ว (`XAUUSD-VIP_202601020100_202601302356.zip`, ~35MB) แต่ใหญ่
   เกินกว่าจะดึงผ่าน Google Drive MCP connector ในเซสชันนี้ได้ตรงๆ (จะกินบริบท
   สนทนาเกือบทั้งหมด) — ทางที่ทำได้ต่อคือให้ผู้ใช้ตัดไฟล์เป็นช่วงเล็กลง (เช่น export
   ทีละเดือนในรูปแบบ M1/M5 OHLC เหมือนไฟล์สัปดาห์นี้ ไม่ใช่ tick) หรือหาวิธี transfer
   อื่นที่ไม่ผ่าน context ของ session นี้โดยตรง
2. **ยืนยัน GMT offset จริง** ด้วย `BrokerProbe.mq5` บนบัญชีเดียวกับที่ export ข้อมูล
3. **Calibrate threshold จาก empirical distribution จริง** (percentile ของ G1/F3) แทน
   ค่าคงที่ชั่วคราวที่ pilot นี้ใช้
4. **Implement swing/liquidity-pool tracking เต็มรูปแบบ** สำหรับ A1 แทน fixed
   R-multiple TP
5. เมื่อครบทั้งหมดข้างต้น จึงเริ่มขั้น Statistical Discovery จริงตามข้อ 5 ของ MASTER
   COMMAND (แบ่ง 60/20/20, วัด expectancy แยกตาม session/regime ฯลฯ)

อัปเดตสถานะใน `research/EDGE_DATABASE.md` แล้ว (ดูคอลัมน์ Decision = `PILOT ONLY —
NOT DISCOVERY` สำหรับ A1/G1/F3)
