#!/usr/bin/env python3
"""Causality-corrected one-year screening for three deterministic XAUUSD Python systems.

Test window: 2025-09-01 <= time < 2026-09-01.
All results are normalized to R and a 1% risk-per-trade equity curve so entry edge
can be compared without each repo's money-management scheme.
"""
from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

START=pd.Timestamp("2025-09-01",tz="UTC")
END=pd.Timestamp("2026-09-01",tz="UTC")
OUT=Path("results"); OUT.mkdir(exist_ok=True)

def load(tf):
    d=pd.read_csv(f"data/processed/xauusd_{tf}.csv")
    d["time"]=pd.to_datetime(d["time"],utc=True)
    return d.sort_values("time").reset_index(drop=True)

def metrics(name,trades,notes=None):
    if not trades:
        return {"name":name,"trades":0,"pf":0,"expectancy_r":0,"max_dd_pct":0,"win_rate_pct":0,"pass":False,"notes":notes or []}
    t=pd.DataFrame(trades).copy()
    t["time"]=pd.to_datetime(t["time"],utc=True)
    t=t[(t.time>=START)&(t.time<END)].sort_values("time").reset_index(drop=True)
    if t.empty:
        return {"name":name,"trades":0,"pf":0,"expectancy_r":0,"max_dd_pct":0,"win_rate_pct":0,"pass":False,"notes":notes or []}
    r=t["r"].astype(float).to_numpy()
    pos=r[r>0].sum(); neg=-r[r<0].sum()
    pf=float(pos/neg) if neg>0 else 999.0
    eq=10000.0; peak=eq; maxdd=0.0; curve=[]
    # standardized fixed-fraction risk: 1R == 1% current equity
    for tm,x in zip(t.time,r):
        eq*=max(0.0,1.0+0.01*x)
        peak=max(peak,eq)
        dd=(peak-eq)/peak*100 if peak else 0
        maxdd=max(maxdd,dd); curve.append((tm.isoformat(),eq))
    monthly=t.assign(month=t.time.dt.to_period("M").astype(str)).groupby("month")["r"].sum()
    prof_months=int((monthly>0).sum())
    best_share=float(monthly.max()/monthly[monthly>0].sum()) if (monthly>0).any() else 1.0
    n=len(t); exp=float(r.mean()); wr=float((r>0).mean()*100)
    passed=bool(n>=50 and pf>=1.20 and maxdd<=20 and exp>0)
    warn=[] if n>=100 else ["sample<100 trades"]
    res={"name":name,"trades":n,"win_rate_pct":round(wr,2),"pf":round(pf,3),
         "expectancy_r":round(exp,4),"net_r":round(float(r.sum()),2),
         "max_dd_pct":round(maxdd,2),"ending_equity_1pct":round(eq,2),
         "positive_months":prof_months,"months":int(len(monthly)),
         "best_positive_month_share":round(best_share,3),"pass":passed,
         "warnings":warn,"notes":notes or []}
    t.to_csv(OUT/(name.lower().replace(" ","_")+"_trades.csv"),index=False)
    return res

# ---------- Indicators ----------
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def atr_ewm(d,n=14):
    pc=d.close.shift(1)
    tr=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,adjust=False).mean()
def adx_ewm(d,n=14):
    up=d.high.diff(); down=-d.low.diff()
    pdm=pd.Series(np.where((up>down)&(up>0),up,0.0),index=d.index)
    mdm=pd.Series(np.where((down>up)&(down>0),down,0.0),index=d.index)
    pc=d.close.shift(1)
    tr=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    a=tr.ewm(span=n,adjust=False).mean()
    pdi=100*pdm.ewm(span=n,adjust=False).mean()/a
    mdi=100*mdm.ewm(span=n,adjust=False).mean()/a
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    return dx.ewm(span=n,adjust=False).mean()
def atr_sma(d,n=14):
    pc=d.close.shift(1)
    tr=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

# ---------- UT Bot (causality-corrected) ----------
def run_ut():
    d=load("m15").copy()
    d["atr"]=atr_ewm(d); d["ema"]=ema(d.close,50); d["adx"]=adx_ewm(d)
    trailing=0.0; pos=None; trades=[]
    for i in range(2,len(d)):
        row=d.iloc[i]; p1=d.iloc[i-1]; p2=d.iloc[i-2]
        if pd.isna(p1.atr) or pd.isna(p1.adx): continue
        nloss=1.5*float(p1.atr)
        prev=trailing
        if p1.close>prev and p2.close>prev: trailing=max(prev,p1.close-nloss)
        elif p1.close<prev and p2.close<prev: trailing=min(prev,p1.close+nloss)
        elif p1.close>prev: trailing=p1.close-nloss
        else: trailing=p1.close+nloss
        # manage any position first on this bar. If it exits intrabar, do not
        # pretend we could re-enter at this bar's already-passed open.
        exited=False
        if pos is not None:
            if pos["side"]=="BUY":
                slhit=row.low<=pos["sl"]; tphit=row.high>=pos["tp"]
            else:
                slhit=row.high>=pos["sl"]; tphit=row.low<=pos["tp"]
            if slhit or tphit:
                rr=-1.0 if slhit else 2.5  # pessimistic SL-first tie
                trades.append({"time":pos["time"],"exit_time":row.time,"side":pos["side"],"r":rr})
                pos=None; exited=True
        if exited or pos is not None: continue
        if p1.atr<6.0 or p1.adx<22.0: continue
        long=bool(p1.close>trailing and p1.close>p1.ema)
        short=bool(p1.close<trailing and p1.close<p1.ema)
        if not (long or short): continue
        sp=float(row.spread)
        if long:
            entry=float(row.open)+sp/2; side="BUY"; sl=entry-nloss; tp=entry+2.5*nloss
        else:
            entry=float(row.open)-sp/2; side="SELL"; sl=entry+nloss; tp=entry-2.5*nloss
        pos={"time":row.time,"side":side,"sl":sl,"tp":tp}
        # Causal improvement over original: newly-opened trade can hit SL/TP in entry bar.
        if side=="BUY": slhit=row.low<=sl; tphit=row.high>=tp
        else: slhit=row.high>=sl; tphit=row.low<=tp
        if slhit or tphit:
            trades.append({"time":row.time,"exit_time":row.time,"side":side,"r":-1.0 if slhit else 2.5})
            pos=None
    return metrics("UT_Bot_M15",trades,["original indicators/entry logic","fixed impossible same-bar re-entry","fixed entry-bar SL/TP omission","1% normalized risk; anti-martingale removed for edge screening"])

# ---------- Volume Profile ----------
def vol_profile(g,bins=100,va=.70):
    lo=float(g.low.min()); hi=float(g.high.max())
    if not hi>lo: return None
    edges=np.linspace(lo,hi,bins+1); v=np.zeros(bins)
    for row in g.itertuples():
        a=float(row.low); b=float(row.high); vol=max(float(row.volume),0.0)
        if b<=a: continue
        left=np.maximum(edges[:-1],a); right=np.minimum(edges[1:],b)
        ov=np.maximum(0,right-left); s=ov.sum()
        if s>0: v+=vol*ov/s
    if v.sum()<=0: return None
    p=int(np.argmax(v)); selected={p}; total=v[p]; target=v.sum()*va
    l=p-1; r=p+1
    while total<target and (l>=0 or r<bins):
        lv=v[l] if l>=0 else -1; rv=v[r] if r<bins else -1
        if rv>lv: selected.add(r); total+=v[r]; r+=1
        else: selected.add(l); total+=v[l]; l-=1
    centers=(edges[:-1]+edges[1:])/2
    return float(centers[p]),float(edges[max(selected)+1]),float(edges[min(selected)])

def scan_exit(d,start,side,sl,tp,last):
    for j in range(start,min(last+1,start+300)):
        row=d.iloc[j]
        if side=="BUY": a=row.low<=sl; b=row.high>=tp
        else: a=row.high>=sl; b=row.low<=tp
        if a and b: return -1.0,j
        if a: return -1.0,j
        if b: return 2.0,j
    return None,None

def run_volume():
    d=load("m5").copy()
    d["ist"]=d.time.dt.tz_convert("Asia/Kolkata")
    d["date"]=d.ist.dt.date; d["tod"]=d.ist.dt.strftime("%H:%M")
    trades=[]
    for date,gday in d.groupby("date",sort=True):
        if pd.Timestamp(date).weekday()>4: continue
        day_idx=gday.index.to_numpy()
        last=int(day_idx[-1])
        sessions=[("MORNING","03:30","06:00",10),("US_OPEN","18:55","19:55",10)]
        for sname,a,b,minbars in sessions:
            sg=gday[(gday.tod>=a)&(gday.tod<=b)]
            if len(sg)<minbars: continue
            vp=vol_profile(sg)
            if vp is None: continue
            poc,vah,val=vp; levels=[("VAH",vah),("POC",poc),("VAL",val)]
            end_idx=int(sg.index[-1])
            taken=False
            for idx in day_idx[day_idx>end_idx]:
                idx=int(idx)
                if idx<3 or idx+1>=len(d): continue
                cur=d.iloc[idx]; prev=d.iloc[idx-1]
                found=None
                for lname,lvl in levels:
                    if cur.low<=lvl+0.50 and cur.close>lvl and prev.close<=lvl:
                        found=("BUY",lname,lvl); break
                    if cur.high>=lvl-0.50 and cur.close<lvl and prev.close>=lvl:
                        found=("SELL",lname,lvl); break
                if not found: continue
                side,lname,lvl=found
                # FIX: signal uses current close, so earliest legal entry is NEXT bar open.
                ei=idx+1
                if d.iloc[ei].ist.date()!=date: break
                entryrow=d.iloc[ei]; sp=float(entryrow.spread)
                if side=="BUY":
                    entry=float(entryrow.open)+sp/2
                    sl=float(d.low.iloc[max(0,idx-3):idx].min())
                    risk=entry-sl
                    tp=entry+2*risk
                else:
                    entry=float(entryrow.open)-sp/2
                    sl=float(d.high.iloc[max(0,idx-3):idx].max())
                    risk=sl-entry
                    tp=entry-2*risk
                if not (0.30<=risk<=15.0): continue
                rr,x=scan_exit(d,ei,side,sl,tp,last)
                if rr is not None:
                    trades.append({"time":entryrow.time,"exit_time":d.iloc[x].time,"side":side,"level":lname,"r":rr})
                taken=True; break
    return metrics("Volume_Profile_M5",trades,["POC/VAH/VAL original session rules","LOOKAHEAD FIX: confirm close then next-bar open","pessimistic SL-first tie"])

# ---------- ICT FVG ----------
def h4_bias(x):
    if len(x)<51: return "RANGING"
    fast=x.close.rolling(10).mean().iloc[-1]; slow=x.close.rolling(50).mean().iloc[-1]; c=x.close.iloc[-1]
    if c>fast and c>slow and fast>slow: return "BULLISH"
    if c<fast and c<slow and fast<slow: return "BEARISH"
    return "RANGING"
def pd_zone(x):
    if len(x)<50: return "EQUILIBRIUM"
    z=x.tail(50); hi=z.high.max(); lo=z.low.min()
    if hi==lo:return "EQUILIBRIUM"
    q=(x.close.iloc[-1]-lo)/(hi-lo)
    return "PREMIUM" if q>.5 else "DISCOUNT" if q<.5 else "EQUILIBRIUM"
def structure(x):
    if len(x)<20:return "NEUTRAL"
    hs=[]; ls=[]
    for i in range(2,len(x)-2):
        w=x.iloc[i-2:i+3]
        if x.high.iloc[i]>w.drop(w.index[2]).high.max(): hs.append(x.high.iloc[i])
        if x.low.iloc[i]<w.drop(w.index[2]).low.min(): ls.append(x.low.iloc[i])
    if len(hs)>=2 and len(ls)>=2:
        if hs[-1]>hs[-2] and ls[-1]>ls[-2]:return "BULLISH"
        if hs[-1]<hs[-2] and ls[-1]<ls[-2]:return "BEARISH"
    return "NEUTRAL"
def fvg_retest(x,bias):
    if len(x)<15:return None
    last=len(x)-1
    for i in range(last-1,max(2,last-15),-1):
        c1=x.iloc[i-2]; c3=x.iloc[i]
        if c3.low>c1.high:
            top=c3.low; bot=c1.high; valid=True; ret=False
            for j in range(i+1,len(x)):
                z=x.iloc[j]
                if z.close<bot: valid=False; break
                if z.low<=top: ret=True
            if valid and ret and bias in ("BULLISH","RANGING"): return "BUY",float(c1.low)
        if c3.high<c1.low:
            top=c1.low; bot=c3.high; valid=True; ret=False
            for j in range(i+1,len(x)):
                z=x.iloc[j]
                if z.close>top: valid=False; break
                if z.high>=bot: ret=True
            if valid and ret and bias in ("BEARISH","RANGING"): return "SELL",float(c1.high)
    return None
def get_session(twib):
    h=twib.hour
    if 8<=h<10:return "ASIA"
    if 14<=h<17:return "LONDON"
    if 19<=h<23:return "NY"
    return "UNKNOWN"
def ict_exit(open_trades,row,now):
    done=[]
    for t in open_trades:
        if t.get("done"): continue
        side=t["side"]
        if side=="BUY":
            if row.low<=t["sl"]: rr=-1.0
            elif row.high>=t["tp2"]: rr=2.0
            elif row.high>=t["tp1"]: rr=(t["tp1"]-t["entry"])/t["risk"]
            else: rr=None
        else:
            if row.high>=t["sl"]: rr=-1.0
            elif row.low<=t["tp2"]: rr=2.0
            elif row.low<=t["tp1"]: rr=(t["entry"]-t["tp1"])/t["risk"]
            else: rr=None
        age=(now-t["opened"]).total_seconds()/60/15
        if rr is None and age>48: rr=0.0
        if rr is not None:
            t["r"]=float(rr); t["done"]=True; t["exit_time"]=row.time; done.append(t)
    return done

def run_ict():
    m5=load("m5"); m15=load("m15"); h4=load("h4")
    m15["atr"]=atr_sma(m15,14)
    # Precompute causal availability times once. searchsorted turns the old
    # full-DataFrame filter on every M5 bar into O(log N) lookup.
    m15_available=pd.DatetimeIndex(m15["time"]).asi8 + 15*60*1_000_000_000
    h4_available=pd.DatetimeIndex(h4["time"]).asi8 + 4*60*60*1_000_000_000
    open_tr=[]; done=[]; trackers={"BUY":(None,None),"SELL":(None,None)}
    for i in range(60,len(m5)):
        row=m5.iloc[i]
        decision=row.time+pd.Timedelta(minutes=5)  # current M5 is now CLOSED
        now_wib=decision.tz_convert("Asia/Jakarta")
        done.extend(ict_exit(open_tr,row,now_wib.to_pydatetime()))
        # CAUSAL HTF FIX: only bars whose full duration has closed by decision time.
        d_ns=int(decision.value)
        j15=int(np.searchsorted(m15_available,d_ns,side="right"))
        j4=int(np.searchsorted(h4_available,d_ns,side="right"))
        x15=m15.iloc[max(0,j15-60):j15].copy()
        x4=h4.iloc[max(0,j4-60):j4].copy()
        if len(x15)<15 or len(x4)<51: continue
        bias=h4_bias(x4); z=pd_zone(x4); st=structure(x4)
        sig=fvg_retest(x15,bias)
        if not sig: continue
        side,extreme=sig
        ses=get_session(now_wib); dow=now_wib.weekday()
        kz=ses in ("ASIA","LONDON","NY")
        conf=int(kz)+int((side=="BUY" and bias=="BULLISH") or (side=="SELL" and bias=="BEARISH"))+1
        valid=(ses=="LONDON" and dow in (0,1,2) and conf>=2) or (ses=="NY" and conf>=3)
        if not valid: continue
        # spam: same extreme inside 15m
        last_t,last_ext=trackers[side]
        if last_t is not None and last_ext==extreme and (decision-last_t).total_seconds()<900: continue
        # invalidation
        if side=="BUY" and row.close<extreme: continue
        if side=="SELL" and row.close>extreme: continue
        if side=="BUY" and z!="DISCOUNT": continue
        if side=="SELL" and z!="PREMIUM": continue
        if side=="BUY" and st=="BEARISH": continue
        if side=="SELL" and st=="BULLISH": continue
        atr=float(x15.atr.iloc[-1])
        if not np.isfinite(atr) or atr<=0: continue
        sp=float(row.spread)
        entry=float(row.close)+(sp/2 if side=="BUY" else -sp/2)
        buf=.8*atr
        if side=="BUY":
            sl=round(extreme-buf,2)
            if sl>=entry: sl=round(entry-buf-1.0,2)
            risk=abs(entry-sl); fallback=entry+risk
            recent=float(m5.iloc[max(0,i-59):i+1].high.max())
            tp1=round(recent if recent>fallback else fallback,2); tp2=round(entry+2*risk,2)
        else:
            sl=round(extreme+buf,2)
            if sl<=entry: sl=round(entry+buf+1.0,2)
            risk=abs(entry-sl); fallback=entry-risk
            recent=float(m5.iloc[max(0,i-59):i+1].low.min())
            tp1=round(recent if recent<fallback else fallback,2); tp2=round(entry-2*risk,2)
        if not (.5*atr<=risk<=5*atr): continue
        t={"time":decision,"opened":now_wib.to_pydatetime(),"side":side,"entry":entry,"sl":sl,
           "tp1":tp1,"tp2":tp2,"risk":risk,"done":False}
        open_tr.append(t); trackers[side]=(decision,extreme)
    clean=[{"time":t["time"],"exit_time":t["exit_time"],"side":t["side"],"r":t["r"]} for t in done if t.get("done")]
    return metrics("ICT_FVG",clean,["H4 10/50 SMA bias + M15 FVG retest","HTF FUTURE-LEAK FIX: M15/H4 only after bar close","WIB session rules","TP outcome follows repo tracker"])

def main():
    results=[run_ut(),run_volume(),run_ict()]
    with open(OUT/"deterministic_summary.json","w",encoding="utf-8") as f: json.dump(results,f,indent=2)
    print("\n=== DETERMINISTIC SCREEN ===")
    for r in results: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__": main()
