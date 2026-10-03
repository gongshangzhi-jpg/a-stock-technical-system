# A股技术选股系统 V5.0

云端版技术分析底座：**GitHub Actions 负责采集行情 → SQLite 保存 → Streamlit 只读分析**。

## 主要能力
- 全市场 A 股股票池自动更新
- 日线行情自动更新
- 周线由日线派生
- 个股技术底座：E/T/S/P/V/M/L/X + Stage
- BREAKOUT / PULLBACK / REVERSAL 策略识别
- 全市场技术筛选器
- 5/10/20/60 日事件回测
- 数据采集与网页解耦：Streamlit 不再直接请求东方财富

## 部署方式
### 1. GitHub
把本项目内容上传到仓库根目录，保持：
```
.github/workflows/update_market.yml
core/
pages/
scripts/
streamlit_app.py
requirements.txt
```

### 2. GitHub Actions
Actions 会在工作日 UTC 07:30 运行（北京时间 15:30），也支持手动 Run workflow。
采集结果写入 `data/market.db` 并自动 commit 回仓库。

### 3. Streamlit Community Cloud
入口：`streamlit_app.py`。
网页只读取仓库中的 SQLite，不直接访问行情网站。

## 本地运行
```bash
pip install -r requirements.txt
python scripts/update_market.py --days 420 --workers 8
streamlit run streamlit_app.py
```

## 注意
- 初版优先保证日线全市场与技术底座稳定；60 分钟数据不进入全市场数据库。
- 60 分钟结构可作为后续候选股增强模块，避免把高频数据写入 GitHub 仓库造成体积快速增长。
- 如果 GitHub 仓库日后超过合适体量，可把 `data/market.db` 迁移到 Supabase/PostgreSQL，网页代码的读取层可以平滑替换。
