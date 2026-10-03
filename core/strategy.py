import pandas as pd

def signal(row, strategy):
    if strategy=='BREAKOUT': return row.Trend in ('T1','T2') and row.Structure in ('S3','S4','S1') and row.VolumeState in ('V1','V5') and row.MomentumState in ('M3','M4','M5') and row.Trigger in ('X1','X2')
    if strategy=='PULLBACK': return row.Trend in ('T1','T2') and row.Structure=='S2' and row.VolumeState in ('V4','V2') and row.Trigger=='X3'
    if strategy=='REVERSAL': return row.Structure=='S5' and row.PositionState in ('L1','L2') and row.Trigger=='X5'
    return False

def backtest(df, strategy, horizon=20):
    rows=[]
    for i in range(len(df)-horizon-1):
        r=df.iloc[i]
        if signal(r,strategy):
            entry=df.iloc[i+1].Open; exitp=df.iloc[i+1+horizon].Close
            ret=exitp/entry-1
            rows.append({'SignalDate':df.index[i],'EntryDate':df.index[i+1],'Entry':entry,'Exit':exitp,'Return':ret})
    out=pd.DataFrame(rows)
    if len(out)==0: return out,{}
    s=out.Return
    stats={'Signals':len(out),'WinRate':float((s>0).mean()),'AvgReturn':float(s.mean()),'MedianReturn':float(s.median()),'P5':float(s.quantile(.05)),'P95':float(s.quantile(.95)),'MaxLoss':float(s.min())}
    return out,stats
