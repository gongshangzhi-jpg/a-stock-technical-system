import streamlit as st
import pandas as pd
from core.data import list_stocks, load_daily
from core.engine import analyze

st.title('全市场筛选')
st.caption('初版采用数据库内日线计算；运行后可按策略与状态过滤。')
strategy=st.selectbox('策略',['全部','BREAKOUT','PULLBACK','REVERSAL'])
limit=st.slider('扫描股票数量',50,3000,500,50)
if st.button('开始扫描',type='primary'):
    stocks=list_stocks().head(limit); rows=[]; bar=st.progress(0)
    for i,rec in stocks.iterrows():
        d=load_daily(str(rec.code),420)
        if len(d)<80: continue
        _,s=analyze(d)
        if strategy!='全部' and s['strategy']!=strategy: continue
        r=d.iloc[-1]
        rows.append({'代码':rec.code,'名称':rec.get('name',''),'收盘':r.close,'策略':s['strategy'],'Stage':s['Stage'],'T':s['T'],'S':s['S'],'V':s['V'],'M':s['M'],'X':s['X'],'RVOL':r.rvol20})
        bar.progress((i+1)/max(len(stocks),1))
    out=pd.DataFrame(rows)
    if out.empty: st.warning('没有匹配结果。')
    else: st.dataframe(out.sort_values(['策略','RVOL'],ascending=[True,False]),use_container_width=True)
