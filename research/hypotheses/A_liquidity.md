# หมวด A — Liquidity (4 hypotheses)

ทุกข้อในหมวดนี้แยกจาก Forbidden Logic ข้อ 1-2: entry มีเหตุผลทิศทางชัดเจนจากพฤติกรรม
สภาพคล่อง ไม่ใช่การคร่อมราคารอ breakout แบบไม่รู้ทิศทาง

---

## A1 — Liquidity Sweep Reversal (Stop Run Fade)

- **Market Mechanism**: ราคาที่ทะลุ swing high/low ก่อนหน้าเล็กน้อยมักเป็นการ "กวาด stop"
  ของนักเทรดรายย่อยที่วาง SL/entry ไว้เหนือ/ใต้จุดนั้น ไม่ใช่การเริ่มเทรนด์จริง — เมื่อ
  สภาพคล่องถูกกวาดแล้วราคามักดีดกลับเข้ากรอบ (institutional stop hunt hypothesis)
- **Hypothesis**: หลังราคาแทงทะลุ swing high/low ล่าสุด (lookback N แท่ง) ด้วยไส้เทียน
  (wick) ที่ยาวผิดปกติ แล้วปิดกลับเข้ากรอบเดิมภายใน 1-3 แท่ง มีโอกาสสูงกว่าค่าเฉลี่ยที่ราคา
  จะเคลื่อนที่สวนทางการทะลุนั้นต่อ
- **Required Data**: OHLC M1/M5 ต่อเนื่อง (ไม่ใช่แค่หน้าต่างที่ EA เดิมเทรด), ควรมี tick
  volume ประกอบถ้ามี
- **Features**: swing high/low (fractal N=5), ระยะทะลุเกิน swing (points), ความยาวไส้เทียน
  เทียบตัว body, เวลาปิดกลับเข้ากรอบ (bars-to-reclaim)
- **Entry Condition**: แท่งปิดกลับเข้ากรอบ (reclaim) หลัง sweep → เข้าฝั่งสวนทางการ sweep
- **Exit Condition**: ถึง target ที่จุดสภาพคล่องถัดไป (swing ก่อนหน้า) หรือ time-stop N แท่ง
- **SL Concept**: เหนือ/ใต้จุดสุดของไส้ที่ sweep (จุดที่ hypothesis ผิด)
- **TP Concept**: swing/liquidity pool ฝั่งตรงข้ามที่ใกล้ที่สุด
- **Timeframe**: M1 entry, M5 บริบท swing
- **Session**: ทุก session ที่มีสภาพคล่องเพียงพอ (ทดสอบแยกราย session ในขั้น Discovery)
- **Expected Edge**: ราคาที่ sweep แล้วดีดกลับมีสัดส่วนมากกว่า sweep แล้ววิ่งต่อในตลาดที่มี
  โครงสร้าง range-bound
- **Failure Condition**: ถ้า reclaim rate ไม่ต่างจาก 50/50 อย่างมีนัยสำคัญ หรือ R-multiple
  เฉลี่ยติดลบหลังต้นทุน → REJECT
- **Test Method**: นับ event sweep+reclaim ทั้งชุดข้อมูล วัด win rate/expectancy แยกตาม
  session, ขนาดการ sweep, และ regime (trend vs range จาก ADX หรือ ATR ratio ภายนอก)

---

## A2 — Stop Run Continuation (แยกจาก A1 ด้วยเงื่อนไข breakaway)

- **Market Mechanism**: ตรงข้ามกับ A1 — เมื่อการ sweep เกิดพร้อม displacement (แท่ง body
  ใหญ่ ไม่ใช่แค่ไส้) และปิดนอกกรอบ แสดงว่าสภาพคล่องที่ถูกกวาดเป็นเชื้อเพลิงให้เทรนด์ต่อจริง
  ไม่ใช่แค่ noise
- **Hypothesis**: sweep ที่มาพร้อมแท่ง displacement (body ≥ x เท่าของ ATR เฉลี่ย) และไม่ปิด
  กลับเข้ากรอบภายใน 1 แท่ง มีโอกาสไปต่อทิศทางเดิมสูงกว่าค่าเฉลี่ย
- **Required Data**: OHLC M1/M5 + ATR ภายนอก (ไม่ใช่ ATR-gate ของ EA เดิม)
- **Features**: swing level, body/ATR ratio ของแท่งที่ sweep, close-position-in-range
- **Entry Condition**: แท่ง displacement ปิดนอกกรอบ swing → เข้าตามทิศทาง breakout
- **Exit Condition**: trailing ตาม structure ใหม่ (swing low/high ที่เกิดขึ้นหลัง breakout)
  หรือ momentum หมด (แท่งย้อนกลับ body ใหญ่)
- **SL Concept**: กลับเข้าไปในกรอบเดิมเกิน 50% ของระยะ sweep
- **TP Concept**: ตาม R-multiple คงที่ระหว่าง Discovery (เช่น 1.5R/2R) แล้วปรับตามผลจริง
- **Timeframe**: M5 หลัก
- **Session**: London/NY open ที่คาดว่ามี displacement บ่อยกว่า
- **Expected Edge**: แยกแยะ sweep ปลอม (A1) กับ sweep จริง (A2) ด้วยลักษณะแท่ง — ถ้าทำได้
  จริงควรมี expectancy ตรงข้ามกันชัดเจนระหว่างสอง subset
- **Failure Condition**: ถ้า body/ATR threshold ไม่แยก A1/A2 ออกจากกันอย่างมีนัยสำคัญ → REJECT
- **Test Method**: เปรียบเทียบ expectancy ของ A1 vs A2 บน sweep event เดียวกัน แบ่งด้วย
  threshold ของ displacement — ต้องเห็นความต่างชัดเจนจึงจะถือว่าทั้งคู่มี information value

---

## A3 — Equal Highs/Lows Liquidity Reclaim

- **Market Mechanism**: ระดับราคาที่ถูกแตะซ้ำ 2+ ครั้ง (equal highs/lows) สะสม stop/entry
  ของนักเทรดจำนวนมาก ณ ระดับเดียวกัน — เมื่อระดับนี้ถูกกวาดในที่สุด มักเป็นจุดเปลี่ยนที่
  ชัดเจนกว่า swing เดี่ยวทั่วไป เพราะเป็น pool สภาพคล่องที่ใหญ่กว่า
- **Hypothesis**: หลัง equal-high/low (แตะ ≥2 ครั้งในกรอบ tolerance เล็ก) ถูกกวาดครั้งแรก
  แล้วดีดกลับ มี edge สูงกว่า single-swing sweep (A1) เพราะสภาพคล่องสะสมมากกว่า
- **Required Data**: OHLC M1/M5 ย้อนหลังพอสร้าง equal-level detection (lookback 20-50 แท่ง)
- **Features**: จำนวนครั้งที่แตะระดับ, tolerance ระหว่างจุดแตะ, ระยะเวลาที่ระดับคงอยู่
- **Entry Condition**: sweep ระดับ equal-level แล้ว reclaim ภายใน N แท่ง → เข้าสวนทาง
- **Exit Condition**: ถึง opposite liquidity pool หรือ time-stop
- **SL Concept**: เหนือ/ใต้จุดสุดของ sweep
- **TP Concept**: equal-level ฝั่งตรงข้ามที่ใกล้ที่สุด หรือ mid-range
- **Timeframe**: M5-M15 สำหรับ detect equal levels, M1 สำหรับ entry timing
- **Session**: ทุก session — ทดสอบว่า session ใดมี equal-level sweep ที่ reclaim rate สูงสุด
- **Expected Edge**: reclaim rate หลัง equal-level sweep สูงกว่า single-swing sweep เนื่อง
  จากสภาพคล่องสะสมมากกว่า (ทดสอบเทียบกับ A1 โดยตรง)
- **Failure Condition**: ถ้าไม่ต่างจาก A1 อย่างมีนัยสำคัญ ให้ REJECT เป็น hypothesis แยก
  (แต่ยังอาจเก็บเป็น feature เสริมของ A1)
- **Test Method**: จับคู่เทียบ expectancy/win-rate ของ equal-level sweep vs single-swing
  sweep บนช่วงข้อมูลเดียวกัน

---

## A4 — Previous Session High/Low Sweep-and-Fail

- **Market Mechanism**: High/Low ของ session ก่อนหน้า (เช่น Asian range) เป็นระดับอ้างอิงที่
  นักเทรดสถาบันใช้ตัดสินใจ — การกวาดระดับนี้ตอนเปิด session ถัดไปแล้วล้มเหลวที่จะยืนราคา
  นอกระดับ มักเป็นสัญญาณว่า session ใหม่จะเทรดสวนทางการกวาด
- **Hypothesis**: ถ้าราคาในชั่วโมงแรกของ London/NY session กวาด high/low ของ session ก่อน
  หน้าแล้วไม่สามารถปิดแท่ง M15 นอกระดับได้ 2 แท่งติด → มีโอกาสสูงที่จะเทรดกลับเข้าสู่ range
  เดิมของ session ก่อนหน้า
- **Required Data**: OHLC M1/M15 ครอบคลุมรอย session ต่อเนื่อง (Asian→London→NY) หลายเดือน
- **Features**: previous-session high/low, จำนวนแท่งที่ปิดนอกระดับหลัง sweep, ระยะทะลุ
- **Entry Condition**: sweep + fail-to-close-outside 2 แท่ง M15 → เข้าสวนทางกลับเข้า range
- **Exit Condition**: กลับถึงกึ่งกลาง range เดิม หรือฝั่งตรงข้ามของ range
- **SL Concept**: เหนือ/ใต้จุดสูงสุด/ต่ำสุดของ sweep บวก buffer
- **TP Concept**: mid-range หรือ opposite boundary ของ session ก่อนหน้า
- **Timeframe**: M15 สำหรับ session-level, M1 สำหรับ execution
- **Session**: London open (เทียบกับ Asian range), NY open (เทียบกับ London range)
- **Expected Edge**: session transition ที่ sweep แล้ว fail สร้าง mean-reversion opportunity
  ที่วัดผลได้ชัดกว่า sweep บน intraday swing ทั่วไป เพราะระดับ session มีความหมายเชิงสถาบัน
- **Failure Condition**: ถ้า fail-to-close ไม่ทำนายทิศทางถัดไปได้ดีกว่าสุ่ม → REJECT
- **Test Method**: สร้างตาราง session high/low ทุกวัน วัด conditional win-rate ของการเทรด
  สวนทางหลัง sweep-and-fail เทียบกับ baseline (เทรดสุ่มทิศทางในเวลาเดียวกัน)
