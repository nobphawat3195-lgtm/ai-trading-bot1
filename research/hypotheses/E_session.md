# หมวด E — Session Behavior (4 hypotheses)

หมายเหตุสำคัญ: ต่างจาก Forbidden Logic ข้อ 4 — ทุกข้อในหมวดนี้ผูกกับ **session ที่มี
เหตุผลเชิงโครงสร้างตลาดจริง** (ชั่วโมงเปิด/ทับซ้อนของตลาดหลักตามเวลามาตรฐานสากล) ไม่ใช่
ตัวเลขนาฬิกาที่ได้จากการ optimize ย้อนหลัง

---

## E1 — London Session Open Directional Expansion

- **Market Mechanism**: London (ตลาด forex/gold ที่มีปริมาณธุรกรรมมากที่สุดของวัน) เปิดตอน
  08:00 London time (07:00/08:00 UTC ขึ้นกับ DST) มักดึงสภาพคล่องสถาบันกลับเข้าตลาดหลังช่วง
  Asian ที่เบาบาง — momentum ชั่วโมงแรกของ London มักสะท้อนทิศทางที่มี informed flow
- **Hypothesis**: ทิศทางการเคลื่อนไหว 15 นาทีแรกหลัง London open มีความสัมพันธ์เชิงบวกกับ
  ทิศทางการเคลื่อนไหวของทั้งชั่วโมงแรก (momentum persistence ระดับ intra-hour)
- **Required Data**: M1/M5 ต่อเนื่องครอบคลุมช่วง London open ทุกวันทำการ
- **Features**: ทิศทาง 15 นาทีแรก (return sign), magnitude ของ 15 นาทีแรก
- **Entry Condition**: 15 นาทีแรกของ London open ปิด return เกิน threshold (เช่น
  >0.3×ATR15) → เข้าทิศทางเดียวกัน
- **Exit Condition**: จบชั่วโมงแรกของ London (time-stop) หรือ momentum กลับทิศทาง
- **SL Concept**: กลับไปยังจุดเปิด London
- **TP Concept**: R-multiple คงที่ระหว่าง Discovery
- **Timeframe**: M1/M5
- **Session**: London open (07:00-08:00 UTC ฤดูหนาว / 07:00-08:00 UTC ตาม London local
  08:00 — ต้องคำนวณ UTC จริงจาก London DST ไม่ใช่ hardcode)
- **Expected Edge**: momentum persistence ระดับสั้น (intra-hour) ที่มีเอกสารวิชาการรองรับใน
  ตลาด forex ช่วง major session open
- **Failure Condition**: ถ้า correlation ระหว่าง 15-นาทีแรกกับชั่วโมงเต็มไม่มีนัยสำคัญ →
  REJECT
- **Test Method**: คำนวณ correlation/win-rate ของ continuation แยกตามวันในสัปดาห์และ
  magnitude ของการเคลื่อนไหวเริ่มต้น

---

## E2 — NY Open Reversal of Asian/London Range Extreme

- **Market Mechanism**: เมื่อ NY session เปิด (13:30 UTC ฤดูหนาว/12:30 UTC ฤดูร้อน ตาม NY
  DST) มักมีข่าวเศรษฐกิจสหรัฐฯ และสภาพคล่องเพิ่มขึ้นมาก — ถ้าราคาอยู่ที่ extreme ของ range
  สะสมจาก Asian+London ก่อนหน้า NY flow มักเทรดสวนกลับเข้า range (fade the extreme) ก่อน
  จะตัดสินทิศทางจริงของวัน
- **Hypothesis**: ถ้าราคา ณ NY open อยู่ใกล้ high/low ของ Asian+London range (ภายใน 10% บน/
  ล่างของ range) มีโอกาส fade กลับเข้า range ในชั่วโมงแรกของ NY มากกว่า breakout ต่อ
- **Required Data**: M5/M15 ครอบคลุม Asian+London+NY open ต่อเนื่อง
- **Features**: ตำแหน่งราคา ณ NY open เทียบ Asian+London range (%), ขนาด range สะสม
- **Entry Condition**: ราคาอยู่ extreme ของ range เมื่อ NY เปิด → เข้าทิศทาง fade เข้า range
- **Exit Condition**: ถึงกึ่งกลาง range หรือ time-stop 1 ชม.
- **SL Concept**: เลย extreme ของ range ที่ใช้อ้างอิง
- **TP Concept**: mid-range หรือ extreme ฝั่งตรงข้าม
- **Timeframe**: M5-M15
- **Session**: NY open โดยเฉพาะ
- **Expected Edge**: fade-rate ที่ NY open เมื่อราคาอยู่ extreme ควรสูงกว่า breakout-rate
  เพราะ NY flow มักทดสอบ liquidity ทั้งสองฝั่งก่อนตัดสินทิศทาง
- **Failure Condition**: ถ้า NY open เป็น breakout-continuation มากกว่า fade อย่างมีนัยสำคัญ
  (ตรงข้าม hypothesis) → REJECT รูปแบบ fade แต่บันทึกเป็นข้อมูลสำหรับ hypothesis breakout แทน
- **Test Method**: วัด outcome (fade vs breakout) ของทุกวันที่ราคาอยู่ extreme ตอน NY open
  เทียบสัดส่วนกับ null 50/50

---

## E3 — London/NY Overlap Momentum Continuation

- **Market Mechanism**: ช่วงทับซ้อนของ London และ NY (12:30-16:00 UTC ฤดูร้อน,
  13:00-16:00 UTC ฤดูหนาว ขึ้นกับ DST ทั้งสองตลาด) เป็นช่วงที่มีสภาพคล่องสูงสุดของวันเพราะ
  สถาบันทั้งสองฝั่งมหาสมุทรแอตแลนติกเทรดพร้อมกัน — เทรนด์ที่เกิดขึ้นแล้วก่อนหน้า overlap
  มักได้แรงหนุนต่อในช่วงนี้
- **Hypothesis**: ถ้ามีเทรนด์ชัดเจน (BOS ทิศทางเดียวกัน ≥2 ครั้ง ดูหมวด B) ก่อนเข้า overlap
  window การ continuation ในช่วง overlap มี win-rate สูงกว่าการเข้าเทรนด์เดียวกันนอกช่วง
  overlap
- **Required Data**: M5/M15 ต่อเนื่อง + BOS detection (ใช้ logic เดียวกับ B1)
- **Features**: สถานะเทรนด์ก่อน overlap, เวลาที่เข้าสู่ overlap window
- **Entry Condition**: เทรนด์ยืนยันก่อน overlap + pullback ตื้นระหว่าง overlap → เข้าตามเทรนด์
- **Exit Condition**: จบ overlap window หรือ CHOCH invalidate
- **SL Concept**: ใต้/เหนือ pullback low/high
- **TP Concept**: extension ตาม leg เทรนด์ก่อนหน้า
- **Timeframe**: M5-M15
- **Session**: London/NY overlap เท่านั้น (คำนวณ UTC จริงตาม DST ของทั้งสองตลาด ไม่ hardcode)
- **Expected Edge**: win-rate ของ continuation ในช่วง overlap สูงกว่านอกช่วง overlap อย่างมี
  นัยสำคัญ (ทดสอบเทียบ B1 ตรงๆ แยกตาม session)
- **Failure Condition**: ถ้า win-rate ไม่ต่างจาก B1 นอกช่วง overlap → REJECT เป็น hypothesis
  แยก (ให้ overlap เป็นแค่ time filter ของ B1 แทน ไม่ใช่ edge อิสระ)
- **Test Method**: เปรียบเทียบ expectancy ของ B1-style continuation entries ที่เกิดในช่วง
  overlap vs นอกช่วง overlap

---

## E4 — Asian Range Breakout at London Open (Structural, ต่างจาก D2)

- **Market Mechanism**: Asian session (00:00-07:00 UTC โดยประมาณ) มักมีสภาพคล่องต่ำกว่าและ
  เทรดในกรอบ (accumulation) เนื่องจากตลาดหลัก (London/NY) ปิดทำการ — เมื่อ London เปิด
  สภาพคล่องสถาบันกลับเข้าตลาดและมักทดสอบ/ทะลุขอบ Asian range เพื่อ "ค้นหาราคา" (price
  discovery) จุดต่างจาก D2: ที่นี่ไม่กรองด้วย range percentile ที่แคบผิดปกติ แต่ทดสอบ Asian
  range **ทุกวัน** ว่า breakout ครั้งแรกที่ London open มักเป็นทิศทางเดียวกับที่ยืนตลอดวัน
  หรือไม่ (คนละสมมติฐานกับ D2 ที่เจาะจงกรณี range แคบผิดปกติเท่านั้น)
- **Hypothesis**: ทิศทางที่ราคาทะลุ Asian-range เป็นครั้งแรกหลัง London open (ไม่ว่า Asian
  range จะแคบหรือกว้าง) มีความสัมพันธ์เชิงบวกกับทิศทางปิดตลาดของวันนั้น (ทำนาย daily bias)
- **Required Data**: M15 OHLC ต่อเนื่อง
- **Features**: Asian range high/low, ทิศทาง breakout แรกที่ London open, daily close
  เทียบ Asian midpoint
- **Entry Condition**: breakout แรกจาก Asian range หลัง London open → เข้าทิศทางนั้นเพื่อถือ
  ต่อเนื่องถึงปลาย London/ต้น NY
- **Exit Condition**: จบ NY session (time-stop) หรือ CHOCH invalidate ระหว่างทาง
- **SL Concept**: กลับเข้า Asian range เกิน 50%
- **TP Concept**: R-multiple ที่ปรับด้วยขนาด Asian range
- **Timeframe**: M15
- **Session**: London open ถึง NY close
- **Expected Edge**: first-breakout-direction ควรทำนาย daily-close-direction ได้ดีกว่าสุ่ม
  (ถ้าเป็นจริง คือหลักฐานว่า Asian range คือ "การสะสม" ก่อน London ตัดสินทิศทาง)
- **Failure Condition**: ถ้า first-breakout-direction ไม่สัมพันธ์กับ daily-close-direction
  อย่างมีนัยสำคัญ (สุ่มพอๆ กับ D2/E2) → REJECT
- **Test Method**: คำนวณ correlation ระหว่างทิศทาง breakout แรกกับทิศทางปิดวัน ในทุกวันของ
  ชุดข้อมูล ทดสอบนัยสำคัญ และเปรียบเทียบกับ D2 ว่าให้ข้อมูลต่างกันจริงหรือซ้ำซ้อน
