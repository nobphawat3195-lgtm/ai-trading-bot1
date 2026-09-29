//+------------------------------------------------------------------+
//|                                            XAU_LadderGrid.mq5    |
//|   XAUUSD ตะแกรงหลายชั้น + TP ladder + เพดานความเสี่ยงแบบแข็ง       |
//|   สมมติฐาน H-GRID1  (docs/LADDER_GRID_HYPOTHESIS.md)             |
//|                                                                  |
//|  กฎ (ตรงกับ tools/ladder_grid_sim.py ที่มี unit test):            |
//|   1) เริ่ม basket เมื่อ Bid ยืดจาก EMA(แท่งปิด) เกิน N x ATR       |
//|      ขายสวนเมื่อยืดขึ้น / ซื้อสวนเมื่อยืดลง                        |
//|   2) ชั้น k เปิดเมื่อราคาสวนทางไป k x Step จาก anchor (ชั้นละครั้ง)  |
//|   3) แต่ละชั้นเปิดหลาย order ตาม TP ladder (ตัวคูณ x Step)         |
//|   4) basket stop = anchor +- ((MaxLevels-1) x Step + Buffer)      |
//|      ตั้งเป็น SL ที่โบรกให้ทุก order (EA ดับก็ยังมี SL)              |
//|   5) lot คำนวณจากขาดทุนสูงสุดตอนชน basket stop <= Risk%           |
//|      ถ้าต่ำกว่า lot ขั้นต่ำ -> ไม่เปิด (ไม่ปัดขึ้น)                  |
//|                                                                  |
//|  *** ยังไม่ได้ compile / backtest ใน MetaEditor ***               |
//|  *** ต้องใช้บัญชี HEDGING / ทดสอบเดโมก่อนเสมอ ***                  |
//|  *** ค่าเริ่มต้นปิดการเทรด (InpTradingEnabled=false) ***          |
//|  gap ทะลุ stop ขาดทุนเกินเพดานได้ (เพดานคำนวณจากราคา stop)         |
//+------------------------------------------------------------------+
//  ── ประวัติเวอร์ชัน ──
//  0.10 เวอร์ชันแรก
#property version   "0.10"
#property description "XAUUSD ladder grid: basket stop + risk-sized lot + hard caps"

#include <Trade/Trade.mqh>

enum ENUM_GRID_DIR { GRID_SELL_ONLY = 0, GRID_BUY_ONLY = 1, GRID_BOTH = 2 };

//=== เปิด/ปิด ===
input bool           InpTradingEnabled   = false;        // อนุญาตเปิด basket ใหม่ (ค่าเริ่มต้นปิด)
input long           InpMagic            = 26092902;     // Magic number
input ENUM_GRID_DIR  InpDirection        = GRID_BOTH;    // ทิศทางที่อนุญาต

//=== สัญญาณ (ใช้แท่งที่ปิดแล้วเท่านั้น) ===
input ENUM_TIMEFRAMES InpSignalTF        = PERIOD_M5;    // Timeframe ของ EMA/ATR
input int            InpEmaPeriod        = 100;          // EMA
input int            InpAtrPeriod        = 14;           // ATR
input double         InpStretchATR       = 2.0;          // เริ่ม basket เมื่อ Bid ห่างจาก EMA เกินกี่ ATR

//=== ตะแกรง (หน่วยดอลลาร์/ออนซ์) ===
input double         InpStepUSD          = 10.0;         // ระยะห่างระหว่างชั้น
input int            InpMaxLevels        = 3;            // จำนวนชั้นสูงสุด
input string         InpTpLadder         = "1,2,4";      // ตัวคูณ TP ต่อ order (x Step) จำนวนค่า = order ต่อชั้น
input double         InpStopBufferUSD    = 15.0;         // basket stop = เลยชั้นสุดท้ายอีกเท่านี้

//=== ขนาดไม้ / ความเสี่ยง ===
input double         InpFixedLot         = 0.0;          // 0 = คำนวณจาก Risk%  >0 = lot คงที่ต่อ order
input double         InpRiskPct          = 2.0;          // ขาดทุนสูงสุดเมื่อชน basket stop (% ของ equity)
input double         InpSlipUSD          = 0.5;          // เผื่อ slippage ต่อ order ($/oz) ในการคำนวณเพดาน

//=== เพดานแข็ง (ปรับเกินนี้ไม่ได้) ===
input double         InpHardBasketRiskPct = 10.0;        // ปฏิเสธถ้าขาดทุนสูงสุดต่อ basket เกิน % นี้ของ equity
input double         InpHardMaxLotPerOrder = 0.10;       // lot สูงสุดต่อ order
input double         InpHardMaxTotalLots  = 0.30;        // lot รวมของทั้ง basket
input double         InpDailyLossPct      = 3.0;         // ขาดทุนวันนี้เกิน % นี้ -> ปิดทั้งหมด + หยุดถึงวันถัดไป
input double         InpMaxDDPct          = 10.0;        // DD จาก peak เกิน % นี้ -> ปิดทั้งหมด + หยุดจนกว่าจะรีเซ็ต
input bool           InpResetHalt         = false;       // ตั้ง true แล้วโหลดใหม่ 1 ครั้งเพื่อล้างสถานะหยุด (แล้วตั้งกลับ false)

//=== ตัวกรอง ===
input int            InpMaxSpreadPts      = 60;          // ไม่เปิดไม้ถ้า spread เกินนี้ (points)
input int            InpCooldownSec       = 900;         // พักหลัง basket จบ ก่อนเริ่มอันใหม่
input int            InpStartHour         = 0;           // เริ่ม basket ใหม่ (ชั่วโมงเซิร์ฟเวอร์) ตรวจ timezone ด้วย BrokerProbe
input int            InpEndHour           = 24;          // จบ (ไม่รวมชั่วโมงนี้) 0-24 = ทั้งวัน
input int            InpDeviationPts      = 30;          // slippage ที่ยอมรับตอนส่งออเดอร์

#define MAX_LADDER 6

CTrade   trade;
double   g_ladder[MAX_LADDER];
int      g_nOrd        = 0;
int      g_hEma        = INVALID_HANDLE;
int      g_hAtr        = INVALID_HANDLE;
datetime g_lastRetry   = 0;
double   g_valPerUsdPerLot = 0;     // มูลค่า USD ต่อการขยับราคา $1 ต่อ 1 lot

//+------------------------------------------------------------------+
//| สถานะที่ต้องรอด restart เก็บใน GlobalVariables                    |
//+------------------------------------------------------------------+
string GvKey(const string n) { return StringFormat("XLG_%I64d_%I64d_%s", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, n); }
double GvGet(const string n, const double def) { string k = GvKey(n); return GlobalVariableCheck(k) ? GlobalVariableGet(k) : def; }
void   GvSet(const string n, const double v)   { GlobalVariableSet(GvKey(n), v); }
void   GvDel(const string n)                   { GlobalVariableDel(GvKey(n)); }

//+------------------------------------------------------------------+
//| ตัวช่วย                                                          |
//+------------------------------------------------------------------+
double StopDistance() { return (InpMaxLevels - 1) * InpStepUSD + InpStopBufferUSD; }

// ขาดทุนสูงสุดต่อ 1 lot (ต่อ order) ถ้าเปิดครบทุกชั้นแล้วชน basket stop
double WorstCasePerLot(const double spreadUsd)
  {
   double perOz = 0;
   for(int k = 0; k < InpMaxLevels; k++)
      perOz += g_nOrd * ((StopDistance() - k * InpStepUSD) + spreadUsd + InpSlipUSD);
   return perOz * g_valPerUsdPerLot;
  }

// lot ต่อ order  คืน 0 = ปฏิเสธ
double SizeLot(const double equity, const double spreadUsd)
  {
   double wc = WorstCasePerLot(spreadUsd);
   if(wc <= 0) return 0;
   double lot = (InpFixedLot > 0) ? InpFixedLot : equity * InpRiskPct / 100.0 / wc;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lot = MathMin(lot, MathMin(vmax, MathMin(InpHardMaxLotPerOrder, InpHardMaxTotalLots / (g_nOrd * InpMaxLevels))));
   lot = MathFloor(lot / step + 1e-9) * step;
   if(lot < vmin - 1e-12) return 0;
   if(lot * wc > equity * InpHardBasketRiskPct / 100.0) return 0;
   return NormalizeDouble(lot, 2);
  }

int CountPositions()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0 && PositionGetInteger(POSITION_MAGIC) == InpMagic
         && PositionGetString(POSITION_SYMBOL) == _Symbol) n++;
   return n;
  }

void CloseAll(const string why)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(!trade.PositionClose(tk))
         PrintFormat("XLG: ปิด #%I64u ไม่สำเร็จ retcode=%u %s", tk, trade.ResultRetcode(), trade.ResultRetcodeDescription());
     }
   PrintFormat("XLG: ปิดทั้งหมด (%s)", why);
  }

int DayKey(const datetime t) { MqlDateTime d; TimeToStruct(t, d); return d.year * 10000 + d.mon * 100 + d.day; }

bool InWindow()
  {
   MqlDateTime d;
   TimeToStruct(TimeCurrent(), d);
   return d.hour >= InpStartHour && d.hour < InpEndHour;
  }

//+------------------------------------------------------------------+
//| เพดานรายวัน / DD (halt: 0 ปกติ, 1 รายวัน, 2 DD)                    |
//+------------------------------------------------------------------+
void RiskUpdate()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   int today = DayKey(TimeCurrent());
   if((int)GvGet("day_key", 0) != today)
     {
      GvSet("day_key", today);
      GvSet("day_start_eq", eq);
      if((int)GvGet("halt", 0) == 1) GvSet("halt", 0);
     }
   double peak = GvGet("peak_eq", eq);
   if(eq > peak) { peak = eq; GvSet("peak_eq", peak); }
   if((int)GvGet("halt", 0) != 0) return;

   double ds = GvGet("day_start_eq", eq);
   int code = 0;
   if(InpDailyLossPct > 0 && ds > 0 && (ds - eq) / ds * 100.0 >= InpDailyLossPct)      code = 1;
   else if(InpMaxDDPct > 0 && peak > 0 && (peak - eq) / peak * 100.0 >= InpMaxDDPct)  code = 2;
   if(code == 0) return;
   GvSet("halt", code);
   PrintFormat("XLG: HALT %s equity=%.2f day_start=%.2f peak=%.2f", code == 1 ? "daily_loss" : "max_dd", eq, ds, peak);
   CloseAll(code == 1 ? "daily_loss" : "max_dd");
  }

//+------------------------------------------------------------------+
//| สถานะ basket (anchor / ทิศ / ชั้นล่าสุด)                            |
//+------------------------------------------------------------------+
bool HaveBasketState() { return GvGet("b_dir", 0) != 0; }

void ClearBasketState()
  {
   GvDel("b_dir"); GvDel("b_anchor"); GvDel("b_level"); GvDel("b_lot");
  }

// กรณี restart แล้วสถานะหาย แต่ยังมีไม้ค้าง: กู้ทิศ / anchor / ชั้น จากไม้ที่เหลือ
bool RecoverBasketState()
  {
   int dir = 0; double best = 0, worst = 0, lot = 0; bool first = true;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic || PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      int d = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL) ? -1 : 1;
      double px = PositionGetDouble(POSITION_PRICE_OPEN);
      lot = PositionGetDouble(POSITION_VOLUME);
      if(first) { dir = d; best = worst = px; first = false; }
      else
        {
         if(d == -1) { best = MathMin(best, px); worst = MathMax(worst, px); }
         else        { best = MathMax(best, px); worst = MathMin(worst, px); }
        }
     }
   if(first) return false;
   int level = (int)MathFloor(MathAbs(worst - best) / InpStepUSD + 0.5);
   GvSet("b_dir", dir); GvSet("b_anchor", best); GvSet("b_level", level); GvSet("b_lot", lot);
   PrintFormat("XLG: กู้สถานะ basket dir=%d anchor=%.2f level=%d (ถ้า anchor ผิด ให้ปิดมือแล้วเริ่มใหม่)", dir, best, level);
   return true;
  }

//+------------------------------------------------------------------+
//| เปิด order ของหนึ่งชั้น                                            |
//+------------------------------------------------------------------+
int OpenLevel(const int dir, const double entryRef, const double sl, const double lot, const int level)
  {
   long stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist = (stopLevel + SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)) * _Point;
   int ok = 0;
   for(int i = 0; i < g_nOrd; i++)
     {
      double tpDist = g_ladder[i] * InpStepUSD;
      if(tpDist < minDist) { PrintFormat("XLG: TP ladder[%d] แคบกว่า stop level ข้าม", i); continue; }
      double tp = NormalizeDouble(entryRef + dir * tpDist, _Digits);
      double slN = NormalizeDouble(sl, _Digits);
      bool sent = (dir > 0) ? trade.Buy(lot, _Symbol, 0.0, slN, tp, StringFormat("XLG L%d", level))
                            : trade.Sell(lot, _Symbol, 0.0, slN, tp, StringFormat("XLG L%d", level));
      if(sent) ok++;
      else PrintFormat("XLG: เปิดไม่สำเร็จ L%d retcode=%u %s", level, trade.ResultRetcode(), trade.ResultRetcodeDescription());
     }
   return ok;
  }

//+------------------------------------------------------------------+
//| จัดการ basket ที่เปิดอยู่: เปิดชั้นถัดไป                           |
//+------------------------------------------------------------------+
void ManageBasket(const double bid, const double ask)
  {
   int dir = (int)GvGet("b_dir", 0);
   double anchor = GvGet("b_anchor", 0);
   int level = (int)GvGet("b_level", 0);
   double lot = GvGet("b_lot", 0);
   if(dir == 0 || anchor <= 0 || lot <= 0) return;
   double sl = anchor - dir * StopDistance();

   // basket stop ฝั่ง EA (เผื่อ SL ที่โบรกถูกแก้/ลบ)
   if((dir == -1 && ask >= sl) || (dir == 1 && bid <= sl)) { CloseAll("basket_stop"); return; }

   int next = level + 1;
   if(next > InpMaxLevels - 1) return;
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPts) return;
   if(TimeCurrent() - g_lastRetry < 2) return;

   double entry = (dir == -1) ? bid : ask;
   bool trig = (dir == -1) ? (bid >= anchor + next * InpStepUSD && bid < sl)
                           : (ask <= anchor - next * InpStepUSD && ask > sl);
   if(!trig) return;
   g_lastRetry = TimeCurrent();
   if(OpenLevel(dir, entry, sl, lot, next) > 0) GvSet("b_level", next);
  }

//+------------------------------------------------------------------+
//| เริ่ม basket ใหม่                                                 |
//+------------------------------------------------------------------+
void TryStartBasket(const double bid, const double ask)
  {
   if(!InpTradingEnabled) return;
   if((int)GvGet("halt", 0) != 0) return;
   if(!InWindow()) return;
   if(TimeCurrent() < (datetime)GvGet("cooldown_until", 0)) return;
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPts) return;
   if(TimeCurrent() - g_lastRetry < 2) return;

   double ema[1], atr[1];
   if(CopyBuffer(g_hEma, 0, 1, 1, ema) != 1 || CopyBuffer(g_hAtr, 0, 1, 1, atr) != 1) return;   // shift 1 = แท่งที่ปิดแล้ว
   if(atr[0] <= 0) return;

   int dir = 0;
   if(InpDirection != GRID_BUY_ONLY  && bid >= ema[0] + InpStretchATR * atr[0]) dir = -1;
   else if(InpDirection != GRID_SELL_ONLY && bid <= ema[0] - InpStretchATR * atr[0]) dir = 1;
   if(dir == 0) return;

   double spreadUsd = ask - bid;
   double lot = SizeLot(AccountInfoDouble(ACCOUNT_EQUITY), spreadUsd);
   if(lot <= 0)
     {
      static datetime lastMsg = 0;
      if(TimeCurrent() - lastMsg > 3600)
        {
         lastMsg = TimeCurrent();
         PrintFormat("XLG: ปฏิเสธ basket: ขาดทุนสูงสุดที่ lot ขั้นต่ำ ~ %.2f USD ต้องมี equity ~ %.0f เพื่อเสี่ยง %.1f%% (equity ตอนนี้ %.0f)",
                     WorstCasePerLot(spreadUsd) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                     WorstCasePerLot(spreadUsd) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN) / (InpRiskPct / 100.0),
                     InpRiskPct, AccountInfoDouble(ACCOUNT_EQUITY));
        }
      return;
     }

   double entry = (dir == -1) ? bid : ask;
   double sl = entry - dir * StopDistance();
   g_lastRetry = TimeCurrent();
   if(OpenLevel(dir, entry, sl, lot, 0) > 0)
     {
      GvSet("b_dir", dir); GvSet("b_anchor", entry); GvSet("b_level", 0); GvSet("b_lot", lot);
      PrintFormat("XLG: เริ่ม basket dir=%d anchor=%.2f lot=%.2f/order stop=%.2f", dir, entry, lot, sl);
     }
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     { Print("XLG: ต้องใช้บัญชี HEDGING เท่านั้น"); return INIT_FAILED; }

   string parts[];
   int n = StringSplit(InpTpLadder, ',', parts);
   g_nOrd = 0;
   for(int i = 0; i < n && g_nOrd < MAX_LADDER; i++)
     {
      double v = StringToDouble(parts[i]);
      if(v > 0) g_ladder[g_nOrd++] = v;
     }
   if(g_nOrd == 0) { Print("XLG: InpTpLadder ไม่ถูกต้อง"); return INIT_PARAMETERS_INCORRECT; }
   if(InpMaxLevels < 1 || InpStepUSD <= 0 || InpStopBufferUSD <= 0)
     { Print("XLG: Step / MaxLevels / Buffer ต้องมากกว่า 0"); return INIT_PARAMETERS_INCORRECT; }

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickValue <= 0 || tickSize <= 0) { Print("XLG: อ่าน tick value/size ไม่ได้"); return INIT_FAILED; }
   g_valPerUsdPerLot = tickValue / tickSize;    // XAUUSD ปกติ = 100

   long stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   if(InpStopBufferUSD < (stopLevel + InpMaxSpreadPts) * _Point)
     { Print("XLG: StopBuffer แคบกว่า stop level + spread"); return INIT_PARAMETERS_INCORRECT; }

   g_hEma = iMA(_Symbol, InpSignalTF, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_hAtr = iATR(_Symbol, InpSignalTF, InpAtrPeriod);
   if(g_hEma == INVALID_HANDLE || g_hAtr == INVALID_HANDLE) { Print("XLG: สร้าง indicator ไม่สำเร็จ"); return INIT_FAILED; }

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpDeviationPts);
   trade.SetTypeFillingBySymbol(_Symbol);

   if(InpResetHalt) { GvSet("halt", 0); GvSet("peak_eq", AccountInfoDouble(ACCOUNT_EQUITY)); Print("XLG: ล้างสถานะหยุดแล้ว (อย่าลืมตั้ง InpResetHalt กลับเป็น false)"); }

   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double wcMin = WorstCasePerLot(0.3) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   PrintFormat("XLG: step=%.1f levels=%d orders/level=%d stop=%.1f | ขาดทุนสูงสุดที่ lot ขั้นต่ำ ~ %.2f USD (%.1f%% ของ equity %.0f)",
               InpStepUSD, InpMaxLevels, g_nOrd, StopDistance(), wcMin, wcMin / eq * 100.0, eq);
   if(SizeLot(eq, 0.3) <= 0)
      PrintFormat("XLG: คำเตือน: ด้วย equity นี้จะไม่เปิด basket (ต้อง ~%.0f เพื่อเสี่ยง %.1f%%) ลดชั้น/order หรือเพิ่มทุน", wcMin / (InpRiskPct / 100.0), InpRiskPct);
   if(!InpTradingEnabled) Print("XLG: InpTradingEnabled = false (ยังไม่เปิดเทรด)");

   RiskUpdate();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_hEma != INVALID_HANDLE) IndicatorRelease(g_hEma);
   if(g_hAtr != INVALID_HANDLE) IndicatorRelease(g_hAtr);
   Comment("");
  }

void OnTick()
  {
   RiskUpdate();
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(bid <= 0 || ask <= 0) return;

   int pos = CountPositions();
   if(pos > 0)
     {
      if(!HaveBasketState() && !RecoverBasketState()) return;
      ManageBasket(bid, ask);
     }
   else
     {
      if(HaveBasketState())            // basket จบแล้ว (TP/SL ครบ) -> ล้างสถานะ + พัก
        {
         ClearBasketState();
         GvSet("cooldown_until", (double)(TimeCurrent() + InpCooldownSec));
        }
      TryStartBasket(bid, ask);
     }
  }
//+------------------------------------------------------------------+
