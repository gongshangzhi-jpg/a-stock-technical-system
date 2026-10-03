import numpy as np
import pandas as pd

def atr(df,n=14):
    tr=pd.concat([(df.High-df.Low),(df.High-df.Close.shift()).abs(),(df.Low-df.Close.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean()

def add_base(df):
    d=df.copy()
    for n in [5,20,60,120,250]: d[f'MA{n}']=d.Close.rolling(n,min_periods=n).mean()
    d['ATR14']=atr(d); d['ATRRatio']=d.ATR14/d.Close
    d['VOL20']=d.Volume.rolling(20,min_periods=20).mean(); d['RVOL']=d.Volume/d.VOL20
    for n in [5,20,60,120,250]: d[f'RET{n}']=d.Close/d.Close.shift(n)-1
    for n in [20,60,250]: d[f'High{n}']=d.High.rolling(n,min_periods=n).max(); d[f'Low{n}']=d.Low.rolling(n,min_periods=n).min()
    d['Slope20']=d.MA20/d.MA20.shift(5)-1; d['Slope60']=d.MA60/d.MA60.shift(5)-1
    return d

def pivots(df,left=3,right=3):
    d=df.copy(); h=d.High.values; l=d.Low.values; sh=np.zeros(len(d),bool); sl=np.zeros(len(d),bool)
    for i in range(left,len(d)-right):
        sh[i]=h[i]>=max(h[i-left:i]) and h[i]>=max(h[i+1:i+right+1])
        sl[i]=l[i]<=min(l[i-left:i]) and l[i]<=min(l[i+1:i+right+1])
    d['PivotHigh']=sh; d['PivotLow']=sl
    d['ConfirmedHigh']=False; d['ConfirmedLow']=False
    if right:
        d.iloc[right:,d.columns.get_loc('ConfirmedHigh')]=sh[:-right]
        d.iloc[right:,d.columns.get_loc('ConfirmedLow')]=sl[:-right]
    else: d['ConfirmedHigh']=sh; d['ConfirmedLow']=sl
    return d

def classify(df):
    if len(df)<80: return pd.DataFrame()
    d=add_base(pivots(df))
    hs=[]; ls=[]; rows=[]
    for i,idx in enumerate(d.index):
        if bool(d.loc[idx,'ConfirmedHigh']): hs.append(idx)
        if bool(d.loc[idx,'ConfirmedLow']): ls.append(idx)
        hh=hl=lh=ll=False
        prev_h=prev_l=None
        if len(hs)>=2:
            a,b=hs[-2],hs[-1]; hh=d.loc[b,'High']>d.loc[a,'High']; lh=d.loc[b,'High']<d.loc[a,'High']; prev_h=d.loc[b,'High']
        if len(ls)>=2:
            a,b=ls[-2],ls[-1]; hl=d.loc[b,'Low']>d.loc[a,'Low']; ll=d.loc[b,'Low']<d.loc[a,'Low']; prev_l=d.loc[b,'Low']
        r=d.loc[idx]; c=r.Close
        if pd.notna(r.MA120) and c>r.MA20>r.MA60>r.MA120 and r.Slope20>0 and r.Slope60>0: T='T1'
        elif pd.notna(r.MA60) and c>r.MA20>r.MA60 and r.Slope20>0: T='T2'
        elif pd.notna(r.MA60) and c>r.MA60 and r.Slope20>0: T='T3'
        elif pd.notna(r.MA60) and abs(r.Slope20)<.005 and abs(r.Slope60)<.005: T='T4'
        elif pd.notna(r.MA60) and c<r.MA20<r.MA60: T='T5'
        else: T='T3' if pd.notna(r.MA60) and c>r.MA60 else 'T4'
        if hh and hl: S='S1'
        elif hl and not ll and T in ('T1','T2'): S='S2'
        elif lh and ll: S='S6'
        elif hl and lh: S='S5'
        elif pd.notna(r.MA20) and (r.High20-r.Low20)/r.MA20<.20 and abs(r.Slope20)<.01: S='S3'
        elif pd.notna(r.High20) and c>r.High20.shift(1) if False else False: S='S4'
        else: S='S3'
        rv=r.RVOL; ret5=r.RET5
        if pd.isna(rv): V='V0'
        elif c>r.High20 and rv>1.5: V='V5'
        elif ret5>0 and rv>1.5: V='V1'
        elif ret5>0 and rv<.8: V='V2'
        elif ret5<0 and rv>1.5: V='V3'
        elif ret5<0 and rv<1: V='V4'
        else: V='V0'
        M='M3' if pd.notna(r.High60) and c>=r.High60 else 'M4' if pd.notna(r.High250) and c/r.High250>=.90 else 'M5' if pd.notna(r.RET60) and r.RET20>0 and r.RET20>r.RET60/3 else 'M1' if r.RET20>0 else 'M0'
        pos=(c-r.Low250)/(r.High250-r.Low250) if pd.notna(r.Low250) and pd.notna(r.High250) and r.High250!=r.Low250 else np.nan
        L='L1' if pd.notna(pos) and pos<.2 else 'L2' if pd.notna(pos) and pos<.4 else 'L3' if pd.notna(pos) and pos<.7 else 'L4' if pd.notna(pos) and pos<.9 else 'L5'
        breakout=(prev_h if prev_h is not None else r.High20)
        if pd.notna(breakout) and c>breakout and rv>1.5: X='X2'
        elif pd.notna(breakout) and c>breakout: X='X1'
        elif T in ('T1','T2') and ret5<0 and rv<1: X='X3'
        elif S=='S5' and rv>1.2: X='X5'
        else: X='X0'
        if X in ('X1','X2'): stage='7'
        elif T=='T5' and S=='S6': stage='1'
        elif T=='T3' and S=='S5': stage='4'
        elif T in ('T1','T2') and S=='S2': stage='6'
        elif T in ('T1','T2'): stage='5'
        elif T=='T4': stage='3'
        else: stage='2'
        score=( {'T1':95,'T2':85,'T3':68,'T4':50,'T5':20}.get(T,40)+{'S1':90,'S2':88,'S3':62,'S4':95,'S5':78,'S6':20}.get(S,45)+{'V1':78,'V2':60,'V3':20,'V4':68,'V5':96,'V0':45}.get(V,45)+{'M3':92,'M4':86,'M5':80,'M1':70,'M0':35}.get(M,40)+{'L1':55,'L2':65,'L3':72,'L4':65,'L5':60}.get(L,50))/5
        rows.append([T,S,V,M,L,X,stage,hh,hl,lh,ll,prev_h,prev_l,breakout,pos,score])
    cols=['Trend','Structure','VolumeState','MomentumState','PositionState','Trigger','Stage','HH','HL','LH','LL','LastSwingHigh','LastSwingLow','BreakoutLevel','Position250','TechnicalScore']
    for j,c in enumerate(cols): d[c]=[x[j] for x in rows]
    return d

def market_regime(index_df):
    d=add_base(index_df.copy())
    r=d.iloc[-1]
    if r.Close>r.MA20>r.MA60 and r.Slope20>0 and r.Slope60>0: return 'E1 强势'
    if r.Close>r.MA60 and abs(r.Slope20)<.005: return 'E2 偏强震荡'
    if abs(r.Slope20)<.005 and abs(r.Slope60)<.005: return 'E3 中性震荡'
    if r.Close<r.MA20 and r.Close>r.MA60: return 'E4 偏弱'
    return 'E5 下跌'

def explain(r, weekly=None, intraday=None):
    x=[f"日线：{r.Trend}/{r.Structure}/{r.VolumeState}/{r.MomentumState}/{r.PositionState}/{r.Trigger}",f"Stage={r.Stage}，技术评分={r.TechnicalScore:.1f}"]
    if pd.notna(r.RVOL): x.append(f"RVOL={r.RVOL:.2f}")
    if pd.notna(r.LastSwingHigh): x.append(f"最近确认结构高点={r.LastSwingHigh:.2f}")
    if pd.notna(r.LastSwingLow): x.append(f"最近确认结构低点={r.LastSwingLow:.2f}")
    if weekly is not None: x.append(f"周线={weekly.Trend}/{weekly.Structure}")
    if intraday is not None: x.append(f"60分钟={intraday.Trend}/{intraday.Structure}/{intraday.Trigger}")
    return '；'.join(x)
