import streamlit as st, plotly.graph_objects as go
from core.data import daily,intraday60
from core.engine import classify,explain

st.title('个股技术分析')
code=st.text_input('输入A股代码',value='300450').strip()
if st.button('刷新分析',type='primary') or code:
    d=daily(code)
    if d.empty: st.error('无法取得该股票行情，请检查代码或数据源。'); st.stop()
    a=classify(d)
    w=classify(d.resample('W-FRI').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum','Amount':'sum'}).dropna())
    m=intraday60(code)
    mi=classify(m) if len(m)>=80 else None
    r=a.iloc[-1]; wr=w.iloc[-1] if len(w) else None; mr=mi.iloc[-1] if mi is not None and len(mi) else None
    st.caption(f"最新数据：{a.index[-1].date()}")
    cols=st.columns(7)
    for c,k,v in zip(cols,['趋势','结构','量价','动量','位置','触发','Stage'],['Trend','Structure','VolumeState','MomentumState','PositionState','Trigger','Stage']): c.metric(k,str(getattr(r,v)))
    st.metric('技术评分',f'{r.TechnicalScore:.1f}')
    st.write(explain(r,wr,mr))
    fig=go.Figure(); fig.add_trace(go.Candlestick(x=a.index[-180:],open=a.Open.tail(180),high=a.High.tail(180),low=a.Low.tail(180),close=a.Close.tail(180),name='K线'))
    for n in [20,60,120]: fig.add_trace(go.Scatter(x=a.index[-180:],y=a[f'MA{n}'].tail(180),name=f'MA{n}'))
    fig.update_layout(height=560,xaxis_rangeslider_visible=False); st.plotly_chart(fig,use_container_width=True)
    c1,c2,c3,c4=st.columns(4)
    c1.metric('最新价',f'{r.Close:.2f}'); c2.metric('RVOL',f'{r.RVOL:.2f}' if r.RVOL==r.RVOL else '-'); c3.metric('突破位',f'{r.BreakoutLevel:.2f}' if r.BreakoutLevel==r.BreakoutLevel else '-'); c4.metric('250日位置',f'{r.Position250:.0%}' if r.Position250==r.Position250 else '-')
    st.subheader('多周期状态'); st.dataframe({'周期':['周线','日线','60分钟'],'趋势':[wr.Trend if wr is not None else '-',r.Trend,mr.Trend if mr is not None else '数据不足'],'结构':[wr.Structure if wr is not None else '-',r.Structure,mr.Structure if mr is not None else '数据不足'],'触发':['-',r.Trigger,mr.Trigger if mr is not None else '-']},use_container_width=True,hide_index=True)
