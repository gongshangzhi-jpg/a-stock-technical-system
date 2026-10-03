import streamlit as st
st.set_page_config(page_title='A股技术分析底座 V4.0', page_icon='📈', layout='wide')
pages={'主界面':[st.Page('pages/dashboard.py',title='首页',icon='🏠',default=True)],'分析':[st.Page('pages/analysis.py',title='个股分析',icon='📈')],'选股':[st.Page('pages/screener.py',title='全市场筛选',icon='🔎')],'研究':[st.Page('pages/backtest.py',title='策略回测',icon='📊'),st.Page('pages/rules.py',title='规则字典',icon='📚')]}
st.navigation(pages).run()
