# หมวด G — Momentum (4 hypotheses)

---

## G1 — Momentum Burst Continuation (Return-based, ไม่ใช่ straddle)

- **Market Mechanism**: การเคลื่อนไหวที่เร็วผิดปกติในช่วงเวลาสั้น (burst) มักสะท้อนการเข้ามา
  ของ informed order flow ขนาดใหญ่ในครั้งเดียว — ต่างจาก EA เดิมที่คร่อมราคารอไม่รู้ทิศทาง
  hypothesis นี้ **รอให้เกิด burst ก่อนแล้วค่อยเข้าตามทิศทางที่เกิดขึ้นจริง** (reactive ไม่ใช่
  proactive-both-sides)
- **Hypothesis**: เมื่อ return ของ N แท่งล่าสุด (เช่น 3 แท่ง M1) เกิน threshold ที่หายาก
  (95th percentile ของ rolling N-bar return distribution) และปิดแท่งด้วย body ใหญ่ (ไม่ใช่
  ไส้ยาว) มีโอกาส continuation ระยะสั้นสูงกว่าค่าเฉลี่ย
- **Required Data**: M1 OHLC ต่อเนื่อง เพื่อสร้าง rolling return distribution
- **Features**: N-bar return, percentile เทียบ rolling window, body/wick ratio ของแท่งสุดท้าย
- **Entry Condition**: burst เกิน threshold + body ใหญ่ → เข้าทิศทางเดียวกันทันที (ไม่รอ
  pullback)
- **Exit Condition**: time-stop สั้น (เช่น 5-10 แท่ง) หรือ momentum หมด (แท่งกลับทิศทาง
  ขนาดใหญ่)
- **SL Concept**: ใต้/เหนือจุดเริ่มของ burst
- **TP Concept**: R-multiple เล็ก (momentum trade เป็น scalping ระยะสั้น)
- **Timeframe**: M1
- **Session**: London/NY (burst แท้จากสถาบันคาดว่าเกิดถี่กว่าใน session สภาพคล่องสูง)
- **Expected Edge**: continuation หลัง genuine burst (body ใหญ่) สูงกว่า burst ปลอม (ไส้ยาว,
  ดูหมวด A1) — เป็นการยืนยันข้ามหมวด (cross-validate กับ A2)
- **Failure Condition**: ถ้า cost (สเปรด+สลิปเพจ) กิน edge ทั้งหมดเพราะ target เล็กเกินไป →
  REJECT ในรูปแบบ M1 scalping นี้ (อาจพิจารณาขยับไป M5)
- **Test Method**: วัด forward return N แท่งถัดไปหลัง burst เทียบ non-burst baseline,
  ทดสอบหลังหักต้นทุนจริง (spread+commission+slippage จากข้อมูลจริง) ว่ายัง positive หรือไม่

---

## G2 — Breakout-and-Retest Entry (ลด false-breakout เทียบ breakout ตรงๆ)

- **Market Mechanism**: การ breakout ระดับสำคัญ (swing high/low, opening-range) แล้วราคา
  ย้อนกลับมาทดสอบระดับนั้นอีกครั้งก่อนไปต่อ (retest) เป็นพฤติกรรมที่ยืนยันว่าระดับเดิม
  เปลี่ยนบทบาทจากแนวต้านเป็นแนวรับ (หรือกลับกัน) จริง — ลดความเสี่ยง false-breakout เทียบกับ
  การไล่ราคา (chase) ทันทีที่ breakout
- **Hypothesis**: breakout ที่มี retest กลับมาแตะระดับเดิม (ภายใน tolerance เล็ก) แล้วปิด
  แท่งยืนยันทิศทางเดิม มี win-rate สูงกว่า breakout ที่เข้าทันทีไม่รอ retest
- **Required Data**: M5 OHLC ต่อเนื่อง + swing-level detection
- **Features**: ระดับที่ breakout, ระยะเวลาก่อน retest, ความแม่นยำของ retest (ห่างจากระดับ
  เดิมเท่าไร)
- **Entry Condition**: breakout ยืนยัน + ราคากลับมาแตะระดับเดิม + แท่งปฏิเสธยืนยันทิศทางเดิม
  → เข้าตาม
- **Exit Condition**: measured move จาก breakout หรือ CHOCH invalidate
- **SL Concept**: กลับเข้าไปฝั่งตรงข้ามของระดับ breakout เกิน buffer
- **TP Concept**: extension ตาม range ที่ breakout มา
- **Timeframe**: M5
- **Session**: London/NY
- **Expected Edge**: win-rate ของ breakout+retest ควรสูงกว่า breakout-ทันที (baseline) —
  ต้องเทียบโดยตรงบนชุด breakout event เดียวกัน (บาง event ไม่มี retest เกิดขึ้น ต้องนับเป็น
  โอกาสที่เสียไปด้วย ไม่ใช่ตัดทิ้ง)
- **Failure Condition**: ถ้า breakout ที่ไม่มี retest ทำกำไรดีกว่าเฉลี่ยรวม (แปลว่ารอ retest
  เสียโอกาสมากกว่าที่ได้) → REJECT
- **Test Method**: เปรียบเทียบ expectancy ของ 3 กลุ่ม: (1) เข้าทันทีทุก breakout (2) เข้าเฉพาะ
  breakout ที่มี retest (3) ไม่เข้าเลยถ้าไม่มี retest ภายใน N แท่ง — วัด expectancy รวมของ
  แต่ละ policy

---

## G3 — Continuation After Shallow Pullback in Established Trend

- **Market Mechanism**: ในเทรนด์ที่ยืนยันแล้ว (BOS ต่อเนื่อง) การ pullback ตื้น (ไม่ทะลุ
  swing ก่อนหน้า) มักเป็นจังหวะที่ผู้เล่นที่พลาดขบวนแรกเข้ามาเพิ่ม position — คล้าย B1 แต่
  ต่างตรงที่ G3 ไม่ต้องรอ BOS ใหม่ยืนยัน แค่ pullback ตื้นในเทรนด์เดิมก็เพียงพอ (higher
  frequency, lower confirmation)
- **Hypothesis**: pullback ที่ไม่เกิน 38% ของ leg ล่าสุด (Fibonacci retracement แบบ
  empirical ทดสอบจริง ไม่ใช้เป็น magic number ตายตัว) ในเทรนด์ที่มี BOS ยืนยันแล้ว มี edge
  continuation แม้ไม่มี BOS ใหม่ยืนยันซ้ำ
- **Required Data**: M5 OHLC + BOS state (จากหมวด B)
- **Features**: % retracement ของ pullback, จำนวน BOS ก่อนหน้าทิศทางเดียวกัน
- **Entry Condition**: เทรนด์ยืนยัน + pullback ≤38% + แท่งกลับทิศทางเทรนด์ → เข้าทันที (ไม่รอ
  BOS ใหม่)
- **Exit Condition**: time-stop หรือ trailing ตาม structure
- **SL Concept**: เลย 61.8% retracement
- **TP Concept**: extension ของ leg เดิม
- **Timeframe**: M5
- **Session**: London/NY
- **Expected Edge**: ความถี่ของสัญญาณสูงกว่า B1 (ไม่ต้องรอ BOS ใหม่) — ทดสอบว่า expectancy
  ต่อไม้ลดลงเท่าไรเทียบกับ B1 และ frequency ที่เพิ่มขึ้นคุ้มหรือไม่ในภาพรวม (expectancy ×
  frequency)
- **Failure Condition**: ถ้า win-rate ต่ำกว่า B1 มากจนภาพรวม (Net Expectancy) แย่กว่า →
  REJECT ให้ใช้ B1 แทน
- **Test Method**: รัน G3 และ B1 บนชุดเทรนด์เดียวกัน เทียบ trade count, win-rate, expectancy
  ต่อไม้ และ total expectancy ของทั้งสองแบบ

---

## G4 — Tick-Volume Burst Confirmation (momentum ยืนยันด้วยปริมาณ)

- **Market Mechanism**: MT5 ให้ tick-volume (จำนวน tick ต่อแท่ง) เป็น proxy ของกิจกรรมตลาด —
  การเคลื่อนไหวราคาที่มาพร้อม tick-volume สูงผิดปกติ (เทียบ rolling average) มีความน่าเชื่อถือ
  มากกว่าการเคลื่อนไหวขนาดเท่ากันที่ volume ต่ำ (อาจเป็นแค่ราคากระโดดจาก liquidity บาง)
- **Hypothesis**: burst ราคาตามหมวด G1 ที่เกิดพร้อม tick-volume เกิน 2× rolling average(20)
  มี win-rate/expectancy สูงกว่า burst ที่ volume ปกติ/ต่ำ
- **Required Data**: M1 OHLC + tick-volume ต่อเนื่อง
- **Features**: tick-volume ของแท่ง burst, rolling average tick-volume (20 แท่ง)
- **Entry Condition**: เข้าเงื่อนไข G1 (burst + body ใหญ่) และ tick-volume ≥2× average →
  เข้า (ถ้า volume ต่ำกว่า ไม่เข้า — เป็น filter เพิ่มจาก G1)
- **Exit Condition**: เดียวกับ G1
- **SL Concept**: เดียวกับ G1
- **TP Concept**: เดียวกับ G1
- **Timeframe**: M1
- **Session**: London/NY
- **Expected Edge**: G4 (มี volume filter) ควรมี win-rate สูงกว่า G1 (ไม่มี filter) แม้จำนวน
  สัญญาณจะน้อยลง — เป็นการทดสอบว่า volume filter มี information value จริงหรือแค่ลด sample
  size โดยไม่ช่วยอะไร
- **Failure Condition**: ถ้า win-rate ของ G4 ไม่ต่างจาก G1 อย่างมีนัยสำคัญ → REJECT การเพิ่ม
  volume filter (ใช้ G1 เปล่าพอ ไม่ต้องเพิ่มความซับซ้อน)
- **Test Method**: แบ่งสัญญาณ G1 ทั้งหมดเป็น high-volume vs normal/low-volume แล้วเทียบ
  win-rate/expectancy สองกลุ่มบนชุด burst event เดียวกัน
