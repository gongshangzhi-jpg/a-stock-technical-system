import streamlit as st
import plotly.graph_objects as go
from core.data import load_daily, load_weekly, stock_name, db_status
from core.engine import analyze

st.title('个股分析')
st.caption('行情来自 GitHub Actions 更新的 SQLite 数据库；网页端不直接访问东方财富。')
code=st.text_input('股票代码','300450').strip().zfill(6)
if st.button('刷新分析',type='primary'):
    d=load_daily(code,420)
    if d.empty:
        st.error('数据库中没有该股票数据，请先运行 GitHub Actions 更新行情。')
    else:
        ed,state=analyze(d); r=ed.iloc[-1]; name=stock_name(code)
        st.subheader(f'{code} {name} · 技术状态')
        cols=st.columns(5)
        for col,k in zip(cols,['E','T','S','P','V']): col.metric(k,state[k])
        cols=st.columns(5)
        for col,k in zip(cols,['M','L','X','Stage','strategy']): col.metric(k,state[k])
        a,b,c,d1=st.columns(4)
        a.metric('收盘',f"{r.close:.2f}"); b.metric('RVOL20',f"{r.rvol20:.2f}x"); c.metric('20日收益',f"{r.ret20:.2%}"); d1.metric('60日收益',f"{r.ret60:.2%}")
        levels={
            '20日突破位':r.high20,'60日压力':r.high60,'20日支撑':r.low20,'60日支撑':r.low60,'MA20':r.ma20,'MA60':r.ma60,'ATR14':r.atr14
        }
        st.markdown('#### 关键价位')
        st.dataframe(__import__('pandas').DataFrame([levels]).T.rename(columns={0:'数值'}).round(2),use_container_width=True)
        st.markdown('#### 日线')
        fig=go.Figure([go.Candlestick(x=ed.trade_date,open=ed.open,high=ed.high,low=ed.low,close=ed.close,name='K线'),go.Scatter(x=ed.trade_date,y=ed.ma20,name='MA20'),go.Scatter(x=ed.trade_date,y=ed.ma60,name='MA60')])
        fig.update_layout(height=560,xaxis_rangeslider_visible=False)
        st.plotly_chart(fig,use_container_width=True)
        w=load_weekly(code,120)
        if not w.empty:
            st.markdown('#### 周线')
            st.line_chart(w.set_index('trade_date')['close'])
        st.markdown('#### 最近30个交易日')
        st.dataframe(ed.tail(30),use_container_width=True)
