import streamlit as st
from core.data import universe
st.title('A股技术分析底座 V4.0')
st.caption('云端部署版：自动行情 + 周线/日线/60分钟多周期 + E/T/S/P/V/M/L/X + 策略筛选')
u=universe()
c1,c2,c3=st.columns(3); c1.metric('A股股票池',f'{len(u):,}'); c2.metric('数据模式','AkShare / Yahoo fallback'); c3.metric('多周期','周线 · 日线 · 60分钟')
st.info('使用左侧菜单进入个股分析或全市场筛选。云端部署后无需本地安装 Python。')
st.markdown('### 系统结构')
st.code('行情 → 多周期技术底座 → E/T/S/P/V/M/L/X → Stage → BREAKOUT/PULLBACK/REVERSAL → 筛选/回测')
