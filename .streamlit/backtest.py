import streamlit as st
from core.data import load_daily
from core.strategy import backtest

st.title('策略回测')
code=st.text_input('股票代码','300450'); strategy=st.selectbox('策略',['BREAKOUT','PULLBACK','REVERSAL']); horizon=st.selectbox('持有期',[5,10,20,60],index=2)
if st.button('运行回测',type='primary'):
    d=load_daily(code,420)
    if d.empty: st.error('数据库中没有该股票数据。')
    else:
        r=backtest(d,strategy,horizon); a,b,c,d1=st.columns(4); a.metric('信号数',r['signals']); b.metric('胜率','-' if r['win_rate'] is None else f"{r['win_rate']:.1%}"); c.metric('平均收益','-' if r['avg_return'] is None else f"{r['avg_return']:.2%}"); d1.metric('中位数','-' if r['median_return'] is None else f"{r['median_return']:.2%}")
        st.caption('信号日收盘后，t+1开盘执行；这是研究工具，不构成交易建议。')
