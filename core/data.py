from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def list_stocks() -> pd.DataFrame:
    with connect() as con:
        return pd.read_sql_query("select * from stocks order by code", con)


def load_daily(code: str, limit: int = 420) -> pd.DataFrame:
    with connect() as con:
        df = pd.read_sql_query(
            "select trade_date, open, high, low, close, volume, amount, pct_chg from daily where code=? order by trade_date desc limit ?",
            con, params=(code, limit))
    if df.empty:
        return df
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values("trade_date").reset_index(drop=True)


def db_status() -> dict:
    with connect() as con:
        stocks = con.execute("select count(*) from stocks").fetchone()[0]
        rows = con.execute("select count(*) from daily").fetchone()[0]
        latest = con.execute("select max(trade_date) from daily").fetchone()[0]
    return {"stocks": stocks, "daily_rows": rows, "latest": latest}
