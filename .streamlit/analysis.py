import streamlit as st
import plotly.graph_objects as go
from core.data import load_daily
from core.engine import analyze

st.title('个股分析')
code=st.text_input('股票代码','300450').strip()
if st.button('刷新分析',type='primary'):
    df=load_daily(code,420)
    if df.empty: st.error('数据库中没有该股票数据，请先运行 GitHub Actions 更新行情。')
    else:
        d,state=analyze(df); r=d.iloc[-1]
        st.subheader(f'{code} · 技术状态')
        cols=st.columns(5)
        for col,(k,v) in zip(cols,list(state.items())[:5]): col.metric(k,v)
        cols=st.columns(5)
        for col,(k,v) in zip(cols,list(state.items())[5:10]): col.metric(k,v)
        st.write('策略：',state['strategy'],'｜ Stage：',state['Stage'])
        fig=go.Figure(data=[go.Candlestick(x=d.trade_date,open=d.open,high=d.high,low=d.low,close=d.close),go.Scatter(x=d.trade_date,y=d.ma20,name='MA20'),go.Scatter(x=d.trade_date,y=d.ma60,name='MA60')])
        fig.update_layout(height=560,xaxis_rangeslider_visible=False)
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(d.tail(30),use_container_width=True)
