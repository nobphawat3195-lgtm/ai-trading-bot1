#!/usr/bin/env python3
"""Adapter for Aarayanc49/xauusd-quant-backtest SWING spec on our common dataset."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EXT=ROOT/"external"/"xauusd-quant-backtest"
sys.path.insert(0,str(EXT))
from research.features import build
from core.strategy import SWING

START=pd.Timestamp("2025-09-01",tz="UTC")
END=pd.Timestamp("2026-09-01",tz="UTC")

def main():
    # Use observed Dukascopy bid/ask spread without the repo's funded-account 1.67x stress multiplier.
    rows=build("XAUUSD",base="M5",spread_mult=1.0,quiet=True,target_r=8.0,hold_hours=24)
    rows=SWING.select(rows)
    selected=[]
    for x in rows:
        t=pd.to_datetime(x["ts"],utc=True)
        if START<=t<END:
            selected.append({"time":t,"side":x["direction"],"r":float(x["r"]),
                             "risk_pips":float(x["risk_pips"]),"session":x["session"],
                             "range_pct":float(x["range_pct"]),"spread_pct":float(x["spread_pct"]),
                             "h4_pullback":float(x["h4_pullback"])})
    t=pd.DataFrame(selected).sort_values("time") if selected else pd.DataFrame(columns=["time","r"])
    r=t.r.to_numpy(dtype=float) if len(t) else np.array([])
    pos=r[r>0].sum() if len(r) else 0; neg=-r[r<0].sum() if len(r) else 0
    pf=float(pos/neg) if neg>0 else (999.0 if pos>0 else 0.0)
    eq=10000.; peak=eq; mdd=0.
    for z in r:
        eq*=max(0.,1.+.01*z); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100)
    if len(t):
        month=t.assign(month=pd.to_datetime(t.time,utc=True).dt.to_period("M").astype(str)).groupby("month").r.sum()
        pm=int((month>0).sum()); nm=len(month)
    else: pm=0; nm=0
    res={"name":"Quant_SWING","trades":int(len(r)),"win_rate_pct":round(float((r>0).mean()*100),2) if len(r) else 0,
         "pf":round(pf,3),"expectancy_r":round(float(r.mean()),4) if len(r) else 0,
         "net_r":round(float(r.sum()),2) if len(r) else 0,"max_dd_pct":round(mdd,2),
         "ending_equity_1pct":round(eq,2),"positive_months":pm,"months":nm,
         "pass":bool(len(r)>=50 and pf>=1.2 and mdd<=20 and (r.mean() if len(r) else 0)>0),
         "warnings":[] if len(r)>=100 else ["sample<100 trades"],
         "notes":["original SWING filters","1.5 ATR stop / 8R target / 24h hold / no trail",
                  "observed Dukascopy spread x1.0","1% normalized risk for comparison"]}
    Path("results").mkdir(exist_ok=True)
    t.to_csv("results/quant_swing_trades.csv",index=False)
    Path("results/quant_summary.json").write_text(json.dumps(res,indent=2),encoding="utf-8")
    print("=== QUANT SWING ===")
    print(json.dumps(res,ensure_ascii=False))
if __name__=="__main__": main()
