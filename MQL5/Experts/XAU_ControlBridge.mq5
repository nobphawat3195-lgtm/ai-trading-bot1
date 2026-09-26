//+------------------------------------------------------------------+
//|                                        XAU_ControlBridge.mq5     |
//|   EA ควบคุมความเสี่ยง + ส่งข้อมูลขึ้นเว็บ (bridge/app.py)          |
//|                                                                  |
//|  หลักการ: EA เป็นผู้ตัดสินใจทั้งหมด เว็บทำได้แค่                  |
//|   - ส่ง config (EA clamp ด้วย hard limit ของตัวเองอีกชั้น)         |
//|   - ส่งคำสั่ง PAUSE / RESUME / CLOSE_ALL                          |
//|  เว็บล่ม / เน็ตหลุด -> EA เข้าโหมดปลอดภัย (ไม่เปิดไม้ใหม่)          |
//|  ทุก request/response เซ็นด้วย HMAC-SHA256 กันปลอมคำสั่ง          |
//|                                                                  |
//|  ตั้งค่า MT5: Tools > Options > Expert Advisors >                  |
//|   ติ๊ก "Allow WebRequest for listed URL" แล้วใส่ URL ของ backend   |
//|  ใน Strategy Tester: bridge ปิดอัตโนมัติ (WebRequest ใช้ไม่ได้)    |
//|  แต่ risk guard ยังทำงาน                                          |
//|                                                                  |
//|  StrategySignal() ยังเป็น stub (คืน 0 เสมอ) ตั้งใจไม่ใส่กลยุทธ์     |
//|  จนกว่า baseline ของ THAOFORAX จะผ่าน (ดู RESEARCH_STATE.md)       |
//+------------------------------------------------------------------+
//  ── ประวัติเวอร์ชัน ──
//  0.10 เวอร์ชันแรก: sync + HMAC + risk guard + PAUSE/RESUME/CLOSE_ALL
#property version   "0.10"
#property description "XAUUSD control bridge: risk guard + signed web telemetry"

#include <Trade/Trade.mqh>

#define EA_VERSION        "0.10"
#define MAX_CLOCK_SKEW    120
#define MAX_DEALS_PER_SYNC 100
#define DONE_RING         32

//=== การเชื่อมต่อเว็บ ===
input string InpBridgeUrl       = "http://127.0.0.1:8765/v1/ea/sync"; // URL backend (ว่าง = ไม่ใช้เว็บ)
input string InpSecret          = "";      // Secret ของบัญชีนี้ (>= 32 ตัวอักษร ตรงกับ BRIDGE_SECRETS)
input int    InpPollSec         = 3;       // Sync ทุกกี่วินาที
input int    InpWebTimeoutMs    = 3000;    // Timeout ต่อ request (ms)
input int    InpOfflineSec      = 60;      // ขาดการติดต่อเกินนี้ -> โหมดปลอดภัย (ไม่เปิดไม้ใหม่)
input int    InpHistoryDays     = 30;      // ครั้งแรกส่ง deal ย้อนหลังกี่วัน
input long   InpMagic           = 26092601;// Magic number

//=== Hard limit (เว็บตั้งเกินนี้ไม่ได้ ไม่ว่ากรณีใด) ===
input double InpHardMaxLot        = 0.10;  // Lot สูงสุดต่อไม้
input double InpHardRiskPct       = 1.0;   // Risk ต่อไม้สูงสุด (% equity)
input double InpHardDailyLossPct  = 5.0;   // ขาดทุนต่อวันสูงสุด (%)
input double InpHardMaxDDPct      = 20.0;  // DD จาก peak สูงสุด (%)
input int    InpHardMaxPositions  = 3;     // จำนวนไม้พร้อมกันสูงสุด
input int    InpHardMaxSpreadPts  = 80;    // Spread สูงสุด (points)
input bool   InpCloseAllOnHalt    = true;  // ชน daily loss / DD แล้วปิดทุกไม้ของ EA

//=== ค่าเริ่มต้น (config v0 ใช้จนกว่าเว็บจะส่งเวอร์ชันใหม่) ===
input bool   InpTradingEnabled  = false;   // อนุญาตเปิดไม้ใหม่
input double InpRiskPct         = 0.5;     // Risk ต่อไม้ (%)
input double InpDailyLossPct    = 3.0;     // หยุดเมื่อขาดทุนวันนี้เกิน (%)
input double InpMaxDDPct        = 10.0;    // หยุดเมื่อ DD จาก peak เกิน (%)
input int    InpMaxPositions    = 1;       // ไม้พร้อมกันสูงสุด
input int    InpMaxSpreadPts    = 40;      // ไม่เปิดไม้ถ้า spread เกิน (points)
input int    InpMinEntryGapSec  = 60;      // เว้นระยะระหว่างไม้ใหม่ (กันเปิดซ้ำ)

struct Cfg
  {
   int      version;
   bool     trading_enabled;
   double   risk_pct;
   double   daily_loss_pct;
   double   max_dd_pct;
   int      max_positions;
   int      max_spread_pts;
   int      min_entry_gap_sec;
  };

struct Ack
  {
   string   id;
   bool     ok;
   string   msg;
  };

CTrade   trade;
Cfg      g_cfg;
Ack      g_acks[];
string   g_done[DONE_RING];
int      g_doneIdx      = 0;
bool     g_bridgeOn     = false;
datetime g_lastOkSync   = 0;   // เวลาเครื่อง (TimeLocal) ของ sync ที่สำเร็จล่าสุด
datetime g_lastAttempt  = 0;
datetime g_startTime    = 0;
string   g_lastError    = "";
bool     g_busy         = false;

//+------------------------------------------------------------------+
//| GlobalVariables: เก็บสถานะ risk ให้รอด restart                    |
//+------------------------------------------------------------------+
string GvKey(const string name)
  {
   return StringFormat("XCB_%I64d_%I64d_%s", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, name);
  }
double GvGet(const string name, const double def)
  {
   string k = GvKey(name);
   return GlobalVariableCheck(k) ? GlobalVariableGet(k) : def;
  }
void GvSet(const string name, const double v) { GlobalVariableSet(GvKey(name), v); }

//+------------------------------------------------------------------+
//| HMAC-SHA256 (MQL5 มีแค่ SHA256 ผ่าน CryptEncode จึงประกอบเอง)     |
//+------------------------------------------------------------------+
void StrBytes(const string s, uchar &out[])
  {
   int n = StringToCharArray(s, out, 0, WHOLE_ARRAY, CP_UTF8);
   ArrayResize(out, MathMax(0, n - 1));   // ตัด null terminator
  }

bool Sha256(const uchar &data[], uchar &out[])
  {
   uchar nokey[];
   return CryptEncode(CRYPT_HASH_SHA256, data, nokey, out) == 32;
  }

string HmacSha256Hex(const string key, const string msg)
  {
   uchar k[], m[];
   StrBytes(key, k);
   StrBytes(msg, m);
   if(ArraySize(k) > 64)
     {
      uchar hk[];
      if(!Sha256(k, hk)) return "";
      ArrayFree(k);
      ArrayCopy(k, hk);
     }
   int klen = ArraySize(k);
   ArrayResize(k, 64);
   for(int i = klen; i < 64; i++) k[i] = 0;

   int mlen = ArraySize(m);
   uchar inner[];
   ArrayResize(inner, 64 + mlen);
   for(int i = 0; i < 64; i++) inner[i] = (uchar)(k[i] ^ 0x36);
   for(int i = 0; i < mlen; i++) inner[64 + i] = m[i];
   uchar ih[];
   if(!Sha256(inner, ih)) return "";

   uchar outer[];
   ArrayResize(outer, 64 + 32);
   for(int i = 0; i < 64; i++) outer[i] = (uchar)(k[i] ^ 0x5c);
   for(int i = 0; i < 32; i++) outer[64 + i] = ih[i];
   uchar oh[];
   if(!Sha256(outer, oh)) return "";

   string hex = "";
   for(int i = 0; i < 32; i++) hex += StringFormat("%02x", oh[i]);
   return hex;
  }

//+------------------------------------------------------------------+
//| Config                                                           |
//+------------------------------------------------------------------+
void ClampCfg(Cfg &c)
  {
   c.risk_pct          = MathMax(0.0, MathMin(c.risk_pct, InpHardRiskPct));
   c.daily_loss_pct    = MathMax(0.1, MathMin(c.daily_loss_pct, InpHardDailyLossPct));
   c.max_dd_pct        = MathMax(0.5, MathMin(c.max_dd_pct, InpHardMaxDDPct));
   c.max_positions     = (int)MathMax(0, MathMin(c.max_positions, InpHardMaxPositions));
   c.max_spread_pts    = (int)MathMax(0, MathMin(c.max_spread_pts, InpHardMaxSpreadPts));
   c.min_entry_gap_sec = (int)MathMax(0, c.min_entry_gap_sec);
  }

void DefaultCfg()
  {
   g_cfg.version           = 0;
   g_cfg.trading_enabled   = InpTradingEnabled;
   g_cfg.risk_pct          = InpRiskPct;
   g_cfg.daily_loss_pct    = InpDailyLossPct;
   g_cfg.max_dd_pct        = InpMaxDDPct;
   g_cfg.max_positions     = InpMaxPositions;
   g_cfg.max_spread_pts    = InpMaxSpreadPts;
   g_cfg.min_entry_gap_sec = InpMinEntryGapSec;
   ClampCfg(g_cfg);
  }

// "CFG <version> k=v|k=v|..."  -> ค่าที่ไม่รู้จักถูกข้าม, ค่าที่ขาดใช้ค่าเดิม
void ApplyCfgLine(const string line)
  {
   string parts[];
   if(StringSplit(line, ' ', parts) < 3) return;
   Cfg c = g_cfg;
   c.version = (int)StringToInteger(parts[1]);
   string pairs[];
   int n = StringSplit(parts[2], '|', pairs);
   for(int i = 0; i < n; i++)
     {
      string kv[];
      if(StringSplit(pairs[i], '=', kv) != 2) continue;
      string k = kv[0];
      double v = StringToDouble(kv[1]);
      if(k == "trading_enabled")        c.trading_enabled   = (v >= 0.5);
      else if(k == "risk_pct")          c.risk_pct          = v;
      else if(k == "daily_loss_pct")    c.daily_loss_pct    = v;
      else if(k == "max_dd_pct")        c.max_dd_pct        = v;
      else if(k == "max_positions")     c.max_positions     = (int)v;
      else if(k == "max_spread_pts")    c.max_spread_pts    = (int)v;
      else if(k == "min_entry_gap_sec") c.min_entry_gap_sec = (int)v;
     }
   ClampCfg(c);
   g_cfg = c;
   PrintFormat("XCB: ใช้ config v%d (trading=%s risk=%.2f%% daily=%.2f%% dd=%.2f%% pos=%d spread=%d gap=%ds)",
               c.version, c.trading_enabled ? "on" : "off", c.risk_pct, c.daily_loss_pct, c.max_dd_pct,
               c.max_positions, c.max_spread_pts, c.min_entry_gap_sec);
  }

//+------------------------------------------------------------------+
//| Risk guard                                                       |
//+------------------------------------------------------------------+
// halt codes: 0 = ปกติ, 1 = daily loss, 2 = max DD
string HaltReason(const int code)
  {
   if(code == 1) return "daily_loss";
   if(code == 2) return "max_dd";
   return "";
  }

int DayKey(const datetime t)
  {
   MqlDateTime d;
   TimeToStruct(t, d);
   return d.year * 10000 + d.mon * 100 + d.day;
  }

int CountMyPositions()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0 && PositionGetInteger(POSITION_MAGIC) == InpMagic) n++;
   return n;
  }

int CloseMyPositions(int &failed)
  {
   int closed = 0;
   failed = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      if(trade.PositionClose(ticket)) closed++;
      else
        {
         failed++;
         PrintFormat("XCB: ปิด #%I64u ไม่สำเร็จ retcode=%u %s", ticket, trade.ResultRetcode(),
                     trade.ResultRetcodeDescription());
        }
     }
   return closed;
  }

void RiskUpdate()
  {
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   int today = DayKey(TimeCurrent());
   if((int)GvGet("day_key", 0) != today)
     {
      GvSet("day_key", today);
      GvSet("day_start_eq", equity);
      if((int)GvGet("halt", 0) == 1) GvSet("halt", 0);   // daily halt หมดอายุเมื่อขึ้นวันใหม่
     }
   double peak = GvGet("peak_eq", equity);
   if(equity > peak) { peak = equity; GvSet("peak_eq", peak); }

   if((int)GvGet("halt", 0) != 0) return;
   double dayStart = GvGet("day_start_eq", equity);
   int code = 0;
   if(dayStart > 0 && (dayStart - equity) / dayStart * 100.0 >= g_cfg.daily_loss_pct) code = 1;
   else if(peak > 0 && (peak - equity) / peak * 100.0 >= g_cfg.max_dd_pct) code = 2;
   if(code == 0) return;

   GvSet("halt", code);
   PrintFormat("XCB: HALT %s equity=%.2f day_start=%.2f peak=%.2f", HaltReason(code), equity, dayStart, peak);
   if(InpCloseAllOnHalt)
     {
      int failed;
      CloseMyPositions(failed);
     }
  }

bool IsOffline()
  {
   if(!g_bridgeOn) return false;
   datetime since = (g_lastOkSync > 0) ? g_lastOkSync : g_startTime;
   return (TimeLocal() - since) > InpOfflineSec;
  }

bool RiskAllowsEntry(string &why)
  {
   if(!g_cfg.trading_enabled)                    { why = "trading disabled"; return false; }
   if(GvGet("paused", 0) > 0)                    { why = "paused";           return false; }
   int halt = (int)GvGet("halt", 0);
   if(halt != 0)                                 { why = "halt " + HaltReason(halt); return false; }
   if(IsOffline())                               { why = "bridge offline";   return false; }
   if(CountMyPositions() >= g_cfg.max_positions) { why = "max positions";    return false; }
   long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread > g_cfg.max_spread_pts)             { why = StringFormat("spread %d", (int)spread); return false; }
   if(TimeCurrent() - (datetime)GvGet("last_entry", 0) < g_cfg.min_entry_gap_sec)
                                                 { why = "entry gap";        return false; }
   return true;
  }

// คำนวณ lot จาก risk% และระยะ SL ถ้าได้ต่ำกว่า lot ขั้นต่ำ -> คืน 0 (ไม่ปัดขึ้นให้เสี่ยงเกิน)
double RiskLot(const double slPoints)
  {
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(slPoints <= 0 || tickValue <= 0 || tickSize <= 0) return 0;
   double lossPerLot = slPoints * _Point / tickSize * tickValue;
   double lot = AccountInfoDouble(ACCOUNT_EQUITY) * g_cfg.risk_pct / 100.0 / lossPerLot;

   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = MathMin(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), InpHardMaxLot);
   lot = MathFloor(lot / step) * step;
   lot = MathMin(lot, vmax);
   if(lot < vmin) return 0;
   return NormalizeDouble(lot, 2);
  }

// dir: +1 buy, -1 sell
bool OpenPosition(const int dir, const double slPoints, const double tpPoints)
  {
   string why;
   if(!RiskAllowsEntry(why)) { PrintFormat("XCB: ไม่เปิดไม้: %s", why); return false; }
   long stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   if(slPoints < stopLevel || (tpPoints > 0 && tpPoints < stopLevel))
     { PrintFormat("XCB: SL/TP แคบกว่า stop level (%d)", (int)stopLevel); return false; }
   double lot = RiskLot(slPoints);
   if(lot <= 0) { Print("XCB: lot ตาม risk% ต่ำกว่าขั้นต่ำของโบรก -> ไม่เปิด"); return false; }

   bool ok;
   if(dir > 0)
     {
      double p = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      ok = trade.Buy(lot, _Symbol, p, p - slPoints * _Point, tpPoints > 0 ? p + tpPoints * _Point : 0, "XCB");
     }
   else
     {
      double p = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      ok = trade.Sell(lot, _Symbol, p, p + slPoints * _Point, tpPoints > 0 ? p - tpPoints * _Point : 0, "XCB");
     }
   if(ok) GvSet("last_entry", (double)TimeCurrent());
   return ok;
  }

//+------------------------------------------------------------------+
//| กลยุทธ์: stub                                                    |
//|  คืน +1 / -1 / 0 และกำหนด slPts/tpPts                             |
//|  จะใส่ logic จริงหลัง baseline + OOS ผ่านตาม CLAUDE.md เท่านั้น     |
//+------------------------------------------------------------------+
int StrategySignal(double &slPts, double &tpPts)
  {
   slPts = 0;
   tpPts = 0;
   return 0;
  }

//+------------------------------------------------------------------+
//| JSON (ส่งเฉพาะ ASCII เพื่อให้ byte ที่เซ็นตรงกับที่ส่งแน่นอน)       |
//+------------------------------------------------------------------+
string JsonStr(const string s)
  {
   string out = "\"";
   int n = StringLen(s);
   for(int i = 0; i < n; i++)
     {
      ushort c = StringGetCharacter(s, i);
      if(c == '"' || c == '\\') out += "\\" + ShortToString(c);
      else if(c < 32 || c > 126) out += "?";
      else out += ShortToString(c);
     }
   return out + "\"";
  }

string Num(const double v, const int digits) { return DoubleToString(v, digits); }

string DealEntryText(const long e)
  {
   if(e == DEAL_ENTRY_IN)    return "in";
   if(e == DEAL_ENTRY_OUT)   return "out";
   if(e == DEAL_ENTRY_INOUT) return "inout";
   return "out_by";
  }

// ดึง deal ที่ยังไม่ได้ส่ง เรียงตามเวลา ไม่เกิน MAX_DEALS_PER_SYNC
// คืน JSON array และ cursor ใหม่ (commit หลัง HTTP 200 เท่านั้น)
string CollectDeals(long &newMsc, ulong &newTicket)
  {
   long  curMsc    = (long)GvGet("deal_msc", (double)((long)(TimeCurrent() - InpHistoryDays * 86400) * 1000));
   ulong curTicket = (ulong)GvGet("deal_ticket", 0);
   newMsc = curMsc;
   newTicket = curTicket;
   if(!HistorySelect((datetime)(curMsc / 1000) - 1, TimeCurrent() + 86400)) return "[]";

   int total = HistoryDealsTotal();
   ulong tickets[];
   long  mscs[];
   int   n = 0;
   for(int i = 0; i < total; i++)
     {
      ulong t = HistoryDealGetTicket(i);
      if(t == 0) continue;
      long type = HistoryDealGetInteger(t, DEAL_TYPE);
      if(type != DEAL_TYPE_BUY && type != DEAL_TYPE_SELL) continue;
      long msc = HistoryDealGetInteger(t, DEAL_TIME_MSC);
      if(msc < curMsc || (msc == curMsc && t <= curTicket)) continue;
      ArrayResize(tickets, n + 1);
      ArrayResize(mscs, n + 1);
      // insertion sort ตาม (msc, ticket)
      int j = n - 1;
      while(j >= 0 && (mscs[j] > msc || (mscs[j] == msc && tickets[j] > t)))
        { mscs[j + 1] = mscs[j]; tickets[j + 1] = tickets[j]; j--; }
      mscs[j + 1] = msc;
      tickets[j + 1] = t;
      n++;
     }

   string out = "[";
   int take = MathMin(n, MAX_DEALS_PER_SYNC);
   for(int i = 0; i < take; i++)
     {
      ulong t = tickets[i];
      if(i > 0) out += ",";
      out += StringFormat("{\"ticket\":%I64u,\"position_id\":%I64d,\"symbol\":%s,\"type\":%s,\"entry\":%s,"
                          "\"volume\":%s,\"price\":%s,\"profit\":%s,\"commission\":%s,\"swap\":%s,"
                          "\"time\":%I64d,\"config_version\":%d}",
                          t, HistoryDealGetInteger(t, DEAL_POSITION_ID),
                          JsonStr(HistoryDealGetString(t, DEAL_SYMBOL)),
                          JsonStr(HistoryDealGetInteger(t, DEAL_TYPE) == DEAL_TYPE_BUY ? "buy" : "sell"),
                          JsonStr(DealEntryText(HistoryDealGetInteger(t, DEAL_ENTRY))),
                          Num(HistoryDealGetDouble(t, DEAL_VOLUME), 2),
                          Num(HistoryDealGetDouble(t, DEAL_PRICE), 5),
                          Num(HistoryDealGetDouble(t, DEAL_PROFIT), 2),
                          Num(HistoryDealGetDouble(t, DEAL_COMMISSION), 2),
                          Num(HistoryDealGetDouble(t, DEAL_SWAP), 2),
                          (long)HistoryDealGetInteger(t, DEAL_TIME),
                          g_cfg.version);   // เวอร์ชันตอนส่ง (deal ส่งภายในไม่กี่วินาทีหลังเกิด)
      newMsc = mscs[i];
      newTicket = t;
     }
   return out + "]";
  }

string BuildBody(long &newMsc, ulong &newTicket)
  {
   string pos = "[";
   int np = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(np++ > 0) pos += ",";
      pos += StringFormat("{\"ticket\":%I64u,\"symbol\":%s,\"type\":%s,\"volume\":%s,\"price_open\":%s,"
                          "\"sl\":%s,\"tp\":%s,\"profit\":%s,\"magic\":%I64d,\"time\":%I64d}",
                          t, JsonStr(PositionGetString(POSITION_SYMBOL)),
                          JsonStr(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell"),
                          Num(PositionGetDouble(POSITION_VOLUME), 2), Num(PositionGetDouble(POSITION_PRICE_OPEN), 5),
                          Num(PositionGetDouble(POSITION_SL), 5), Num(PositionGetDouble(POSITION_TP), 5),
                          Num(PositionGetDouble(POSITION_PROFIT), 2), PositionGetInteger(POSITION_MAGIC),
                          (long)PositionGetInteger(POSITION_TIME));
     }
   pos += "]";

   string acks = "[";
   for(int i = 0; i < ArraySize(g_acks); i++)
     {
      if(i > 0) acks += ",";
      acks += StringFormat("{\"id\":%s,\"ok\":%s,\"msg\":%s}", JsonStr(g_acks[i].id),
                           g_acks[i].ok ? "true" : "false", JsonStr(g_acks[i].msg));
     }
   acks += "]";

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   int halt = (int)GvGet("halt", 0);
   string risk = StringFormat("{\"halted\":%s,\"reason\":%s,\"paused\":%s,\"offline\":%s,\"day_pnl\":%s,"
                              "\"day_start_equity\":%s,\"peak_equity\":%s}",
                              halt != 0 ? "true" : "false", JsonStr(HaltReason(halt)),
                              GvGet("paused", 0) > 0 ? "true" : "false", IsOffline() ? "true" : "false",
                              Num(equity - GvGet("day_start_eq", equity), 2),
                              Num(GvGet("day_start_eq", equity), 2), Num(GvGet("peak_eq", equity), 2));

   return StringFormat("{\"account\":%I64d,\"server\":%s,\"magic\":%I64d,\"ea_version\":%s,\"config_version\":%d,"
                       "\"symbol\":%s,\"balance\":%s,\"equity\":%s,\"margin_free\":%s,\"spread_pts\":%d,"
                       "\"positions\":%s,\"deals\":%s,\"acks\":%s,\"risk\":%s}",
                       AccountInfoInteger(ACCOUNT_LOGIN), JsonStr(AccountInfoString(ACCOUNT_SERVER)), InpMagic,
                       JsonStr(EA_VERSION), g_cfg.version, JsonStr(_Symbol),
                       Num(AccountInfoDouble(ACCOUNT_BALANCE), 2), Num(equity, 2),
                       Num(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2),
                       (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD),
                       pos, CollectDeals(newMsc, newTicket), acks, risk);
  }

//+------------------------------------------------------------------+
//| คำสั่งจากเว็บ (ทุกคำสั่ง idempotent: ส่งซ้ำก็ได้ผลเหมือนเดิม)       |
//+------------------------------------------------------------------+
bool AlreadyDone(const string id)
  {
   for(int i = 0; i < DONE_RING; i++) if(g_done[i] == id) return true;
   return false;
  }

void QueueAck(const string id, const bool ok, const string msg)
  {
   int n = ArraySize(g_acks);
   ArrayResize(g_acks, n + 1);
   g_acks[n].id = id;
   g_acks[n].ok = ok;
   g_acks[n].msg = msg;
  }

void ExecuteCommand(const string id, const string type)
  {
   if(AlreadyDone(id)) { QueueAck(id, true, "duplicate"); return; }
   g_done[g_doneIdx] = id;
   g_doneIdx = (g_doneIdx + 1) % DONE_RING;

   if(type == "PAUSE")
     {
      GvSet("paused", 1);
      QueueAck(id, true, "paused");
     }
   else if(type == "RESUME")
     {
      // RESUME = คนตัดสินใจแล้ว: ล้าง pause + halt และตั้ง peak ใหม่ที่ equity ปัจจุบัน
      // (daily loss จะ halt ซ้ำทันทีถ้ายังเกินเกณฑ์ของวันนี้)
      GvSet("paused", 0);
      GvSet("halt", 0);
      GvSet("peak_eq", AccountInfoDouble(ACCOUNT_EQUITY));
      QueueAck(id, true, "resumed");
     }
   else if(type == "CLOSE_ALL")
     {
      GvSet("paused", 1);   // ปุ่มฉุกเฉิน: ปิดแล้วต้องไม่เปิดใหม่เองจนกว่าจะ RESUME
      int failed;
      int closed = CloseMyPositions(failed);
      QueueAck(id, failed == 0, StringFormat("closed %d failed %d, paused", closed, failed));
     }
   else QueueAck(id, false, "unknown command");
   PrintFormat("XCB: คำสั่ง %s (%s)", type, id);
  }

// ตรวจลายเซ็นก่อน แล้วค่อยทำตาม ถ้าไม่ผ่านทิ้งทั้ง response
bool HandleResponse(const string response)
  {
   string lines[];
   int n = StringSplit(response, '\n', lines);
   string payload = "", sig = "";
   int count = 0;
   for(int i = 0; i < n; i++)
     {
      string line = lines[i];
      StringTrimRight(line);
      if(StringLen(line) == 0) continue;
      if(StringFind(line, "SIG ") == 0) { sig = StringSubstr(line, 4); break; }
      payload += (count++ > 0 ? "\n" : "") + line;
     }
   if(sig == "" || HmacSha256Hex(InpSecret, payload) != sig)
     { g_lastError = "response signature invalid"; return false; }

   string pl[];
   int m = StringSplit(payload, '\n', pl);
   if(m < 1 || StringFind(pl[0], "OK ") != 0) { g_lastError = "bad response"; return false; }
   long serverTs = StringToInteger(StringSubstr(pl[0], 3));
   if(MathAbs((double)(serverTs - (long)TimeGMT())) > MAX_CLOCK_SKEW)
     { g_lastError = "response too old / clock skew"; return false; }

   for(int i = 1; i < m; i++)
     {
      if(StringFind(pl[i], "CFG ") == 0) ApplyCfgLine(pl[i]);
      else if(StringFind(pl[i], "CMD ") == 0)
        {
         string p[];
         if(StringSplit(pl[i], ' ', p) == 3) ExecuteCommand(p[1], p[2]);
        }
     }
   return true;
  }

void DoSync()
  {
   long newMsc;
   ulong newTicket;
   int acksSent = ArraySize(g_acks);
   string body = BuildBody(newMsc, newTicket);

   string ts = IntegerToString((long)TimeGMT());
   string nonce = StringFormat("%I64u%05d%05d", GetMicrosecondCount(), MathRand(), MathRand());
   string sig = HmacSha256Hex(InpSecret, ts + "\n" + nonce + "\n" + body);
   string headers = "Content-Type: application/json\r\n"
                    "X-Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\r\n"
                    "X-Ts: " + ts + "\r\nX-Nonce: " + nonce + "\r\nX-Sig: " + sig + "\r\n";

   uchar bytes[];
   StrBytes(body, bytes);
   char post[];
   ArrayResize(post, ArraySize(bytes));
   for(int i = 0; i < ArraySize(bytes); i++) post[i] = (char)bytes[i];

   char result[];
   string resultHeaders;
   ResetLastError();
   int status = WebRequest("POST", InpBridgeUrl, headers, InpWebTimeoutMs, post, result, resultHeaders);
   if(status == -1)
     {
      int err = GetLastError();
      g_lastError = StringFormat("WebRequest err=%d", err);
      if(err == 4014) g_lastError += " (ยังไม่ได้เพิ่ม URL ใน Options > Expert Advisors)";
      return;
     }
   string response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
   if(status != 200) { g_lastError = StringFormat("HTTP %d %s", status, StringSubstr(response, 0, 120)); return; }
   if(!HandleResponse(response)) return;

   // server รับแล้ว: เลื่อน cursor และลบ ack ที่ส่งไปแล้ว (ack ใหม่จาก response นี้ยังอยู่)
   GvSet("deal_msc", (double)newMsc);
   GvSet("deal_ticket", (double)newTicket);
   int remain = ArraySize(g_acks) - acksSent;
   for(int i = 0; i < remain; i++)   // copy ทีละ field (struct ที่มี string ห้าม assign ตรง)
     {
      g_acks[i].id  = g_acks[acksSent + i].id;
      g_acks[i].ok  = g_acks[acksSent + i].ok;
      g_acks[i].msg = g_acks[acksSent + i].msg;
     }
   ArrayResize(g_acks, remain);
   g_lastOkSync = TimeLocal();
   g_lastError = "";
  }

//+------------------------------------------------------------------+
void UpdateComment()
  {
   int halt = (int)GvGet("halt", 0);
   Comment(StringFormat("XAU Control Bridge %s\nBridge: %s%s\nConfig v%d  trading=%s\nRisk: %s%s\nDay P/L: %.2f",
                        EA_VERSION,
                        !g_bridgeOn ? "ปิด" : (IsOffline() ? "OFFLINE (โหมดปลอดภัย)" : "online"),
                        g_lastError == "" ? "" : "\nError: " + g_lastError,
                        g_cfg.version, g_cfg.trading_enabled ? "on" : "off",
                        halt != 0 ? "HALT " + HaltReason(halt) : "ok",
                        GvGet("paused", 0) > 0 ? " (paused)" : "",
                        AccountInfoDouble(ACCOUNT_EQUITY) - GvGet("day_start_eq", AccountInfoDouble(ACCOUNT_EQUITY))));
  }

int OnInit()
  {
   // self-test: ต้องได้ค่าเดียวกับ bridge/tests (RFC 4231 style vector)
   if(HmacSha256Hex("key", "The quick brown fox jumps over the lazy dog")
      != "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8")
     {
      Print("XCB: HMAC self-test ไม่ผ่าน -> หยุด");
      return INIT_FAILED;
     }
   trade.SetExpertMagicNumber(InpMagic);
   DefaultCfg();
   MathSrand((uint)GetTickCount());
   g_startTime = TimeLocal();

   g_bridgeOn = (InpBridgeUrl != "") && !MQLInfoInteger(MQL_TESTER) && !MQLInfoInteger(MQL_OPTIMIZATION);
   if(g_bridgeOn && StringLen(InpSecret) < 32)
     {
      Print("XCB: InpSecret ต้องยาว >= 32 ตัวอักษร");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(g_bridgeOn && StringFind(InpBridgeUrl, "https://") != 0
      && StringFind(InpBridgeUrl, "://127.0.0.1") < 0 && StringFind(InpBridgeUrl, "://localhost") < 0)
      Print("XCB: คำเตือน URL ไม่ใช่ https ข้อมูลบัญชีวิ่งแบบไม่เข้ารหัส (คำสั่งยังถูกเซ็นกันปลอมอยู่)");

   RiskUpdate();
   EventSetTimer(1);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   Comment("");
  }

void OnTimer()
  {
   if(g_busy) return;
   g_busy = true;
   RiskUpdate();
   if(g_bridgeOn && TimeLocal() - g_lastAttempt >= InpPollSec)
     {
      g_lastAttempt = TimeLocal();
      DoSync();
     }
   UpdateComment();
   g_busy = false;
  }

void OnTick()
  {
   RiskUpdate();
   double slPts, tpPts;
   int sig = StrategySignal(slPts, tpPts);
   if(sig != 0) OpenPosition(sig, slPts, tpPts);
  }
//+------------------------------------------------------------------+
