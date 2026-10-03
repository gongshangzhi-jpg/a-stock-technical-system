import pandas as pd
from .engine import enrich


def backtest(df: pd.DataFrame, strategy: str, horizon: int = 20) -> dict:
    d=enrich(df).copy()
    if len(d)<100: return {"signals":0,"win_rate":None,"avg_return":None,"median_return":None,"max_drawdown":None}
    if strategy=="BREAKOUT": sig=(d.close>d.high20)&(d.rvol20>=1.2)
    elif strategy=="PULLBACK": sig=(d.close>d.ma20)&(d.ma20>d.ma60)&(d.rvol20<1.0)
    else: sig=(d.close>d.ma20)&(d.ma20.diff()>0)&(d.close.shift(5)<d.ma20.shift(5))
    entries=d.index[sig]; rets=[]
    for i in entries:
        pos=d.index.get_loc(i)
        if pos+horizon+1>=len(d): continue
        entry=float(d.iloc[pos+1].open); exitp=float(d.iloc[pos+horizon+1].close)
        if entry: rets.append(exitp/entry-1)
    s=pd.Series(rets,dtype=float)
    if s.empty: return {"signals":0,"win_rate":None,"avg_return":None,"median_return":None,"max_drawdown":None}
    curve=(1+s).cumprod(); dd=(curve/curve.cummax()-1).min()
    return {"signals":len(s),"win_rate":float((s>0).mean()),"avg_return":float(s.mean()),"median_return":float(s.median()),"max_drawdown":float(dd)}
