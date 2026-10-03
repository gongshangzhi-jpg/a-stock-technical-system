import streamlit as st
from core.data import daily
from core.engine import classify
from core.strategy import backtest
st.title('策略回测')
code=st.text_input('股票代码',value='300450'); strategy=st.selectbox('策略',['BREAKOUT','PULLBACK','REVERSAL']); horizon=st.selectbox('持有期',[5,10,20,60],index=2)
if st.button('开始回测',type='primary'):
    d=classify(daily(code))
    trades,stats=backtest(d,strategy,horizon)
    if not stats: st.warning('历史上没有满足条件的信号。')
    else:
        c=st.columns(6); labels=[('信号数','Signals'),('胜率','WinRate'),('平均收益','AvgReturn'),('中位数','MedianReturn'),('P5','P5'),('最大亏损','MaxLoss')]
        for col,(lab,key) in zip(c,labels):
            v=stats[key]; col.metric(lab,f'{v:.1%}' if key!='Signals' else str(v))
        st.dataframe(trades,use_container_width=True,hide_index=True)
