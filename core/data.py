from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    return con


def db_ready() -> bool:
    if not DB_PATH.exists():
        return False
    try:
        with connect() as con:
            names = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        return {'stocks', 'daily'}.issubset(names)
    except Exception:
        return False


def list_stocks(query: str = "", limit: int | None = None) -> pd.DataFrame:
    sql = "select code, name from stocks"
    params = []
    if query:
        sql += " where code like ? or name like ?"
        q = f"%{query}%"
        params += [q, q]
    sql += " order by code"
    if limit:
        sql += " limit ?"
        params.append(limit)
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)


def load_daily(code: str, limit: int = 420) -> pd.DataFrame:
    with connect() as con:
        df = pd.read_sql_query(
            "select trade_date, open, high, low, close, volume, amount, pct_chg "
            "from daily where code=? order by trade_date desc limit ?",
            con, params=(str(code).zfill(6), limit))
    if df.empty:
        return df
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values("trade_date").reset_index(drop=True)


def load_weekly(code: str, limit: int = 160) -> pd.DataFrame:
    d = load_daily(code, min(limit * 6, 800))
    if d.empty:
        return d
    d = d.set_index("trade_date")
    w = d.resample("W-FRI").agg({
        "open":"first", "high":"max", "low":"min", "close":"last",
        "volume":"sum", "amount":"sum"
    }).dropna(subset=["close"]).reset_index()
    return w.tail(limit).reset_index(drop=True)


def stock_name(code: str) -> str:
    with connect() as con:
        row = con.execute("select name from stocks where code=? limit 1", (str(code).zfill(6),)).fetchone()
    return row[0] if row else ""


def db_status() -> dict:
    if not DB_PATH.exists():
        return {"stocks":0,"daily_rows":0,"latest":None,"db_size_mb":0.0}
    with connect() as con:
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        if not {'stocks','daily'}.issubset(tables):
            return {"stocks":0,"daily_rows":0,"latest":None,"db_size_mb":DB_PATH.stat().st_size/1024/1024}
        stocks = con.execute("select count(*) from stocks").fetchone()[0]
        rows = con.execute("select count(*) from daily").fetchone()[0]
        latest = con.execute("select max(trade_date) from daily").fetchone()[0]
    return {"stocks":stocks,"daily_rows":rows,"latest":latest,"db_size_mb":DB_PATH.stat().st_size/1024/1024}
