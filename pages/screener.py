import streamlit as st
import pandas as pd
from core.data import list_stocks, load_daily
from core.engine import analyze

st.title('全市场筛选')
st.caption('扫描 GitHub Actions 已更新的本地 SQLite 日线数据库。')
strategy=st.selectbox('策略',['全部','BREAKOUT','PULLBACK','REVERSAL'])
limit=st.slider('扫描股票数量',50,6000,1000,50)
if st.button('开始扫描',type='primary'):
    stocks=list_stocks(limit=limit); rows=[]; bar=st.progress(0)
    for n,rec in enumerate(stocks.itertuples(index=False),1):
        d=load_daily(str(rec.code),420)
        if len(d)<80: bar.progress(n/len(stocks)); continue
        ed,s=analyze(d); r=ed.iloc[-1]
        if strategy!='全部' and s['strategy']!=strategy: bar.progress(n/len(stocks)); continue
        rows.append({'代码':str(rec.code).zfill(6),'名称':rec.name,'收盘':r.close,'策略':s['strategy'],'Stage':s['Stage'],'T':s['T'],'S':s['S'],'V':s['V'],'M':s['M'],'X':s['X'],'RVOL':r.rvol20,'20日收益':r.ret20,'60日收益':r.ret60})
        bar.progress(n/len(stocks))
    out=pd.DataFrame(rows)
    if out.empty: st.warning('没有匹配结果。')
    else:
        out=out.sort_values(['策略','RVOL'],ascending=[True,False])
        st.metric('候选数量',len(out)); st.dataframe(out,use_container_width=True)
