# XAU Control Bridge

เว็บ dashboard + ช่องควบคุมสำหรับ EA บน MT5 desktop

```
MT5 (XAU_ControlBridge.mq5)  --HTTPS POST ทุก 3 วิ (เซ็น HMAC)-->  bridge/app.py (FastAPI + SQLite)  <--  เว็บ dashboard
      ตัดสินใจเทรด + risk guard เอง         <-- config / คำสั่ง (เซ็น HMAC) --
```

## หลักการออกแบบ

| เรื่อง | ทำอย่างไร |
|---|---|
| ใครตัดสินใจเทรด | **EA เท่านั้น** เว็บส่งได้แค่ config กับคำสั่ง PAUSE / RESUME / CLOSE_ALL ไม่มีคำสั่งเปิดไม้ |
| ถ้าเว็บส่งค่าอันตราย | backend ตรวจช่วงค่าก่อนรอบหนึ่ง แล้ว EA clamp ด้วย hard limit (`InpHard*`) อีกชั้น |
| เว็บล่ม / เน็ตหลุด | ขาดการติดต่อเกิน `InpOfflineSec` EA จะเข้าโหมดปลอดภัย: ไม่เปิดไม้ใหม่ แต่ SL/TP ของไม้เดิมยังอยู่ที่โบรก |
| ปลอมคำสั่ง | request และ response เซ็นด้วย HMAC-SHA256 และมี timestamp กับ nonce กัน replay ถ้า EA ตรวจลายเซ็นไม่ผ่านจะทิ้งทั้ง response |
| ส่งคำสั่งซ้ำ | คำสั่งทุกตัวให้ผลเหมือนเดิมถ้าทำซ้ำ EA จำ id ล่าสุด 32 ตัว คำสั่งหมดอายุใน 10 นาทีถ้า EA ไม่มารับ |
| Deal หาย / ซ้ำ | EA เลื่อน cursor หลังได้ HTTP 200 เท่านั้น และ server ใช้ `INSERT OR IGNORE` ตาม ticket |
| Restart MT5 | สถานะ risk (day start equity, peak, halt, pause, cursor) เก็บใน GlobalVariables |
| $30 เปิด 0.01 แล้วเสี่ยงเกิน | `RiskLot()` ถ้า lot ที่คำนวณจาก risk% ต่ำกว่า lot ขั้นต่ำ จะ**ไม่เปิดไม้** ไม่ปัดขึ้น |
| เปิดไม้ซ้ำใน 1 วินาที | `min_entry_gap_sec` บวก `max_positions` |

`StrategySignal()` ใน EA ยังเป็น stub คืนค่า 0 เสมอ ตั้งใจไว้แบบนี้จนกว่า baseline และ OOS ของกลยุทธ์จะผ่านตาม CLAUDE.md

## รันแบบ local

```bash
pip install -r bridge/requirements.txt
export BRIDGE_ADMIN_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(24))')"
export BRIDGE_SECRETS="<เลขบัญชี MT5>:$(python -c 'import secrets;print(secrets.token_hex(32))')"
uvicorn bridge.app:app --host 127.0.0.1 --port 8765
# เปิด http://127.0.0.1:8765/ แล้วใส่ BRIDGE_ADMIN_TOKEN
```

หลายบัญชีใส่คั่นด้วย comma: `BRIDGE_SECRETS="111:secretA,222:secretB"`

ทดสอบโดยไม่ต้องมี MT5 ด้วยตัวจำลอง EA:

```bash
python -m bridge.ea_sim --account <เลขบัญชี> --secret <secret> --rounds 30
python -m pytest bridge/tests -q
```

## ติดตั้ง EA

1. คัดลอก `MQL5/Experts/XAU_ControlBridge.mq5` ไปไว้ในโฟลเดอร์ `MQL5/Experts` แล้ว compile ต้องได้ 0 error(s)
2. MT5 > Tools > Options > Expert Advisors > ติ๊ก **Allow WebRequest for listed URL** แล้วเพิ่ม `http://127.0.0.1:8765`
   (ถ้า backend อยู่บน VPS ให้ใช้ `https://โดเมนของคุณ`)
3. ลาก EA ใส่กราฟ XAUUSD แล้วใส่ `InpSecret` ให้ตรงกับ secret ของบัญชีนั้นใน `BRIDGE_SECRETS`
4. ดู tab Experts ถ้า self-test HMAC ไม่ผ่าน EA จะไม่เริ่มทำงาน และบนกราฟต้องขึ้น `Bridge: online`
5. **ทดสอบบนบัญชีเดโมก่อน** อย่างน้อย 2 สัปดาห์

## ขึ้น VPS / cloud

- ต้องใช้ HTTPS (เช่น Caddy หรือ nginx + Let's Encrypt ด้านหน้า uvicorn) ถ้าใช้ http ธรรมดา ลายเซ็นยังกันการปลอมคำสั่งได้ แต่ข้อมูลบัญชีจะวิ่งแบบไม่เข้ารหัส
- ห้ามเปิด dashboard ออกอินเทอร์เน็ตถ้า admin token ยังอ่อน
- นาฬิกาเครื่อง MT5 กับ server ต้องต่างกันไม่เกิน 120 วินาที (เปิด NTP ไว้)

## Protocol

ดู docstring ใน `bridge/protocol.py`

| Endpoint | ใคร | ทำอะไร |
|---|---|---|
| `POST /v1/ea/sync` | EA | ส่ง state/positions/deals/acks แล้วรับ CFG กับ CMD |
| `GET /v1/accounts` | admin | รายชื่อบัญชีพร้อมสถานะ online |
| `GET /v1/accounts/{acc}/state` | admin | state ล่าสุด |
| `GET /v1/accounts/{acc}/deals` | admin | deal history |
| `GET /v1/accounts/{acc}/stats` | admin | PF, win rate, expectancy, avg win/loss |
| `POST /v1/accounts/{acc}/commands` | admin | `{"type": "PAUSE" \| "RESUME" \| "CLOSE_ALL"}` |
| `GET/PUT /v1/accounts/{acc}/config` | admin | ดูหรือตั้ง config (สร้างเวอร์ชันใหม่ทุกครั้งที่บันทึก) |

`CLOSE_ALL` จะ Pause ให้ด้วยเสมอ กันไม่ให้ EA เปิดไม้ใหม่ทันทีหลังปิด ต้องกด Resume เอง
`RESUME` จะล้าง halt และตั้ง peak equity ใหม่ที่ค่าปัจจุบัน แต่ถ้าวันนี้ยังขาดทุนเกินเกณฑ์ daily loss จะ halt ซ้ำทันที

## ยังไม่ได้ทำ / ข้อจำกัด

- **ยังไม่ได้ compile EA บน MetaEditor จริง** (เครื่องที่เขียนไม่มี MT5) ต้อง compile แล้วส่ง log มาตรวจ
- ยังไม่มีระบบ login หลายผู้ใช้ มี admin token เดียว
- `config_version` ของ deal คือเวอร์ชันตอน EA ส่งข้อมูล ไม่ใช่ตอนเปิดไม้ (ปกติต่างกันไม่กี่วินาที)
- ยังไม่มีกราฟ equity และยังไม่มี LLM filter (ขั้นถัดไป)
