# หมวด H — Statistical Behavior (4 hypotheses)

หมวดนี้เป็น "pure statistical" filters/edges ที่ไม่ผูกกับ market-structure concept
โดยตรง แต่ยังต้องมีเหตุผลเชิงกลไกประกอบ (ไม่ใช่แค่ data-mining ตัวเลข) ตามกฎข้อ 3 ของ
MASTER COMMAND

---

## H1 — Hour-of-Day Return Seasonality

- **Market Mechanism**: กิจกรรมตลาด XAUUSD ไม่สม่ำเสมอตลอด 24 ชม. — สภาพคล่อง, ผู้เล่น,
  และ event ข่าวมาตรฐาน (เช่น US data release เวลาคงที่) กระจุกตัวในบางชั่วโมง ทำให้ mean
  return และ variance รายชั่วโมงต่างกันอย่างมีนัยสำคัญทางสถิติได้ในทางทฤษฎี — แต่ต้องระวัง
  ว่านี่คือ correlation ไม่ใช่ causation จนกว่าจะผูกกับกลไกจริง (เช่น เวลาข่าวมาตรฐาน)
- **Hypothesis**: บางชั่วโมงของวัน (UTC) มี mean directional return ที่ต่างจาก 0 อย่างมี
  นัยสำคัญทางสถิติ อย่างสม่ำเสมอข้ามหลายเดือน/ปี ไม่ใช่ noise ของช่วงตัวอย่างเดียว
- **Required Data**: M15/H1 OHLC ย้อนหลังอย่างน้อย 2-3 ปี (เพื่อแยก seasonality จริงจาก noise)
- **Features**: hour-of-day (UTC), mean return, std, sample size ต่อชั่วโมง
- **Entry Condition**: เข้าเมื่อเปิดชั่วโมงที่มี historical mean-return นัยสำคัญ ทิศทางตาม
  bias ทางสถิตินั้น
- **Exit Condition**: ปิดเมื่อจบชั่วโมงนั้น (fixed holding period)
- **SL Concept**: ATR-based ของชั่วโมงนั้นโดยเฉพาะ (variance รายชั่วโมงต่างกัน)
- **TP Concept**: ไม่ตั้ง fixed — ปิดตามเวลา (time-exit)
- **Timeframe**: H1 หลัก, M15 สำหรับ execution
- **Session**: ทุกชั่วโมงถูกทดสอบ ไม่จำกัด — ผลจะบอกเองว่าชั่วโมงไหนมีนัยสำคัญ
- **Expected Edge**: ถ้าพบชั่วโมงที่ significant และ **สอดคล้องกับเหตุผลเชิงกลไก** (เช่น
  ตรงกับเวลาข่าว/session open มาตรฐาน) จะมีความน่าเชื่อถือสูงกว่าชั่วโมงที่ significant แบบ
  ไม่มีคำอธิบาย (ซึ่งมีความเสี่ยง data-mining สูง ต้องระวังเป็นพิเศษ)
- **Failure Condition**: ถ้า effect ไม่เสถียรข้าม sub-period (แบ่งข้อมูลเป็น 2-3 ช่วงย่อย
  แล้วทิศทาง/นัยสำคัญเปลี่ยนไป) → REJECT ทันที ถือเป็น false positive จาก multiple-testing
- **Test Method**: multiple-hypothesis-testing correction (เช่น Bonferroni สำหรับ 24
  ชั่วโมง) บน mean-return ต่อชั่วโมง, ตรวจ stability ข้าม sub-period ก่อนเชื่อผล

---

## H2 — Day-of-Week Effect

- **Market Mechanism**: พฤติกรรมตลาดต่างกันตามวันในสัปดาห์จากเหตุผลเชิงโครงสร้าง เช่น
  วันจันทร์มักมี gap จากสุดสัปดาห์และสภาพคล่องเบาบางช่วงเช้า, วันศุกร์มักมีการปิด position
  ก่อนสุดสัปดาห์ (weekend risk aversion) — เป็นปรากฏการณ์ที่มีเหตุผลเชิงพฤติกรรมนักลงทุนรองรับ
- **Hypothesis**: return distribution และ volatility ของวันจันทร์/ศุกร์ ต่างจากวันอังคาร-
  พฤหัสบดีอย่างมีนัยสำคัญ (ทั้งในแง่ magnitude และทิศทาง)
- **Required Data**: Daily OHLC ย้อนหลัง 2-3 ปี
- **Features**: day-of-week, daily return, daily range
- **Entry Condition**: ใช้เป็น **filter ประกอบ** hypothesis อื่น (เช่น ลด position หรือเลี่ยง
  เทรด mean-reversion ในวันที่มี weekend-gap risk) มากกว่าเป็น standalone entry
- **Exit Condition**: N/A (เป็น filter ไม่ใช่ entry เดี่ยว)
- **SL Concept**: N/A — ใช้ SL ของ hypothesis หลักที่ H2 ไปกรอง
- **TP Concept**: N/A
- **Timeframe**: Daily
- **Session**: ทั้งวัน
- **Expected Edge**: ถ้าวันจันทร์มี false-breakout สูงกว่าปกติ (เพราะสภาพคล่องเบาบาง) การใช้
  H2 กรองวันจันทร์ออกจาก breakout-hypothesis (เช่น E4/G2) ควรเพิ่ม win-rate ของ subset ที่
  เหลือ
- **Failure Condition**: ถ้า day-of-week ไม่มีผลต่อ win-rate ของ hypothesis ที่ทดสอบ (ทั้ง
  breakout และ mean-reversion) → REJECT การใช้เป็น filter
- **Test Method**: วัด win-rate ของ hypothesis หลัก (เช่น E4) แยกตามวันในสัปดาห์ ทดสอบ
  ANOVA/chi-square ว่าความต่างมีนัยสำคัญหรือไม่

---

## H3 — Consecutive Loss/Win Streak Behavioral Reversal (ระดับวัน ไม่ใช่ระดับไม้)

- **Market Mechanism**: ต่างจาก F3 (streak ของแท่งเทียน) — ข้อนี้มองที่ streak ของ **ทิศทาง
  ปิดตลาดรายวัน** ติดต่อกัน (เช่น ปิดบวก 5 วันติด) ซึ่งสะท้อนการไล่ราคาสะสมของนักลงทุนรายย่อย
  ในกรอบเวลาที่ยาวกว่า intraday — มีวรรณกรรมด้าน behavioral finance สนับสนุนว่า
  overextension ระดับวันมักตามด้วย mean-reversion ระดับสัปดาห์
- **Hypothesis**: หลังจากราคาปิดทิศทางเดียวกันติดต่อกันเกิน threshold ที่หายาก (เทียบ
  empirical distribution ของ daily-close-streak) มีโอกาส reversal ในช่วง 3-5 วันถัดไปสูงกว่า
  ค่าเฉลี่ย
- **Required Data**: Daily close ย้อนหลัง 3-5 ปี (เพื่อสร้าง empirical streak distribution
  ที่เชื่อถือได้)
- **Features**: ความยาว daily-close streak, percentile เทียบ distribution
- **Entry Condition**: streak เกิน 90th percentile → เข้าทิศทางสวน ถือหลายวัน (swing, ไม่ใช่
  intraday)
- **Exit Condition**: N วันถัดไป (time-stop) หรือถึง target
- **SL Concept**: เลยจุดสูงสุด/ต่ำสุดของ streak
- **TP Concept**: retracement บางส่วนของ streak move
- **Timeframe**: Daily (นอกขอบเขตหลัก M1/M5 ของโปรเจกต์ — ระบุไว้ชัดเจนว่าเป็น swing-scale
  ทดสอบเพื่อเปรียบเทียบ ไม่ใช่กลยุทธ์หลักที่จะนำไปสร้าง EA M1 โดยตรง)
- **Session**: N/A (daily-scale)
- **Expected Edge**: reversal-rate หลัง extreme daily streak ควรสูงกว่า baseline (ที่ไม่มี
  streak) อย่างมีนัยสำคัญ
- **Failure Condition**: ถ้า sample size ของ extreme streak น้อยเกินไปจนไม่มีนัยสำคัญทาง
  สถิติ (โอกาสสูงเพราะ streak ยาวๆ หายาก) → REJECT หรือระบุเป็น "insufficient evidence"
  ไม่ใช่ "REJECT เพราะพิสูจน์ว่าไม่มี edge" (ต้องแยกสองกรณีนี้ให้ชัดในรายงาน)
- **Test Method**: สร้าง empirical distribution ของ daily streak length, วัด forward N-day
  return หลัง extreme streak เทียบ non-extreme, ตรวจ sample size ให้พอก่อนสรุป

---

## H4 — Previous Session Return Autocorrelation

- **Market Mechanism**: ผลตอบแทนของ session หนึ่ง (เช่น Asian) อาจมีความสัมพันธ์เชิงสถิติกับ
  ผลตอบแทนของ session ถัดไป (London) ผ่านกลไก order-flow ต่อเนื่อง (position ที่เปิดใน Asian
  ถูก manage ต่อใน London) หรือกลไก mean-reversion ข้าม session — ทิศทางความสัมพันธ์ (บวก/ลบ)
  เป็นคำถามเชิงประจักษ์ที่ต้องทดสอบ ไม่ตั้งสมมติฐานทิศทางล่วงหน้า
- **Hypothesis**: ผลตอบแทนของ session ก่อนหน้า (sign และ magnitude) มีค่าพยากรณ์
  (predictive power) ต่อผลตอบแทนของ session ถัดไป มากกว่าระดับสุ่ม
- **Required Data**: M15 OHLC ต่อเนื่อง เพื่อคำนวณ return ราย session (Asian/London/NY)
  ย้อนหลังหลายเดือน-ปี
- **Features**: return ของ session ก่อนหน้า (sign, magnitude), session คู่ที่ทดสอบ
  (Asian→London, London→NY, NY→Asian วันถัดไป)
- **Entry Condition**: เปิด session ใหม่ + return ของ session ก่อนหน้าเข้าเงื่อนไขที่มี
  predictive power (ทิศทางตามผลการทดสอบเชิงประจักษ์ ไม่ fix ไว้ล่วงหน้า) → เข้าทิศทางที่
  โมเดลทำนาย
- **Exit Condition**: จบ session ปัจจุบัน (time-stop)
- **SL Concept**: ATR-based ของ session ปัจจุบัน
- **TP Concept**: time-exit เป็นหลัก ไม่ fix price target
- **Timeframe**: M15
- **Session**: ทดสอบทุกคู่ session ที่ต่อเนื่องกัน (Asian→London, London→NY, NY→Asian)
- **Expected Edge**: ถ้าพบ autocorrelation (บวกหรือลบ) ที่เสถียรข้าม sub-period จะเป็น edge
  เชิงสถิติล้วนที่ใช้ประกอบกับ hypothesis เชิงกลไกอื่นได้ (เช่น เป็น directional bias filter
  ให้ E1/E2)
- **Failure Condition**: ถ้า correlation ไม่มีนัยสำคัญ หรือมีนัยสำคัญแต่กลับทิศทางระหว่าง
  sub-period ต่างๆ (ไม่เสถียร) → REJECT
- **Test Method**: คำนวณ correlation (Pearson หรือ Spearman) ระหว่าง return session-ก่อน
  กับ session-ถัดไป แยกคู่ session, ทดสอบนัยสำคัญ + ตรวจ stability ข้าม sub-period ก่อนสรุป
