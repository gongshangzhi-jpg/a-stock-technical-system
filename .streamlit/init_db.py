from pathlib import Path
import sqlite3
DB=Path(__file__).resolve().parents[1]/'data'/'market.db'
DB.parent.mkdir(exist_ok=True)
con=sqlite3.connect(DB)
con.execute('create table if not exists stocks(code text primary key,name text)')
con.execute('create table if not exists daily(code text, trade_date text, open real, high real, low real, close real, volume real, amount real, pct_chg real, primary key(code,trade_date))')
con.commit(); con.close(); print(DB)
