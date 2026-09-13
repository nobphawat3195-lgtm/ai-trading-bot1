# หมวด C — Imbalance / Fair Value Gap (3 hypotheses)

---

## C1 — Fair Value Gap (FVG) Fill Reversal

- **Market Mechanism**: FVG (ช่องว่างราคาที่แท่งกลางไม่ทับซ้อนกับแท่งซ้าย-ขวา) เกิดจากการ
  เคลื่อนไหวเร็วเกินกว่า order flow ทั้งสองฝั่งจะจับคู่กันได้ทัน — ราคามักย้อนกลับมา "เติม"
  ช่องว่างนี้บางส่วนก่อนไปทิศทางเดิม (inefficiency fill) เป็นพฤติกรรมที่สังเกตซ้ำได้
- **Hypothesis**: เมื่อราคาย้อนกลับมาแตะขอบ FVG (50% ของช่องว่าง) แล้วมีแท่งปฏิเสธ
  (rejection wick) มี edge เข้าทิศทางเดิมของ FVG ต่อ (FVG เป็นแนวรับ/แนวต้านชั่วคราว)
- **Required Data**: OHLC M1/M5 ต่อเนื่อง
- **Features**: ขนาด FVG (points), % ที่ราคาเข้าไปเติมก่อน reject, อายุของ FVG (บาร์นับจาก
  เกิดถึงถูกทดสอบ)
- **Entry Condition**: ราคาแตะโซน FVG (ภายใน 50% แรกของช่องว่าง) + แท่งปฏิเสธ → เข้าทิศทาง
  เดิมของ FVG
- **Exit Condition**: ถึง origin ของ leg ที่สร้าง FVG หรือ time-stop
- **SL Concept**: ฝั่งตรงข้ามของ FVG (เลย 50%-100% ของช่องว่าง)
- **TP Concept**: จุดเริ่มต้นของ leg ที่สร้าง FVG (measured move)
- **Timeframe**: M5 หลัก, M1 สำหรับ timing entry แม่นขึ้น
- **Session**: ทุก session — คาด London/NY มี FVG คุณภาพสูงกว่า (displacement ชัดกว่า)
- **Expected Edge**: FVG ที่ถูกทดสอบครั้งแรกและ reject มี win-rate สูงกว่า baseline สุ่ม
  เพราะสะท้อน unfilled order flow จริง
- **Failure Condition**: ถ้า FVG ที่ถูกเติมเกิน 50% มักวิ่งทะลุต่อ (invalidate) บ่อยกว่า
  reject → REJECT รูปแบบนี้ พิจารณา C2 แทน
- **Test Method**: เก็บทุก FVG ที่เกิด วัด outcome (reject vs fill-through) แยกตามขนาด FVG
  และ session, ทดสอบว่า reject-rate สูงกว่าสุ่มอย่างมีนัยสำคัญหรือไม่

---

## C2 — Displacement Retracement into FVG (Continuation Entry)

- **Market Mechanism**: ตรงข้ามกับ C1 ในแง่การใช้งาน — แทนที่จะเทรด FVG เป็นแนวรับ/ต้าน
  hypothesis นี้ใช้ FVG เป็น "จุดเข้าที่มีต้นทุนต่ำ" ระหว่างเทรนด์ที่ยังคงตัว โดยรอ retracement
  เข้าไปใน FVG แล้วไปต่อทิศทางเดิม (ไม่ใช่ reversal)
- **Hypothesis**: ในบริบทที่มี BOS ยืนยันเทรนด์อยู่แล้ว (ดูหมวด B) การ retrace เข้า FVG ล่าสุด
  ที่สร้างจาก impulse leg ทิศทางเทรนด์ แล้วดีดออกจาก FVG ไปทิศทางเดิม มี edge continuation
  ที่ risk:reward ดีกว่าการไล่ราคา (chase breakout)
- **Required Data**: OHLC M5 + สถานะ BOS ล่าสุด (ใช้ logic เดียวกับ B1)
- **Features**: ทิศทาง BOS ปัจจุบัน, ตำแหน่ง FVG เทียบกับเทรนด์, ความลึกของ retracement
- **Entry Condition**: เทรนด์ยืนยันจาก BOS + ราคาแตะ FVG ของ impulse leg ล่าสุด + แท่งดีดออก
  ทิศทางเทรนด์ → เข้าตาม
- **Exit Condition**: BOS ทิศทางเดิมยืนยันซ้ำ (partial take) หรือ CHOCH invalidate
- **SL Concept**: ฝั่งตรงข้ามของ FVG
- **TP Concept**: swing ถัดไปตามทิศทางเทรนด์
- **Timeframe**: M5
- **Session**: London/NY (เทรนด์ intraday ชัดกว่า Asian)
- **Expected Edge**: risk:reward ดีกว่าการเข้าตาม breakout ตรงๆ เพราะ SL แคบกว่า (อยู่ติด
  FVG) ในขณะที่ target เท่ากัน
- **Failure Condition**: ถ้า retracement ทะลุ FVG ต่อเนื่อง (invalidate) บ่อยกว่าที่คาด →
  REJECT หรือปรับเป็นรอ confirmation เพิ่ม
- **Test Method**: วัด expectancy ของ entry-at-FVG-retest เทียบกับ entry-at-breakout (B1)
  บนชุด BOS event เดียวกัน — ต้องได้ R-multiple เฉลี่ยดีกว่าอย่างมีนัยสำคัญ

---

## C3 — Session-Open Gap Fill

- **Market Mechanism**: XAUUSD เทรดเกือบ 24 ชม. แต่ยังมีช่วงสภาพคล่องบางระหว่างปิด NY/เปิด
  Asian ที่ทำให้เกิด "gap" เล็กๆ ระหว่างปิดแท่งสุดท้ายของวันก่อนกับเปิดแท่งแรกของวันถัดไป
  (broker daily close) — ช่องว่างนี้มักถูกเติมเต็มในช่วงต้นของ session ถัดไป
- **Hypothesis**: gap เปิดตลาด (เทียบ close วันก่อนกับ open วันนี้) ที่มีขนาดเกิน threshold
  (เช่น > 0.5×ATR รายวัน) มีแนวโน้มถูกเติมเต็มบางส่วนภายในชั่วโมงแรกของการเทรดวันใหม่
- **Required Data**: Daily close/open ต่อเนื่อง + M5 intraday ของชั่วโมงแรก
- **Features**: ขนาด gap (points, เทียบ ATR รายวัน), ทิศทาง gap, session ที่ gap เกิด
- **Entry Condition**: เปิดตลาดแล้วมี gap เกิน threshold → เข้าทิศทางเข้าหา close เดิม
  (fade gap) ทันทีที่เปิด session หรือรอ pullback เล็กน้อยยืนยันก่อน
- **Exit Condition**: ราคาแตะระดับ close เดิม (fill สมบูรณ์) หรือ time-stop (เช่น 2 ชม.แรก)
- **SL Concept**: ถัดจากจุดเปิดตลาดในทิศทางตรงข้าม (gap ขยายต่อ = invalidate)
- **TP Concept**: ระดับ close ของวันก่อนหน้า (full fill) หรือ partial fill (50%)
- **Timeframe**: Daily สำหรับ detect gap, M5 สำหรับ execution
- **Session**: ต้นชั่วโมงแรกของ session ที่มีสภาพคล่องกลับมา (Asian open หรือ London open
  ขึ้นกับ broker's daily close time)
- **Expected Edge**: fill-rate ของ gap เกิน threshold ควรสูงกว่า 50% อย่างมีนัยสำคัญถ้า
  hypothesis ถูกต้อง (เป็น mean-reversion เชิงโครงสร้างสภาพคล่อง ไม่ใช่ momentum)
- **Failure Condition**: XAUUSD สภาพคล่องต่อเนื่องสูงกว่า FX คู่หลักทั่วไป — gap อาจเล็ก/หา
  ยากจนไม่มีนัยสำคัญทางสถิติ (sample size ต่ำ) → ถ้า sample ไม่พอหรือ fill-rate ไม่ต่างจาก
  สุ่ม → REJECT
- **Test Method**: รวบรวม daily gap ทั้งหมดในชุดข้อมูล, วัด fill-rate และเวลาเฉลี่ยที่ใช้
  fill, ทดสอบนัยสำคัญเทียบ null hypothesis (fill-rate = 50%)
