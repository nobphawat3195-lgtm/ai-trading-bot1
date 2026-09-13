# หมวด D — Volatility Regime (3 hypotheses)

หมายเหตุ: ATR ใช้เป็น input ประกอบได้ตาม `FORBIDDEN_LOGIC.md` แต่ทุกข้อในหมวดนี้ต้อง
**ไม่ใช่** ATR-fast(14)/slow(60) ratio ≤ threshold แบบเดียวกับ EA เดิมเป๊ะๆ — ต้องมี
สมมติฐานกลไกตลาดที่ต่างออกไปกำกับการใช้ ATR

---

## D1 — Volatility Regime Expansion Breakout (Daily ATR percentile)

- **Market Mechanism**: วันที่ realized volatility (daily range) อยู่ใน percentile ต่ำเทียบ
  กับ N วันย้อนหลัง มักตามมาด้วยวันที่ volatility ขยายตัว (volatility clustering / mean
  reversion ของ volatility เอง ไม่ใช่ของราคา) — เป็นปรากฏการณ์สถิติที่รู้จักกันดีใน volatility
  time series
- **Hypothesis**: หลังจาก daily ATR percentile ต่ำกว่า 20th percentile (เทียบ 60 วันย้อนหลัง)
  ติดต่อกัน ≥3 วัน วันถัดไปมีโอกาสเกิด directional breakout ที่ให้ผลตอบแทนดีกว่าเฉลี่ย
- **Required Data**: Daily OHLC ย้อนหลังอย่างน้อย 2-3 ปี เพื่อคำนวณ percentile ให้เสถียร
- **Features**: daily ATR(14), percentile rank เทียบ 60 วัน, จำนวนวันติดต่อกันที่ต่ำกว่า
  threshold
- **Entry Condition**: วันถัดจาก low-volatility streak → เข้าตามทิศทางที่ราคาทะลุ high/low
  ของ streak นั้น (breakout จากกรอบบีบตัวหลายวัน)
- **Exit Condition**: ATR percentile กลับมาสูงกว่า median (regime คลายตัวแล้ว) หรือ time-stop
- **SL Concept**: กลับเข้ากรอบ low-volatility streak เกิน 50%
- **TP Concept**: ตาม R-multiple ที่ปรับด้วย ATR ปัจจุบัน (ATR-based target)
- **Timeframe**: Daily สำหรับ regime, M15-M30 สำหรับ execution
- **Session**: ทดสอบว่า breakout มักเกิดใน session ไหนของวันที่เข้าเงื่อนไข
- **Expected Edge**: return หลัง low-vol streak ควรมี magnitude สูงกว่า unconditional
  distribution อย่างมีนัยสำคัญ (volatility clustering เป็นปรากฏการณ์ที่มีวรรณกรรมรองรับ)
- **Failure Condition**: ถ้า directional bias ไม่ชัด (breakout สุ่มทิศทาง 50/50 และ magnitude
  ไม่ต่างจาก baseline) → REJECT การเทรดทิศทาง แต่เก็บไว้เป็น regime filter ของ hypothesis อื่น
- **Test Method**: แบ่งวันเป็น 2 กลุ่ม (หลัง low-vol streak vs ไม่ใช่) วัด forward
  return magnitude และ variance แต่ละกลุ่ม เทียบด้วย statistical test (เช่น t-test บน
  |return|)

---

## D2 — Intraday Range Compression → Session Breakout (แยกจาก D1 ด้วย timeframe)

- **Market Mechanism**: เหมือน D1 แต่ทำงานระดับ intraday — ช่วง Asian session ที่ range แคบ
  ผิดปกติ (เทียบ Asian range เฉลี่ย N วัน) มักตามมาด้วยการขยายตัวชัดเจนตอน London open เพราะ
  สภาพคล่องสถาบันกลับเข้าตลาด
- **Hypothesis**: ถ้า Asian session range (high-low ของช่วง Asian) ต่ำกว่า 25th percentile
  เทียบ 20 วันย้อนหลัง breakout ที่ London open มีโอกาสไปต่อ (ไม่ใช่ false breakout) สูงกว่า
  วันที่ Asian range ปกติ/กว้าง
- **Required Data**: M15 OHLC ต่อเนื่อง เพื่อคำนวณ Asian-session range รายวัน
- **Features**: Asian range (points), percentile เทียบ 20 วัน, ทิศทาง breakout ที่ London open
- **Entry Condition**: Asian range แคบผิดปกติ + London open ทะลุ Asian high/low →
  เข้าตามทิศทางทะลุ
- **Exit Condition**: London session จบ (time-stop) หรือ momentum หมด (แท่งกลับทิศทาง
  ขนาดใหญ่)
- **SL Concept**: กลับเข้า Asian range
- **TP Concept**: R-multiple คงที่ระหว่าง Discovery หรือ ATR-based
- **Timeframe**: M15 สำหรับ regime, M5 สำหรับ execution
- **Session**: London open โดยเฉพาะ (ชั่วโมงแรก)
- **Expected Edge**: false-breakout rate ที่ London open ควรต่ำกว่าเมื่อ Asian range แคบ
  ผิดปกติ เทียบกับ Asian range ปกติ
- **Failure Condition**: ถ้า false-breakout rate ไม่ต่างกันระหว่างสอง regime → REJECT
- **Test Method**: แบ่งวันตาม Asian-range percentile, วัด success-rate ของ breakout ที่
  London open แยกแต่ละกลุ่ม เปรียบเทียบทางสถิติ

---

## D3 — Range Expansion Day Continuation (Opening Range Breakout variant)

- **Market Mechanism**: วันที่เปิดตลาด (เช่น London open) ด้วย range ของชั่วโมงแรกที่กว้าง
  ผิดปกติ (initiative move จากสถาบัน) มักมีแนวโน้ม "trend day" ที่ราคาวิ่งทิศทางเดียวต่อ
  ตลอดวัน มากกว่าวันที่เปิดด้วย range แคบ (ต่างจาก D2 ที่ดูก่อนเปิด D3 ดูหลังเปิดแล้ว)
- **Hypothesis**: ถ้า opening-range (ชั่วโมงแรกของ London) กว้างเกิน 1.5×ATR เฉลี่ยของ
  opening-range ย้อนหลัง 20 วัน การ breakout จาก opening-range นั้นมีโอกาส continuation
  ตลอดช่วงที่เหลือของ London/NY session สูงกว่าค่าเฉลี่ย
- **Required Data**: M5/M15 OHLC ต่อเนื่อง
- **Features**: opening-range size (points), percentile เทียบ 20 วัน, ทิศทาง breakout
- **Entry Condition**: opening-range กว้างผิดปกติ + ราคาทะลุขอบ opening-range → เข้าตาม
- **Exit Condition**: จบ NY session (time-stop) หรือ trailing ตาม structure (BOS ใหม่หยุด)
- **SL Concept**: กลับเข้า opening-range
- **TP Concept**: measured move เท่ากับความกว้าง opening-range (classic ORB projection)
- **Timeframe**: M5-M15
- **Session**: London open ถึง NY close
- **Expected Edge**: "trend day" ที่เริ่มด้วย wide opening-range ควร outperform วันที่เริ่ม
  ด้วย opening-range แคบ ในแง่ follow-through ตลอดวัน
- **Failure Condition**: ถ้า wide-opening-range day ไม่ต่างจาก narrow-opening-range day ใน
  แง่ follow-through → REJECT
- **Test Method**: แบ่งวันตาม opening-range percentile วัด % ของวันที่เป็น "trend day"
  (ปิดใกล้ extreme ของวัน) ในแต่ละกลุ่ม เทียบสถิติ
