#!/usr/bin/env python3
"""Build common XAUUSD bars from monthly Dukascopy tick Parquet files."""
from pathlib import Path
import numpy as np
import pandas as pd

RULES={"M1":"1min","M5":"5min","M15":"15min","H1":"1h","H4":"4h","D1":"1D"}

def month_to_m1(path: Path) -> pd.DataFrame:
    d=pd.read_parquet(path,columns=["timestamp","bid","ask","bid_vol","ask_vol"])
    d["timestamp"]=pd.to_datetime(d["timestamp"],utc=True)
    for c in ["bid","ask","bid_vol","ask_vol"]:
        d[c]=pd.to_numeric(d[c],errors="coerce")
    d=d.dropna(subset=["timestamp","bid","ask"]).sort_values("timestamp")
    d=d[d.ask>=d.bid]
    d["mid"]=(d.bid+d.ask)/2.0
    d["spread"]=d.ask-d.bid
    d["volume"]=(d.bid_vol.fillna(0)+d.ask_vol.fillna(0))/2.0
    d=d.set_index("timestamp")
    m=d.resample("1min",label="left",closed="left").agg(
        open=("mid","first"),high=("mid","max"),low=("mid","min"),close=("mid","last"),
        volume=("volume","sum"),spread=("spread","mean")
    ).dropna(subset=["open","high","low","close"])
    print(f"{path.name}: ticks={len(d):,} -> M1={len(m):,}")
    return m

def resample(df,rule):
    if rule=="1min": return df.copy()
    return df.resample(rule,label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum","spread":"mean"}
    ).dropna(subset=["open","high","low","close"])

def main():
    files=sorted(Path("data/ticks_repo").glob("20*/xauusd_20??_??.parquet"))
    if not files: raise SystemExit("No monthly parquet files found")
    parts=[]
    for p in files:
        try:
            z=month_to_m1(p)
            if len(z):
                parts.append(z)
        except Exception as e:
            print(f"SKIP_BAD_FILE {p}: {type(e).__name__}: {e}")
    if not parts:
        raise SystemExit("No readable tick parquet files")
    m1=pd.concat(parts).sort_index()
    # exact-month files should not overlap; be defensive if they do.
    m1=m1[~m1.index.duplicated(keep="last")]
    bad=((m1.high<m1.low)|(m1.high<m1.open)|(m1.high<m1.close)|(m1.low>m1.open)|(m1.low>m1.close)).sum()
    if bad: raise SystemExit(f"OHLC sanity failed: {bad} bars")
    out=Path("data/processed"); qdir=Path("data/quant_csv")
    out.mkdir(parents=True,exist_ok=True); qdir.mkdir(parents=True,exist_ok=True)
    print(f"Combined M1={len(m1):,} {m1.index.min()} -> {m1.index.max()}")
    # coverage audit: report market-hour gaps longer than 10 minutes (weekends excluded)
    delta=m1.index.to_series().diff()
    gaps=[]
    for tm,dt in delta[delta>pd.Timedelta(minutes=10)].items():
        prev=tm-dt
        # Ignore ordinary weekend gaps (~Fri->Sun/Mon); keep suspicious weekday/multi-day holes.
        if prev.weekday()==4 and tm.weekday() in (6,0) and dt<pd.Timedelta(days=4):
            continue
        gaps.append((prev,tm,dt))
    print(f"SUSPICIOUS_GAPS={len(gaps)}")
    for a,b,dt in gaps[:30]:
        print(f"GAP {a} -> {b} duration={dt}")
    print(f"Spread median={m1.spread.median():.4f} USD p90={m1.spread.quantile(.9):.4f} USD")
    for tf,rule in RULES.items():
        x=resample(m1,rule).reset_index().rename(columns={"ts":"time"})
        if "time" not in x.columns: x=x.rename(columns={x.columns[0]:"time"})
        x.to_csv(out/f"xauusd_{tf.lower()}.csv",index=False)
        q=x.rename(columns={"volume":"tick_volume"}).copy()
        q["spread"]=q["spread"]/0.01
        q["time"]=pd.to_datetime(q["time"],utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
        q.to_csv(qdir/f"XAUUSD_{tf}.csv",index=False)
        print(f"{tf}: {len(x):,} bars")
if __name__=="__main__": main()
