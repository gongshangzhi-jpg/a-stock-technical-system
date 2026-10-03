# A股技术分析底座 V4.0

目标：云端可部署的 A 股技术分析系统。

## 功能
- 自动A股股票池
- AkShare主数据源 + Yahoo Finance fallback
- 日线、周线、60分钟多周期
- E/T/S/P/V/M/L/X技术状态
- HH/HL/LH/LL结构
- Stage阶段
- BREAKOUT / PULLBACK / REVERSAL筛选
- 5/10/20/60日基础回测
- Plotly交互K线

## 本地运行
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 云端部署
项目可直接放入GitHub仓库，然后在 Streamlit Community Cloud 创建应用，入口选择 `streamlit_app.py`。Community Cloud 支持从GitHub选择仓库、分支和入口文件，并提供 `streamlit.app` URL；Python依赖由 `requirements.txt` 安装。

## 重要说明
1. 行情数据依赖第三方数据源，可能存在延迟、限流或缺失。
2. 60分钟数据不可用时系统显示数据不足，不用日线伪造60分钟。
3. 全市场扫描应控制扫描数量并依赖缓存，避免频繁请求数据源。
4. 技术评分用于排序和研究，不构成投资建议。
