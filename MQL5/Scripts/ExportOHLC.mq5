//+------------------------------------------------------------------+
//|  ExportOHLC.mq5                                                  |
//|  ส่งออกแท่ง OHLC (M1/M5/M15/M30/H1/H4/Daily) เต็มวัน ทุก session  |
//|  -> CSV สำหรับ Statistical Discovery ของ hypothesis ใหม่          |
//|                                                                  |
//|  ต่างจาก ExportSessionTicks.mq5 ตรงไหน:                          |
//|    ExportSessionTicks.mq5 ส่งออก tick ความละเอียด 1 วินาที       |
//|    เฉพาะหน้าต่างเวลาแคบๆ ที่ EA เดิม (StraddleReverse) เทรด       |
//|    (~1.5-3 ชม./วัน) -- ใช้ตรวจ/backtest EA เดิมเท่านั้น           |
//|                                                                  |
//|    hypothesis ใหม่ 30 ข้อใน research/hypotheses/ กระจายอยู่ทุก    |
//|    session (Asian/London/NY/Overlap) ไม่ได้จำกัดแค่หน้าต่างเดิม  |
//|    -> ต้องมีข้อมูล "เต็มวัน" ทุกวัน ไม่ใช่แค่บางชั่วโมง           |
//|    -> ใช้แท่ง OHLC (เบากว่า tick มาก) แทน จะได้ export ได้ยาว     |
//|       เป็นปีโดยไฟล์ไม่ใหญ่เกินไป                                  |
//|                                                                  |
//|  วิธีใช้: ลากลงกราฟ XAUUSD -> ตั้ง timeframe + ช่วงวันที่ -> รัน  |
//|          ไฟล์ออกที่ Data Folder\MQL5\Files\                      |
//|          (MT5: File -> Open Data Folder)                         |
//|                                                                  |
//|  หมายเหตุ: ต้องโหลดประวัติแท่งให้ครบก่อน                         |
//|            (เปิดกราฟ timeframe ที่จะ export -> เลื่อนย้อนหลัง     |
//|            จนสุดช่วงที่ต้องการ ไม่งั้น CopyRates จะได้แท่งไม่ครบ) |
//+------------------------------------------------------------------+
#property copyright "XAU EA toolkit"
#property version   "1.00"
#property script_show_inputs
#property description "ส่งออกแท่ง OHLC เต็มวันทุก session เป็น CSV สำหรับ edge research"

enum ENUM_EXPORT_TF
  {
   TF_M1  = PERIOD_M1,
   TF_M5  = PERIOD_M5,
   TF_M15 = PERIOD_M15,
   TF_M30 = PERIOD_M30,
   TF_H1  = PERIOD_H1,
   TF_H4  = PERIOD_H4,
   TF_D1  = PERIOD_D1
  };

input datetime     InpFrom   = D'2023.01.01 00:00';  // เริ่มส่งออก (เวลาเซิร์ฟเวอร์)
input datetime     InpTo     = D'2026.08.23 00:00';  // จบส่งออก (เวลาเซิร์ฟเวอร์)
input ENUM_EXPORT_TF InpTF   = TF_M5;                 // Timeframe ที่จะ export
input int          InpServerGMT = 3;      // เขตเวลาเซิร์ฟเวอร์ (ดูจาก BrokerProbe ข้อ 2)
                                            // -> เขียนลง header ไฟล์ ไม่แปลงเวลาให้
                                            //    (แปลงฝั่ง Python ทีเดียวสำหรับทุกไฟล์
                                            //    จะตรวจสอบ/แก้ offset ผิดพลาดได้ง่ายกว่า)
input string        InpOutFile   = "";      // ชื่อไฟล์ผลลัพธ์ (ว่าง = ตั้งชื่ออัตโนมัติ)

string AutoFileName()
  {
   return StringFormat("xau_ohlc_%s_%s.csv", _Symbol, EnumToString((ENUM_TIMEFRAMES)InpTF));
  }

void OnStart()
  {
   if(InpTo <= InpFrom)
     {
      Print("!! ช่วงวันที่ไม่ถูกต้อง: InpTo ต้องมากกว่า InpFrom");
      return;
     }

   ENUM_TIMEFRAMES tf = (ENUM_TIMEFRAMES)InpTF;
   string outFile = (InpOutFile == "") ? AutoFileName() : InpOutFile;

   //--- ตรวจว่ามีประวัติพอไหม เตือนถ้าไม่ครบ (CopyRates คืนแค่เท่าที่มีในเครื่อง)
   datetime firstBar = (datetime)SeriesInfoInteger(_Symbol, tf, SERIES_FIRSTDATE);
   if(firstBar == 0 || firstBar > InpFrom)
     {
      PrintFormat("⚠ ประวัติแท่งที่มีในเครื่องเริ่มที่ %s ซึ่งช้ากว่า InpFrom (%s)",
                  TimeToString(firstBar, TIME_DATE),
                  TimeToString(InpFrom, TIME_DATE));
      Print("   -> เปิดกราฟ timeframe นี้แล้วเลื่อนย้อนหลังให้สุดก่อน แล้วรันสคริปต์นี้ใหม่");
     }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int got = CopyRates(_Symbol, tf, InpFrom, InpTo, rates);
   if(got <= 0)
     {
      PrintFormat("!! อ่านแท่งไม่ได้เลย (CopyRates คืน %d) — ตรวจว่าโหลดประวัติแล้วหรือยัง", got);
      return;
     }

   int fh = FileOpen(outFile, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
     {
      PrintFormat("!! เปิดไฟล์ไม่ได้: %s (error %d)", outFile, GetLastError());
      return;
     }

   //--- header บอก metadata ที่จำเป็นต่อการตีความไฟล์ฝั่ง Python ให้ครบ
   FileWrite(fh, "# symbol=" + _Symbol,
             "timeframe=" + EnumToString(tf),
             "server_gmt_offset=" + IntegerToString(InpServerGMT),
             "digits=" + IntegerToString((int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
             "point=" + DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_POINT), 8));
   FileWrite(fh, "server_time", "open", "high", "low", "close", "tick_volume", "spread");

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   for(int i = 0; i < got; i++)
     {
      FileWrite(fh,
                TimeToString(rates[i].time, TIME_DATE|TIME_SECONDS),
                DoubleToString(rates[i].open,  digits),
                DoubleToString(rates[i].high,  digits),
                DoubleToString(rates[i].low,   digits),
                DoubleToString(rates[i].close, digits),
                (long)rates[i].tick_volume,
                (long)rates[i].spread);
     }

   FileClose(fh);
   PrintFormat("เสร็จ: เขียน %d แท่ง (%s %s) -> MQL5\\Files\\%s",
               got, _Symbol, EnumToString(tf), outFile);
   PrintFormat("ช่วงที่ export จริง: %s -> %s (เวลาเซิร์ฟเวอร์)",
               TimeToString(rates[0].time, TIME_DATE|TIME_SECONDS),
               TimeToString(rates[got-1].time, TIME_DATE|TIME_SECONDS));
   Print("ถ้าต้องการหลาย timeframe (เช่น M5 สำหรับ execution + H1 สำหรับบริบท structure) "
         "ให้รันสคริปต์นี้ซ้ำโดยเปลี่ยน InpTF แล้วส่งไฟล์ทั้งหมดมาพร้อมกัน");
   if(got > 300000)
      Print("ไฟล์นี้ใหญ่ (>300k แถว) ควร zip ก่อนส่ง");
  }
//+------------------------------------------------------------------+
