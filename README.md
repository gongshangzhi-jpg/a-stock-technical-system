# A股技术选股系统 V5.1

数据链：GitHub Actions → 东方财富行情采集 → SQLite `data/market.db` → Streamlit。

网页端只读取数据库，不直接请求东方财富/AkShare。

## GitHub Actions
- `Update A-share market data` 可手动运行。
- 工作日 UTC 08:30 自动运行，即北京时间 16:30。
- 数据以 SQLite 主键 `(code, trade_date)` upsert，重复运行不会因重复主键失败。

## Streamlit
- 个股分析：日线、周线、E/T/S/P/V/M/L/X、Stage、关键价位。
- 全市场筛选：BREAKOUT / PULLBACK / REVERSAL。
- 策略回测：t日收盘产生信号，t+1开盘执行。

> GitHub 仓库不建议长期保存超大数据库。如果 `market.db` 接近 GitHub 单文件限制，应迁移到对象存储或数据库服务。
