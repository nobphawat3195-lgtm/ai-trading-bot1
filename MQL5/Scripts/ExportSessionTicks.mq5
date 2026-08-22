//+------------------------------------------------------------------+
//|  ExportSessionTicks.mq5                                          |
//|  ส่งออกราคา bid/ask ความละเอียด 1 วินาที เฉพาะหน้าต่างเวลาที่ EA |
//|  เทรดจริง -> ไฟล์ CSV ขนาดเล็กพอที่จะส่งให้วิเคราะห์ต่อได้       |
//|                                                                  |
//|  ทำไมต้องกรองหน้าต่างเวลา:                                       |
//|    tick ทองทั้งปี = หลายร้อย MB ส่งไปไหนไม่ได้                   |
//|    แต่ EA เทรดแค่ 1.5 ชม./วัน -> เหลือไม่กี่สิบ MB               |
//|                                                                  |
//|  วิธีใช้: ลากลงกราฟ XAUUSD -> ตั้งช่วงวันที่ -> รัน              |
//|          ไฟล์ออกที่ Data Folder\MQL5\Files\                      |
//|          (MT5: File -> Open Data Folder)                         |
//|                                                                  |
//|  หมายเหตุ: ต้องโหลดประวัติ tick ให้ครบก่อน                       |
//|            (กราฟ M1 -> เลื่อนย้อนหลังจนสุดช่วงที่ต้องการ)        |
//+------------------------------------------------------------------+
#property copyright "XAU EA toolkit"
#property version   "1.00"
#property script_show_inputs
#property description "ส่งออก bid/ask 1 วินาที เฉพาะช่วงเวลาที่ EA เทรด เป็น CSV"

input datetime InpFrom        = D'2025.11.01 00:00';  // เริ่มส่งออก (เวลาเซิร์ฟเวอร์)
input datetime InpTo          = D'2026.08.22 00:00';  // จบส่งออก (เวลาเซิร์ฟเวอร์)
input int      InpServerGMT   = 3;     // เขตเวลาเซิร์ฟเวอร์ (ดูจาก BrokerProbe ข้อ 2)
input int      InpWinStartUTC = 19;    // หน้าต่าง: ชั่วโมงเริ่ม (UTC)
input int      InpWinEndUTC   = 21;    // หน้าต่าง: ชั่วโมงจบ (UTC)
input int      InpPadMinutes  = 90;    // เผื่อหัวท้ายกี่นาที (ให้พอคำนวณ ATR ย้อนหลัง)
input string   InpOutFile     = "xau_session_ticks.csv";  // ชื่อไฟล์ผลลัพธ์

//--- แปลงเวลาเซิร์ฟเวอร์ -> นาทีของวันตาม UTC
int UtcMinuteOfDay(const datetime serverTime, const int offsetHours)
  {
   MqlDateTime dt;
   TimeToStruct(serverTime, dt);
   int m = dt.hour*60 + dt.min - offsetHours*60;
   while(m < 0)     m += 1440;
   while(m >= 1440) m -= 1440;
   return m;
  }

void OnStart()
  {
   if(InpTo <= InpFrom)
     {
      Print("!! ช่วงวันที่ไม่ถูกต้อง: InpTo ต้องมากกว่า InpFrom");
      return;
     }

   int winStart = InpWinStartUTC*60 - InpPadMinutes;
   int winEnd   = InpWinEndUTC*60   + InpPadMinutes;
   PrintFormat("หน้าต่างที่ส่งออก (UTC, รวมเผื่อหัวท้าย %d นาที): %02d:%02d - %02d:%02d",
               InpPadMinutes, (winStart/60+24)%24, ((winStart%60)+60)%60,
               (winEnd/60)%24, winEnd%60);

   int fh = FileOpen(InpOutFile, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
     {
      PrintFormat("!! เปิดไฟล์ไม่ได้: %s (error %d)", InpOutFile, GetLastError());
      return;
     }
   FileWrite(fh, "server_time", "bid", "ask");

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   ulong  rowsOut = 0, ticksIn = 0;
   int    daysDone = 0;

   //--- เดินทีละวันเพื่อไม่ให้ CopyTicksRange กินหน่วยความจำจนล้ม
   for(datetime day = InpFrom; day < InpTo; day += 86400)
     {
      MqlTick ticks[];
      int got = CopyTicksRange(_Symbol, ticks, COPY_TICKS_INFO,
                               (ulong)day*1000, (ulong)(day+86400)*1000);
      if(got <= 0) continue;
      ticksIn += (ulong)got;

      //--- ยุบเหลือวินาทีละ 1 แถว (เก็บราคาสุดท้ายของวินาทีนั้น)
      datetime lastSec = 0;
      double   lastBid = 0.0, lastAsk = 0.0;

      for(int i = 0; i < got; i++)
        {
         datetime t = ticks[i].time;
         int utcMin = UtcMinuteOfDay(t, InpServerGMT);
         //--- winStart อาจติดลบ (ข้ามเที่ยงคืน) จึงเทียบแบบพันรอบ
         int rel = utcMin - ((winStart % 1440) + 1440) % 1440;
         if(rel < 0) rel += 1440;
         if(rel > (winEnd - winStart)) continue;

         if(ticks[i].bid > 0.0) lastBid = ticks[i].bid;
         if(ticks[i].ask > 0.0) lastAsk = ticks[i].ask;
         if(lastBid <= 0.0 || lastAsk <= 0.0) continue;

         if(t != lastSec)
           {
            if(lastSec != 0)
              {
               FileWrite(fh, TimeToString(lastSec, TIME_DATE|TIME_SECONDS),
                         DoubleToString(lastBid, digits),
                         DoubleToString(lastAsk, digits));
               rowsOut++;
              }
            lastSec = t;
           }
        }
      if(lastSec != 0 && lastBid > 0.0 && lastAsk > 0.0)
        {
         FileWrite(fh, TimeToString(lastSec, TIME_DATE|TIME_SECONDS),
                   DoubleToString(lastBid, digits),
                   DoubleToString(lastAsk, digits));
         rowsOut++;
        }

      daysDone++;
      if(daysDone % 20 == 0)
         PrintFormat("... ผ่านไป %d วัน  เขียนแล้ว %I64u แถว", daysDone, rowsOut);
     }

   FileClose(fh);
   PrintFormat("เสร็จ: อ่าน tick %I64u -> เขียน %I64u แถว  ไฟล์: MQL5\\Files\\%s",
               ticksIn, rowsOut, InpOutFile);
   if(rowsOut == 0)
      Print("!! ไม่ได้ข้อมูลเลย — ยังไม่ได้โหลดประวัติ tick หรือ InpServerGMT ตั้งผิด");
   else
      Print("บีบไฟล์เป็น .zip ก่อนส่ง จะเล็กลงราว 5-10 เท่า");
  }
//+------------------------------------------------------------------+
