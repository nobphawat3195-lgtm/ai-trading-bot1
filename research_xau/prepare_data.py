#!/usr/bin/env python3
"""Prepare one-year XAUUSD research bars from Dukascopy-node BID/ASK M1 CSVs."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

RULES={"M1":"1min","M5":"5min","M15":"15min","H1":"1h","H4":"4h","D1":"1D"}

def _read(path: str) -> pd.DataFrame:
    p=Path(path)
    df=pd.read_csv(p)
    if len(df.columns)==1:
        df=pd.read_csv(p, sep=";")
    df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
    tc=next((c for c in ["timestamp","time","datetime","date","gmt_time"] if c in df.columns),None)
    if tc is None:
        raise ValueError(f"{p}: no timestamp column; got {list(df.columns)}")
    s=df[tc]
    if np.issubdtype(s.dtype, np.number):
        num=pd.to_numeric(s,errors="coerce")
        mx=float(num.dropna().abs().max())
        unit="ms" if mx>1e11 else "s"
        ts=pd.to_datetime(num,unit=unit,utc=True,errors="coerce")
    else:
        ts=pd.to_datetime(s,utc=True,errors="coerce")
    ren={}
    for want in ["open","high","low","close"]:
        cand=next((c for c in df.columns if c==want or c.endswith("_"+want)),None)
        if cand is None:
            raise ValueError(f"{p}: missing {want}; got {list(df.columns)}")
        ren[cand]=want
    vc=next((c for c in ["volume","tick_volume","vol"] if c in df.columns),None)
    keep=list(ren)+([vc] if vc else [])
    out=df[keep].rename(columns=ren).copy()
    out.insert(0,"time",ts)
    if vc:
        if vc=="volume":
            out["volume"]=pd.to_numeric(out["volume"],errors="coerce")
        else:
            out["volume"]=pd.to_numeric(out[vc],errors="coerce")
            if vc in out.columns: out.drop(columns=[vc],inplace=True)
    else:
        out["volume"]=0.0
    for c in ["open","high","low","close","volume"]:
        out[c]=pd.to_numeric(out[c],errors="coerce")
    out=out.dropna(subset=["time","open","high","low","close"]).drop_duplicates("time").sort_values("time")
    return out.set_index("time")

def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if rule=="1min":
        return df.copy()
    agg={"open":"first","high":"max","low":"min","close":"last","volume":"sum","spread":"mean"}
    return df.resample(rule,label="left",closed="left").agg(agg).dropna(subset=["open","high","low","close"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bid",required=True)
    ap.add_argument("--ask",required=True)
    a=ap.parse_args()
    bid=_read(a.bid)
    ask=_read(a.ask)
    common=bid.index.intersection(ask.index)
    if len(common)<10000:
        raise SystemExit(f"Too few aligned M1 bars: {len(common)}")
    bid=bid.loc[common]
    ask=ask.loc[common]
    mid=pd.DataFrame(index=common)
    for c in ["open","high","low","close"]:
        mid[c]=(bid[c].to_numpy()+ask[c].to_numpy())/2.0
    mid["volume"]=bid["volume"].to_numpy()
    mid["spread"]=(ask["close"].to_numpy()-bid["close"].to_numpy()).clip(min=0)
    mid=mid[(mid.high>=mid.low)&(mid.high>=mid.open)&(mid.high>=mid.close)&(mid.low<=mid.open)&(mid.low<=mid.close)]
    outdir=Path("data/processed")
    qdir=Path("data/quant_csv")
    outdir.mkdir(parents=True,exist_ok=True)
    qdir.mkdir(parents=True,exist_ok=True)
    print(f"aligned M1={len(mid):,} {mid.index.min()} -> {mid.index.max()}")
    print(f"spread median={mid.spread.median():.4f} USD p90={mid.spread.quantile(.9):.4f} USD")
    for tf,rule in RULES.items():
        x=_resample(mid,rule).reset_index()
        x.to_csv(outdir/f"xauusd_{tf.lower()}.csv",index=False)
        q=x.rename(columns={"volume":"tick_volume"}).copy()
        q["spread"]=q["spread"]/0.01
        q["time"]=pd.to_datetime(q["time"],utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
        q.to_csv(qdir/f"XAUUSD_{tf}.csv",index=False)
        print(f"{tf}: {len(x):,} bars")

if __name__=="__main__":
    main()
