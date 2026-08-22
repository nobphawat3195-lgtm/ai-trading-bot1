//+------------------------------------------------------------------+
//|  BrokerProbe.mq5                                                 |
//|  ตรวจสเปกโบรก + เขตเวลาเซิร์ฟเวอร์ + DST  ก่อนย้าย EA ข้ามโบรก   |
//|                                                                  |
//|  วิธีใช้: ลากลงกราฟ XAUUSD (M1) ของโบรกที่จะตรวจ                |
//|          อ่านผลในแท็บ Experts (Toolbox)                          |
//|                                                                  |
//|  ตอบ 3 คำถามที่ทำให้ backtest ข้ามโบรกไม่ตรงกัน:                 |
//|   1) เซิร์ฟเวอร์นี้ GMT เท่าไร                                   |
//|   2) เซิร์ฟเวอร์นี้ขยับตาม DST หรือไม่ (สำคัญที่สุด)             |
//|   3) หน้าต่างเวลาเป้าหมาย (UTC) ตรงกับนาฬิกาเซิร์ฟเวอร์กี่โมง    |
//+------------------------------------------------------------------+
#property copyright "XAU EA toolkit"
#property version   "1.00"
#property script_show_inputs
#property description "ตรวจสเปกโบรก เขตเวลา และ DST ก่อนย้าย EA ข้ามโบรก"

input int InpTargetUTCStartH = 19;   // หน้าต่างเป้าหมาย: ชั่วโมงเริ่ม (UTC)
input int InpTargetUTCStartM = 0;    // หน้าต่างเป้าหมาย: นาทีเริ่ม (UTC)
input int InpTargetUTCEndH   = 20;   // หน้าต่างเป้าหมาย: ชั่วโมงจบ (UTC)
input int InpTargetUTCEndM   = 30;   // หน้าต่างเป้าหมาย: นาทีจบ (UTC)
input int InpDSTScanMonths   = 12;   // ย้อนสแกนหา DST กี่เดือน

//--- แปลงนาทีของวันเป็นข้อความ hh:mm (พันรอบ 24 ชม. ให้เอง)
string HHMM(int minutes)
  {
   while(minutes < 0)     minutes += 1440;
   while(minutes >= 1440) minutes -= 1440;
   return StringFormat("%02d:%02d", minutes/60, minutes%60);
  }

//+------------------------------------------------------------------+
//| 1) สเปกสัญลักษณ์                                                 |
//+------------------------------------------------------------------+
void ReportSymbol()
  {
   int    digits  = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point   = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int    stopsLv = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   int    freezLv = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   double bid     = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask     = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   Print("──────── 1. สเปกสัญลักษณ์ ────────");
   PrintFormat("โบรก            : %s", AccountInfoString(ACCOUNT_COMPANY));
   PrintFormat("เซิร์ฟเวอร์      : %s", AccountInfoString(ACCOUNT_SERVER));
   PrintFormat("สัญลักษณ์        : %s", _Symbol);
   PrintFormat("ทศนิยม           : %d  (1 จุด = %.5f)", digits, point);
   PrintFormat("ขนาดสัญญา        : %.0f", SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE));
   PrintFormat("ล็อต ต่ำสุด/สูงสุด/ขั้น : %.2f / %.2f / %.2f",
               SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
               SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX),
               SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP));
   PrintFormat("Tick value/size  : %.5f / %.5f",
               SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE),
               SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE));
   PrintFormat("StopsLevel       : %d จุด  ($%.2f)   <-- 0 = วางออเดอร์ชิดราคาได้",
               stopsLv, stopsLv*point);
   PrintFormat("FreezeLevel      : %d จุด  ($%.2f)", freezLv, freezLv*point);
   PrintFormat("สเปรดตอนนี้      : %.0f จุด  ($%.3f)  bid=%.*f ask=%.*f",
               (ask-bid)/point, ask-bid, digits, bid, digits, ask);
   PrintFormat("Swap long/short  : %.3f / %.3f  (โหมด %d, วันสามเท่า %d)",
               SymbolInfoDouble(_Symbol, SYMBOL_SWAP_LONG),
               SymbolInfoDouble(_Symbol, SYMBOL_SWAP_SHORT),
               (int)SymbolInfoInteger(_Symbol, SYMBOL_SWAP_MODE),
               (int)SymbolInfoInteger(_Symbol, SYMBOL_SWAP_ROLLOVER3DAYS));

   long marginMode = AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   PrintFormat("โหมดบัญชี        : %s   <-- EA ต้องใช้ HEDGING",
               marginMode == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING ? "HEDGING (ผ่าน)"
                                                                : "NETTING (EA ใช้ไม่ได้)");
   PrintFormat("เลเวอเรจ         : 1:%d", (int)AccountInfoInteger(ACCOUNT_LEVERAGE));
  }

//+------------------------------------------------------------------+
//| 2) เขตเวลาเซิร์ฟเวอร์ ณ ตอนนี้                                   |
//+------------------------------------------------------------------+
int ReportClock()
  {
   datetime srv = TimeCurrent();
   datetime gmt = TimeGMT();
   int offset   = (int)MathRound(((double)srv - (double)gmt) / 3600.0);

   Print("──────── 2. นาฬิกา ณ ตอนนี้ ────────");
   PrintFormat("เวลาเซิร์ฟเวอร์   : %s", TimeToString(srv, TIME_DATE|TIME_SECONDS));
   PrintFormat("เวลา GMT         : %s", TimeToString(gmt, TIME_DATE|TIME_SECONDS));
   PrintFormat("เวลาเครื่องคุณ    : %s", TimeToString(TimeLocal(), TIME_DATE|TIME_SECONDS));
   PrintFormat(">> เขตเวลาเซิร์ฟเวอร์ = GMT%+d   <-- ค่านี้คือ InpServerGMTOffset / InpExpectedGMT",
               offset);
   return offset;
  }

//+------------------------------------------------------------------+
//| 3) หน้าต่างเป้าหมาย (UTC) -> นาฬิกาเซิร์ฟเวอร์ + เวลาไทย         |
//+------------------------------------------------------------------+
void ReportWindow(const int offset)
  {
   int utcStart = InpTargetUTCStartH*60 + InpTargetUTCStartM;
   int utcEnd   = InpTargetUTCEndH*60   + InpTargetUTCEndM;

   Print("──────── 3. หน้าต่างเวลาเป้าหมาย ────────");
   PrintFormat("เป้าหมาย (UTC)      : %s - %s", HHMM(utcStart), HHMM(utcEnd));
   PrintFormat("นาฬิกาเซิร์ฟเวอร์นี้ : %s - %s",
               HHMM(utcStart + offset*60), HHMM(utcEnd + offset*60));
   PrintFormat("เวลาไทย (GMT+7)     : %s - %s",
               HHMM(utcStart + 7*60), HHMM(utcEnd + 7*60));
  }

//+------------------------------------------------------------------+
//| 4) ตรวจ DST จากประวัติราคา                                       |
//|                                                                  |
//|  หลักการ: ทองมีช่วงพักเทรดทุกวัน (daily break) ซึ่งตรึงกับเวลา   |
//|  ตลาดจริง ไม่ใช่เวลาเซิร์ฟเวอร์  ถ้าเซิร์ฟเวอร์ขยับตาม DST       |
//|  ช่วงพักจะอยู่ที่ "ชั่วโมงเดิม" ของนาฬิกาเซิร์ฟเวอร์ตลอดปี       |
//|  ถ้าเซิร์ฟเวอร์ตรึง GMT+0 (เช่น Exness) ช่วงพักจะเลื่อน 1 ชม.    |
//|  ระหว่างฤดูร้อน/หนาว  ตารางข้างล่างจะเห็นความต่างทันที           |
//+------------------------------------------------------------------+
void ReportDST()
  {
   Print("──────── 4. ตรวจ DST จากช่วงพักเทรดรายวัน ────────");

   datetime to   = TimeCurrent();
   datetime from = to - (datetime)InpDSTScanMonths*30*86400;

   datetime times[];
   int n = CopyTime(_Symbol, PERIOD_M1, from, to, times);
   if(n < 2)
     {
      PrintFormat("!! โหลดข้อมูล M1 ไม่พอ (ได้ %d แท่ง) — เปิดกราฟ M1 แล้วเลื่อนย้อนหลัง"
                  " ให้ MT5 ดาวน์โหลดประวัติก่อน แล้วรันสคริปต์ใหม่", n);
      return;
     }
   PrintFormat("สแกน %d แท่ง M1  (%s ถึง %s)", n,
               TimeToString(times[0], TIME_DATE), TimeToString(times[n-1], TIME_DATE));

   //--- นับความถี่ของ "ชั่วโมงเซิร์ฟเวอร์ที่ช่วงพักเริ่ม" แยกตามเดือน
   int  tally[120][24];   // [ดัชนีเดือน][ชั่วโมง]
   int  monthYear[120], monthNum[120], monthCount = 0;
   ArrayInitialize(tally, 0);

   for(int i = 1; i < n; i++)
     {
      int gapMin = (int)((times[i] - times[i-1]) / 60);
      //--- ช่วงพักรายวันของทองยาว ~60 นาที  ตัดช่วงหยุดสุดสัปดาห์ (>300 นาที) ทิ้ง
      if(gapMin < 30 || gapMin > 300) continue;

      MqlDateTime dt;
      TimeToStruct(times[i-1], dt);

      int idx = -1;
      for(int m = 0; m < monthCount; m++)
         if(monthYear[m] == dt.year && monthNum[m] == dt.mon) { idx = m; break; }
      if(idx < 0)
        {
         if(monthCount >= 120) continue;
         idx = monthCount++;
         monthYear[idx] = dt.year;
         monthNum[idx]  = dt.mon;
        }
      tally[idx][dt.hour]++;
     }

   if(monthCount == 0)
     {
      Print("!! ไม่พบช่วงพักรายวันในข้อมูลนี้ — สัญลักษณ์นี้อาจเทรด 24 ชม.");
      Print("   ให้ตรวจ DST ด้วยวิธีอื่น: เปิดสคริปต์นี้ซ้ำหลังวันเปลี่ยน DST");
      Print("   (ยุโรป: อาทิตย์สุดท้ายของ มี.ค. และ ต.ค.) แล้วเทียบค่าในข้อ 2");
      return;
     }

   Print("เดือน    | ชั่วโมง(เซิร์ฟเวอร์)ที่ช่วงพักเริ่ม | จำนวนวัน");
   int firstHour = -1, lastHour = -1;
   bool shifted = false;
   for(int m = 0; m < monthCount; m++)
     {
      int bestH = -1, bestC = 0;
      for(int h = 0; h < 24; h++)
         if(tally[m][h] > bestC) { bestC = tally[m][h]; bestH = h; }
      if(bestH < 0) continue;
      PrintFormat("%04d-%02d | %02d:00                              | %d",
                  monthYear[m], monthNum[m], bestH, bestC);
      if(firstHour < 0) firstHour = bestH;
      lastHour = bestH;
      if(bestH != firstHour) shifted = true;
     }

   Print("");
   if(shifted)
     {
      PrintFormat(">> ช่วงพักเลื่อนระหว่างปี (%02d:00 <-> %02d:00 เวลาเซิร์ฟเวอร์)", firstHour, lastHour);
      Print(">> แปลว่า เซิร์ฟเวอร์นี้ 'ไม่' ขยับตาม DST  =  offset คงที่ทั้งปี");
      Print(">> ตั้ง InpServerGMTOffset / InpExpectedGMT ค่าเดียวได้ตลอดปี (ค่าจากข้อ 2)");
     }
   else
     {
      PrintFormat(">> ช่วงพักอยู่ที่ %02d:00 เวลาเซิร์ฟเวอร์เท่ากันทุกเดือน", firstHour);
      Print(">> แปลว่า เซิร์ฟเวอร์นี้ 'ขยับตาม' DST  =  offset เปลี่ยนปีละ 2 ครั้ง");
      Print(">> !! ต้องแก้ InpServerGMTOffset / InpExpectedGMT ทุกครั้งที่เปลี่ยน DST");
      Print(">> !! และ backtest ที่คร่อมวันเปลี่ยน DST จะเทรดผิดชั่วโมงไปครึ่งช่วง");
     }
  }

//+------------------------------------------------------------------+
void OnStart()
  {
   Print("════════════ BrokerProbe v1.00 ════════════");
   ReportSymbol();
   int offset = ReportClock();
   ReportWindow(offset);
   ReportDST();
   Print("════════════ จบรายงาน ════════════");
   Print("คัดลอกทั้งหมดจากแท็บ Experts (คลิกขวา -> Copy) ส่งกลับมาได้เลย");
  }
//+------------------------------------------------------------------+
