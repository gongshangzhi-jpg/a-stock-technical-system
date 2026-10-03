import streamlit as st, pandas as pd
from core.data import universe,daily
from core.engine import classify
from core.strategy import signal
st.title('全市场技术筛选')
u=universe(); st.caption(f'当前股票池：{len(u):,}')
strategy=st.selectbox('策略',['BREAKOUT','PULLBACK','REVERSAL','不限'])
limit=st.slider('扫描股票数量',20,min(500,len(u)) if len(u)>=20 else 20,100,10)
minscore=st.slider('最低技术评分',0,100,65,5)
if st.button('开始扫描',type='primary'):
    work=u.sort_values('MarketCap',ascending=False).head(limit) if 'MarketCap' in u else u.head(limit)
    rows=[]; bar=st.progress(0)
    for j,(_,item) in enumerate(work.iterrows()):
        d=daily(item.Code)
        if len(d)<80: continue
        a=classify(d); r=a.iloc[-1]
        if r.TechnicalScore<minscore: continue
        ok=signal(r,strategy) if strategy!='不限' else True
        if ok: rows.append({'Code':item.Code,'Name':item.Name,'Score':round(r.TechnicalScore,1),'Trend':r.Trend,'Structure':r.Structure,'Volume':r.VolumeState,'Momentum':r.MomentumState,'Position':r.PositionState,'Trigger':r.Trigger,'Stage':r.Stage,'Close':round(r.Close,2)})
        bar.progress((j+1)/len(work))
    out=pd.DataFrame(rows).sort_values('Score',ascending=False) if rows else pd.DataFrame()
    st.session_state['screen']=out
if 'screen' in st.session_state:
    out=st.session_state['screen']; st.write(f'符合条件：{len(out)}只'); st.dataframe(out,use_container_width=True,hide_index=True)
    if len(out): st.download_button('导出CSV',out.to_csv(index=False).encode('utf-8-sig'),'screen_results.csv','text/csv')
