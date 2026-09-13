# หมวด B — Market Structure (4 hypotheses)

---

## B1 — Break of Structure (BOS) Continuation

- **Market Mechanism**: เมื่อโครงสร้างราคาทำ higher-high/lower-low ใหม่ต่อเนื่อง (BOS)
  ยืนยันว่าฝั่งควบคุมตลาด (buyer/seller) ยังครองอยู่ — การเข้าตามทิศทาง BOS ที่มี pullback
  ตื้นมักได้ continuation มากกว่าการเข้าตอนไม่มี structure ยืนยัน
- **Hypothesis**: หลัง BOS (ปิดแท่งทะลุ swing high/low ล่าสุดตามทิศทางเทรนด์ปัจจุบัน) แล้ว
  ราคา pullback ไม่เกิน 50% ของ leg ล่าสุด ก่อนไปต่อทิศทางเดิม มี edge เชิง continuation
- **Required Data**: OHLC M5/M15 ต่อเนื่องหลายเดือน เพื่อระบุ swing structure ได้แม่นยำ
- **Features**: swing high/low series, ทิศทาง BOS, ขนาด pullback (% ของ leg), จำนวน BOS
  ต่อเนื่องทิศทางเดียวกัน (structure strength)
- **Entry Condition**: BOS ยืนยัน + pullback ตื้น (≤50%) + แท่งกลับทิศทางเทรนด์ → เข้าตาม BOS
- **Exit Condition**: BOS ทิศทางตรงข้ามเกิดขึ้น (CHOCH) หรือถึง target R-multiple
- **SL Concept**: ใต้/เหนือจุดต่ำสุด/สูงสุดของ pullback
- **TP Concept**: swing ก่อนหน้าที่ตรงข้าม หรือ extension ตาม leg ก่อนหน้า (เช่น 1x leg length)
- **Timeframe**: M15 โครงสร้าง, M5 entry
- **Session**: London/NY (ช่วงที่ structure เคลื่อนไหวชัดกว่า Asian range-bound)
- **Expected Edge**: continuation หลัง BOS+shallow-pullback ควรมี win-rate/expectancy สูงกว่า
  การเข้าแบบสุ่มในเทรนด์เดียวกัน
- **Failure Condition**: ถ้า pullback depth ไม่มีผลต่อ win-rate อย่างมีนัยสำคัญ → REJECT
- **Test Method**: ระบุ BOS event อัตโนมัติจาก swing detection, แบ่งกลุ่มตาม pullback depth,
  วัด expectancy แต่ละกลุ่มแยกจาก regime (trending vs ranging ภายนอก)

---

## B2 — Change of Character (CHOCH) Reversal

- **Market Mechanism**: CHOCH คือจุดที่โครงสร้างเทรนด์เดิมถูกทำลายครั้งแรก (higher-low แรก
  ที่ต่ำกว่า higher-low ก่อนหน้าในอัพเทรนด์ หรือกลับกัน) — เป็นสัญญาณเปลี่ยนฝั่งควบคุมตลาด
  ก่อนที่ราคาจะยืนยันด้วย BOS ทิศทางใหม่
- **Hypothesis**: CHOCH แรกหลังเทรนด์ยาวนาน (≥N BOS ทิศทางเดียวกันต่อเนื่อง) มีโอกาสนำไปสู่
  การกลับตัวจริงมากกว่า CHOCH ที่เกิดกลางช่วง sideways ที่ไม่มีเทรนด์ชัดมาก่อน
- **Required Data**: OHLC M15 ย้อนหลังยาวพอนับ BOS/CHOCH sequence
- **Features**: จำนวน BOS ต่อเนื่องก่อน CHOCH, ระยะเวลาเทรนด์เดิม, ขนาด leg สุดท้ายก่อน CHOCH
- **Entry Condition**: ยืนยัน CHOCH (ปิดแท่งทำลาย higher-low/lower-high ล่าสุด) → เข้าทิศทางใหม่
- **Exit Condition**: BOS ทิศทางใหม่ยืนยันซ้ำ (take partial), หรือ CHOCH กลับทิศทางเดิมอีกครั้ง
  (invalidate)
- **SL Concept**: เหนือ/ใต้ extreme ของเทรนด์เดิมก่อน CHOCH
- **TP Concept**: ระยะเทียบเท่า leg เทรนด์เดิม (measured move) หรือ liquidity pool ถัดไป
- **Timeframe**: M15
- **Session**: ทุก session ที่มีเทรนด์ก่อนหน้าชัดเจน
- **Expected Edge**: CHOCH หลังเทรนด์ยาวมี follow-through สูงกว่า CHOCH ในตลาด choppy —
  ถ้าพิสูจน์ได้จะเป็น filter สำคัญ
- **Failure Condition**: ถ้า follow-through rate ไม่ต่างตามความยาวเทรนด์ก่อนหน้า → REJECT
- **Test Method**: จัดกลุ่ม CHOCH ตามความยาวเทรนด์ก่อนหน้า วัด forward return N แท่งถัดไป
  แยกกลุ่ม เทียบ statistical significance

---

## B3 — Displacement-then-Compression Cycle Entry

- **Market Mechanism**: หลังการเคลื่อนไหวแรง (displacement) ราคามักเข้าสู่ช่วงบีบตัว
  (compression/consolidation) เพื่อ "ย่อยข่าว"/สร้างสมดุลใหม่ ก่อนไปต่อทิศทางเดิมหรือกลับตัว
  — จังหวะท้ายของ compression มักให้ risk:reward ที่ดีกว่าเข้าตอน displacement เอง
- **Hypothesis**: เมื่อ compression (range แคบ ATR หดตัวต่อเนื่อง ≥N แท่ง) เกิดขึ้นหลัง
  displacement leg และราคาหลุด compression ไปทิศทางเดียวกับ displacement เดิม มี edge
  continuation ที่ดีกว่าเข้ากลาง displacement
- **Required Data**: OHLC M5 ต่อเนื่อง
- **Features**: ขนาด displacement leg, ความยาว/ความแคบของ compression, ทิศทางที่หลุดออก
- **Entry Condition**: หลุด compression ทิศทางเดียวกับ displacement ก่อนหน้า → เข้าตาม
- **Exit Condition**: measured move จาก displacement เดิม หรือ compression ใหม่เกิดขึ้นอีก
- **SL Concept**: ฝั่งตรงข้ามของ compression range
- **TP Concept**: ระยะเท่ากับ displacement leg เดิม (measured move projection)
- **Timeframe**: M5
- **Session**: ทุก session — คาดว่า London/NY มี displacement ชัดกว่า Asian
- **Expected Edge**: continuation-after-compression มี win-rate สูงกว่าการเข้าโดยไม่รอ
  compression (baseline: เข้าทันทีหลัง displacement)
- **Failure Condition**: ถ้าไม่ต่างจาก baseline อย่างมีนัยสำคัญ หรือ compression กินเวลานาน
  จนโอกาสเทรดต่ำเกินจะใช้งานจริง → REJECT
- **Test Method**: เปรียบเทียบ 2 กลุ่ม (เข้าหลัง compression breakout vs เข้าทันทีหลัง
  displacement) บนชุด displacement event เดียวกัน

---

## B4 — Trend Transition Confirmation (Multi-Timeframe Structure Alignment)

- **Market Mechanism**: การกลับตัวของเทรนด์ที่ "ยืนอยู่" มักต้องการ alignment ระหว่าง
  timeframe ใหญ่ (H1 บริบท) กับ timeframe เล็ก (M5 execution) — CHOCH บน M5 อย่างเดียวมี
  false-signal สูงถ้า H1 ยังอยู่ในเทรนด์เดิมชัดเจน
- **Hypothesis**: CHOCH บน M5 ที่เกิดพร้อมกับสัญญาณอ่อนตัวของเทรนด์บน H1 (เช่น H1 ทำ
  lower-high ครั้งแรกในอัพเทรนด์) มี follow-through สูงกว่า CHOCH บน M5 ที่ H1 ยังแข็งแรง
- **Required Data**: OHLC M5 และ H1 คู่กัน ครอบคลุมช่วงเดียวกัน
- **Features**: สถานะโครงสร้าง H1 (BOS ล่าสุดทิศทางไหน), CHOCH บน M5, ระยะเวลาห่างกัน
- **Entry Condition**: CHOCH M5 + H1 แสดงสัญญาณอ่อนตัวภายใน N แท่งก่อนหน้า → เข้าทิศทางใหม่
- **Exit Condition**: H1 BOS ยืนยันทิศทางใหม่ (take profit เพิ่ม) หรือ M5 กลับไปยืนยันเทรนด์
  เดิม (invalidate)
- **SL Concept**: เหนือ/ใต้ extreme ของ CHOCH บน M5
- **TP Concept**: ตาม H1 swing ถัดไป
- **Timeframe**: H1 (context) + M5 (entry)
- **Session**: ทุก session ที่ H1 structure เปลี่ยนแปลงชัดเจน
- **Expected Edge**: multi-timeframe alignment ควรลด false-signal ของ CHOCH เดี่ยว (B2) ได้
  — ทดสอบเทียบ win-rate โดยตรงกับ B2
- **Failure Condition**: ถ้า alignment ไม่ช่วยเพิ่ม win-rate เทียบ B2 เดี่ยวๆ อย่างมีนัยสำคัญ
  → REJECT (ให้ใช้ B2 เปล่าแทน ไม่ต้องเพิ่มความซับซ้อน)
- **Test Method**: เปรียบเทียบ expectancy ของ CHOCH-only (B2) vs CHOCH+H1-alignment (B4)
  บนชุด event เดียวกัน — ต้องดีขึ้นมีนัยสำคัญจึงคุ้มความซับซ้อนที่เพิ่ม
