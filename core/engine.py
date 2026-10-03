from __future__ import annotations
import numpy as np
import pandas as pd


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy().sort_values("trade_date").reset_index(drop=True)
    for c in ["open","high","low","close","volume","amount"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["ma5"] = d.close.rolling(5).mean()
    d["ma20"] = d.close.rolling(20).mean()
    d["ma60"] = d.close.rolling(60).mean()
    d["ma120"] = d.close.rolling(120).mean()
    d["ma250"] = d.close.rolling(250).mean()
    prev = d.close.shift(1)
    tr = pd.concat([(d.high-d.low), (d.high-prev).abs(), (d.low-prev).abs()], axis=1).max(axis=1)
    d["atr14"] = tr.rolling(14).mean()
    d["rvol20"] = d.volume / d.volume.rolling(20).mean().replace(0, np.nan)
    d["ret5"] = d.close.pct_change(5)
    d["ret20"] = d.close.pct_change(20)
    d["ret60"] = d.close.pct_change(60)
    d["high20"] = d.high.rolling(20).max().shift(1)
    d["high60"] = d.high.rolling(60).max().shift(1)
    d["low20"] = d.low.rolling(20).min().shift(1)
    d["low60"] = d.low.rolling(60).min().shift(1)
    d["high250"] = d.high.rolling(250).max().shift(1)
    d["low250"] = d.low.rolling(250).min().shift(1)
    d["slope20"] = d.close.rolling(20).apply(lambda x: np.polyfit(np.arange(len(x)), x, 1)[0], raw=True)
    return d


def classify(d: pd.DataFrame) -> dict:
    if len(d) < 80:
        return {"E":"E3","T":"T4","S":"S3","P":"P5","V":"V4","M":"M2","L":"L3","X":"X1","Stage":"数据不足","strategy":"WATCH"}
    r = d.iloc[-1]; c=float(r.close); ma20=float(r.ma20); ma60=float(r.ma60)
    up = c > ma20 > ma60 and r.slope20 > 0
    down = c < ma20 < ma60 and r.slope20 < 0
    breakout = pd.notna(r.high20) and c > float(r.high20)
    volume_break = breakout and float(r.rvol20 or 0) >= 1.5
    near_high = c >= d.high.tail(250).max() * .95
    if up and r.ret20 > .05: T="T1"
    elif up: T="T2"
    elif down: T="T5"
    elif c > ma60: T="T3"
    else: T="T4"
    if volume_break: S,P,V,X="S4","P2","V5","X2"
    elif breakout: S,P,V,X="S4","P2","V2","X1"
    elif up and c >= ma20: S,P,V,X="S1","P3",("V2" if r.rvol20 < 1 else "V1"),"X4"
    elif up: S,P,V,X="S2","P5","V4","X3"
    elif down: S,P,V,X="S6","P6",("V3" if r.rvol20 > 1.2 else "V4"),"X6"
    else: S,P,V,X="S3","P1","V4","X1"
    ret60=float(r.ret60) if pd.notna(r.ret60) else 0
    M="M4" if near_high else ("M3" if ret60 > .15 else ("M1" if ret60 > 0 else "M2"))
    low250=float(d.low.tail(250).min()); pos=c/low250 if low250 else 1
    L="L5" if near_high else ("L4" if pos > 1.6 else ("L3" if pos > 1.25 else "L2"))
    E="E1" if up and ret60>0 else ("E5" if down else "E3")
    if down and r.ret20 > -.08 and c > ma20: stage="趋势转换"
    elif down: stage="下跌"
    elif volume_break: stage="突破加速"
    elif breakout: stage="平台突破"
    elif up and r.rvol20 < 1: stage="上升整理"
    elif up: stage="上升"
    elif c > ma60: stage="底部/反转观察"
    else: stage="震荡"
    strategy="WATCH"
    if X in {"X1","X2"} and T in {"T1","T2","T3"}: strategy="BREAKOUT"
    elif T in {"T1","T2"} and S=="S2" and r.rvol20 <= 1.05: strategy="PULLBACK"
    elif T=="T3" and S in {"S3"}: strategy="REVERSAL"
    return {"E":E,"T":T,"S":S,"P":P,"V":V,"M":M,"L":L,"X":X,"Stage":stage,"strategy":strategy}


def analyze(df: pd.DataFrame):
    d=enrich(df); return d,classify(d)
