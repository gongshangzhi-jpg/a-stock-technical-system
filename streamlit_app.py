import streamlit as st
from core.data import db_status

st.set_page_config(page_title='A股技术选股系统 V5.0', layout='wide')
st.title('A股技术选股系统 V5.0')
st.caption('GitHub Actions 采集行情 → SQLite → Streamlit 技术分析底座')
try:
    s=db_status(); c1,c2,c3=st.columns(3); c1.metric('股票数',s['stocks']); c2.metric('日线记录',s['daily_rows']); c3.metric('最新交易日',s['latest'] or '-')
except Exception as e: st.error(f'数据库读取失败：{e}')
st.info('请从左侧进入“个股分析”或“全市场筛选”。如果刚部署，请先在 GitHub Actions 手动运行 Update A-share market data。')
