import streamlit as st
from core.data import db_status

st.set_page_config(page_title='A股技术选股系统 V5.1', layout='wide')
st.title('A股技术选股系统 V5.1')
st.caption('GitHub Actions 自动采集 → SQLite 数据库 → 多周期技术分析底座 → 全市场筛选')
try:
    s=db_status()
    c1,c2,c3,c4=st.columns(4)
    c1.metric('股票数',s['stocks']); c2.metric('日线记录',s['daily_rows']); c3.metric('最新交易日',s['latest'] or '-'); c4.metric('数据库大小',f"{s['db_size_mb']:.1f} MB")
    if s['stocks'] and s['daily_rows']:
        st.success('数据库已就绪。网页端当前不直接请求东方财富/AkShare。')
    else:
        st.warning('数据库尚未就绪，请在 GitHub Actions 运行 Update A-share market data。')
except Exception as e: st.error(f'数据库读取失败：{e}')
st.markdown('### 使用顺序')
st.markdown('1. **个股分析**：输入代码查看 E/T/S/P/V/M/L/X、Stage、关键价位和日/周线。\n2. **全市场筛选**：扫描数据库中的股票，筛选 BREAKOUT / PULLBACK / REVERSAL。\n3. **策略回测**：用信号日收盘、下一交易日开盘执行的规则进行研究。')
