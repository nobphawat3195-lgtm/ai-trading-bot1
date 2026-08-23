# หมวด F — Mean Reversion (4 hypotheses)

---

## F1 — Extreme Deviation from Session VWAP Reversion

- **Market Mechanism**: VWAP (volume-weighted average price ของ session ปัจจุบัน) คือระดับ
  ราคาเฉลี่ยที่นักเทรดสถาบันจำนวนมากใช้อ้างอิงต้นทุน — การเบี่ยงเบนไกลจาก VWAP ผิดปกติ
  (เกิน N standard deviation ของ intraday distribution) มักถูกดึงกลับเพราะสถาบันที่ยังไม่ได้
  execute เต็มจำนวนจะเข้าซื้อ/ขายเพื่อ "เฉลี่ยต้นทุน" กลับเข้าใกล้ VWAP
- **Hypothesis**: เมื่อราคาห่างจาก session-VWAP เกิน 2 standard deviation (คำนวณจาก
  intraday price distribution ของ session นั้น) มีโอกาสย้อนกลับเข้าใกล้ VWAP มากกว่าวิ่งต่อ
- **Required Data**: M1 OHLC + tick volume (หรือ MT5 tick-volume proxy) เพื่อคำนวณ VWAP
  รายวัน/ราย session
- **Features**: ระยะห่างจาก VWAP (หน่วย SD), เวลาที่ใช้ไปของ session (VWAP ยิ่งช้ายิ่งเสถียร)
- **Entry Condition**: ราคาห่าง VWAP เกิน 2SD + แท่งกลับทิศทางเข้าหา VWAP → เข้าทิศทาง
  reversion
- **Exit Condition**: ราคากลับถึง VWAP หรือ time-stop
- **SL Concept**: ไกลจาก VWAP กว่าเดิม (เกิน 3SD)
- **TP Concept**: VWAP หรือ 1SD
- **Timeframe**: M1/M5 execution, คำนวณ VWAP สะสมทั้ง session
- **Session**: ทุก session — ทดสอบว่า session ไหนมี reversion rate สูงสุด (คาด London/NY ที่
  volume มากกว่าจะ VWAP เสถียรกว่า Asian)
- **Expected Edge**: reversion-rate จาก extreme deviation ควรสูงกว่า 50% อย่างมีนัยสำคัญใน
  ตลาดที่ไม่มี trend day รุนแรง
- **Failure Condition**: ถ้าเข้าเงื่อนไขนี้บ่อยในวัน trend-day (D3) แล้ว reversion ไม่เกิด
  (ราคาวิ่งต่อ) → ต้องแยก regime (ตัด trend-day ออกจากการเทรด mean-reversion) มิฉะนั้น REJECT
- **Test Method**: วัด forward-return หลังแตะ 2SD แยกตาม regime (trend day vs range day จาก
  D1/D3), ทดสอบว่า reversion มีนัยสำคัญเฉพาะใน range day หรือไม่

---

## F2 — Asian Session Range Reversion (Fade the Edges)

- **Market Mechanism**: Asian session มักมีสภาพคล่องต่ำและเทรดในกรอบแคบเนื่องจากไม่มีตลาด
  หลักเปิดทำการ (accumulation phase) — การแตะขอบบนหรือล่างของ range ที่ก่อตัวขึ้นในช่วง Asian
  มักถูก fade กลับเข้ากรอบเพราะไม่มี informed flow มากพอจะดันราคาทะลุกรอบจริงในช่วงนี้
- **Hypothesis**: ในช่วง Asian session (ก่อน London open) การแตะขอบบน/ล่างของ range ที่
  ก่อตัวมาแล้วอย่างน้อย 2 ชม. มีโอกาส fade กลับเข้ากรอบสูงกว่า breakout ต่อ (ต่างจาก E4 ที่
  ดู breakout ตอน London เปิด — F2 ดูพฤติกรรม *ภายใน* Asian session เอง)
- **Required Data**: M5 OHLC ต่อเนื่องช่วง Asian
- **Features**: ความกว้าง range ณ เวลาที่ทดสอบ, จำนวนครั้งที่แตะขอบก่อนหน้า
- **Entry Condition**: แตะขอบบน/ล่างของ Asian range ที่ก่อตัว ≥2 ชม. + แท่งปฏิเสธ → เข้าทิศทาง
  fade กลับกรอบ
- **Exit Condition**: กึ่งกลาง range หรือขอบตรงข้าม หรือหมดเวลา Asian session (ก่อน London
  open ต้องปิดหรือลดขนาด position)
- **SL Concept**: เลยขอบ range ที่ทดสอบ
- **TP Concept**: กึ่งกลาง range
- **Timeframe**: M5
- **Session**: Asian เท่านั้น (00:00-07:00 UTC โดยประมาณ)
- **Expected Edge**: fade-rate ภายใน Asian session ควรสูงกว่า breakout-rate เนื่องจากสภาพ
  คล่องต่ำ
- **Failure Condition**: ถ้าวันที่มีข่าวสำคัญช่วง Asian (เช่น China/Japan data) ทำให้
  breakout เกิดบ่อยผิดปกติจนกลบ edge → ต้องมี news filter มิฉะนั้น REJECT ภาพรวม
- **Test Method**: วัด fade-rate เทียบ breakout-rate ของทุกครั้งที่แตะขอบ Asian range,
  แยกวันที่มี high-impact news ออกจากกัน เทียบผลสองกลุ่ม

---

## F3 — Overextension After Consecutive Same-Direction Candles

- **Market Mechanism**: ลำดับแท่งเทียนทิศทางเดียวกันติดต่อกันจำนวนมากผิดปกติ (เช่น 6-8
  แท่งเขียวติด) มักสะท้อนการไล่ราคา (chasing) ของนักเทรดรายย่อยมากกว่า informed flow ต่อเนื่อง
  จริง — มีแนวโน้ม mean-revert ระยะสั้นหลังจากลำดับยาวผิดปกติ
- **Hypothesis**: หลังแท่งทิศทางเดียวกันติดต่อกันเกิน threshold ที่หายาก (เทียบ empirical
  distribution ของ streak length ในข้อมูลจริง เช่น เกิน 95th percentile) มีโอกาส pullback/
  reversal ระยะสั้นสูงกว่าค่าเฉลี่ย
- **Required Data**: M1/M5 OHLC ต่อเนื่อง เพื่อสร้าง empirical distribution ของ streak length
- **Features**: ความยาว streak ปัจจุบัน, percentile เทียบ distribution ของ symbol/timeframe
  นี้เอง (ไม่ใช้ threshold ตายตัวข้ามตลาด)
- **Entry Condition**: streak ยาวเกิน 95th percentile + แท่งกลับทิศทางแรก → เข้าทิศทางสวน
- **Exit Condition**: time-stop สั้น (N แท่ง) หรือถึง target R-multiple เล็ก
- **SL Concept**: เลยจุดสูงสุด/ต่ำสุดของ streak
- **TP Concept**: retracement 38-50% ของ streak move (Fibonacci-style แต่ยึด empirical
  ไม่ใช่ magic number)
- **Timeframe**: M1/M5
- **Session**: ทุก session — ทดสอบว่า streak ยาวผิดปกติเกิดบ่อย/ได้ผลต่างกันตาม session
  หรือไม่
- **Expected Edge**: การเข้าสวนหลัง extreme streak ควรมี win-rate สูงกว่าการเข้าสวนแท่งทิศทาง
  เดียวกันแบบสุ่มความยาว (baseline)
- **Failure Condition**: ถ้า streak ยาวมักเกิดในวัน trend-day ที่ไปต่อจริง (คล้าย D3) —
  reversal ไม่เกิด → ต้องแยก regime มิฉะนั้น REJECT
- **Test Method**: สร้าง empirical distribution ของ streak length ทั้งชุดข้อมูล วัด forward
  return หลัง extreme streak เทียบ non-extreme streak เดียวกันความยาวปานกลาง

---

## F4 — VWAP Band Fade (Bollinger-style band รอบ VWAP)

- **Market Mechanism**: ต่างจาก F1 ตรงที่ใช้ band แบบไดนามิก (VWAP ± k×rolling-std) แทน
  fixed-SD ของทั้ง session — จับจังหวะ fade ที่ปรับตัวตามความผันผวนปัจจุบันแบบ rolling แทนที่
  จะรอ session สะสมนาน ทำให้ใช้ได้เร็วกว่า F1 ตั้งแต่ต้น session
- **Hypothesis**: ราคาที่แตะ VWAP band บน/ล่าง (rolling 20-period std) ระหว่างช่วงที่ไม่มี
  เทรนด์ยืนยัน (ไม่มี BOS ทิศทางเดียวกัน ≥2 ครั้งตามหมวด B) มีโอกาส fade กลับเข้า band สูงกว่า
  breakout ทะลุ band
- **Required Data**: M1/M5 OHLC + tick volume ต่อเนื่อง
- **Features**: ตำแหน่งราคาเทียบ band, สถานะ BOS (มีเทรนด์หรือไม่)
- **Entry Condition**: แตะ band บน/ล่าง + ไม่มี BOS ยืนยันเทรนด์ + แท่งปฏิเสธ → เข้าทิศทาง
  fade
- **Exit Condition**: กลับถึง VWAP (mid-band) หรือ time-stop
- **SL Concept**: เลย band ออกไปอีกระยะหนึ่ง (เช่น +0.5×std)
- **TP Concept**: VWAP (mid-band)
- **Timeframe**: M1/M5
- **Session**: ทุก session — regime filter (no-trend) สำคัญกว่า session filter ในข้อนี้
- **Expected Edge**: fade-rate เมื่อไม่มีเทรนด์ยืนยันควรสูงกว่า fade-rate เมื่อมีเทรนด์ยืนยัน
  (regime-dependent edge) — ถ้าพิสูจน์ได้ว่า filter BOS ช่วยแยกผลได้จริง จะเป็นหลักฐานว่า
  mean-reversion ใช้ได้เฉพาะ range-regime เท่านั้น
- **Failure Condition**: ถ้า fade-rate ไม่ต่างกันระหว่างมี/ไม่มีเทรนด์ยืนยัน (filter ไม่มี
  information value) → REJECT การใช้ BOS-filter แต่พิจารณาทดสอบ F1/F4 แบบไม่มี filter ต่อ
- **Test Method**: แบ่งกลุ่มตามสถานะ BOS วัด fade-rate/expectancy แต่ละกลุ่ม เทียบสถิติ
  ระหว่างสองกลุ่ม และเทียบกับ F1 (fixed-SD) ว่า dynamic band ให้ edge ดีกว่าจริงหรือไม่
