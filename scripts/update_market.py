import argparse
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "market.db"


def session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        }
    )
    return s


def stock_list():
    # 优先直接读取已经存在的 SQLite 股票池
    if DB.exists():
        try:
            with sqlite3.connect(DB) as con:
                df = pd.read_sql_query(
                    "select code,name from stocks where code is not null",
                    con,
                )

            if len(df) > 100:
                print("using cached stock universe", len(df))
                return df
        except Exception as e:
            print("cached stock universe failed:", repr(e))

    # 只有数据库完全没有股票池时，才尝试东方财富
    # 正常情况下不会走这里
    url = "https://82.push2.eastmoney.com/api/qt/clist/get"

    p = {
        "pn": 1,
        "pz": 6000,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f12,f14",
    }

    r = session().get(url, params=p, timeout=20)
    r.raise_for_status()

    j = r.json()
    rows = (j.get("data") or {}).get("diff") or []

    return pd.DataFrame(
        [{"code": x.get("f12"), "name": x.get("f14")} for x in rows]
    )


def tx_code(code):
    code = str(code).zfill(6)

    if code.startswith(("600", "601", "603", "605", "688", "689")):
        return "sh" + code

    return "sz" + code


def fetch(code, days=10):
    tc = tx_code(code)

    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    p = {
        "param": f"{tc},day,,,{min(max(days, 1), 640)},qfq"
    }

    r = session().get(url, params=p, timeout=20)
    r.raise_for_status()

    j = r.json()

    data = (
        j.get("data", {})
        .get(tc, {})
    )

    rows = data.get("qfqday") or data.get("day") or []

    if not rows:
        return pd.DataFrame()

    result = []

    for row in rows:
        if len(row) < 6:
            continue

        result.append(
            {
                "date": row[0],
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]),
            }
        )

    if not result:
        return pd.DataFrame()

    df = pd.DataFrame(result)

    df["code"] = str(code).zfill(6)

    return df


def main(days, workers):

    stocks = stock_list()

    print("stocks", len(stocks))

    if stocks.empty:
        raise RuntimeError("stock universe is empty")

    # 如果数据库已经有大量历史数据，
    # 默认只增量抓取最近10个交易日。
    existing_rows = 0

    if DB.exists():
        try:
            with sqlite3.connect(DB) as con:
                existing_rows = con.execute(
                    "select count(*) from daily"
                ).fetchone()[0]
        except Exception:
            existing_rows = 0

    if existing_rows > 100000 and days >= 420:
        days = 10

    print("update days", days)
    print("workers", workers)
    print("existing daily rows", existing_rows)

    all_data = []

    def worker(code):
        try:
            df = fetch(code, days)

            if df.empty:
                return None

            return df

        except Exception as e:
            print("FAILED", code, repr(e))
            return None

    with ThreadPoolExecutor(max_workers=workers) as ex:

        futures = {
            ex.submit(worker, code): code
            for code in stocks["code"].dropna().astype(str)
        }

        for i, future in enumerate(as_completed(futures), 1):

            df = future.result()

            if df is not None and not df.empty:
                all_data.append(df)

            if i % 100 == 0:
                print("progress", i, "/", len(futures))

            # 腾讯公开接口没有 SLA，稍微降低请求压力
            time.sleep(0.01)

    if not all_data:
        raise RuntimeError("No market data fetched")

    market = pd.concat(all_data, ignore_index=True)

    market["date"] = pd.to_datetime(market["date"])

    market = market.drop_duplicates(
        subset=["code", "date"]
    )

    market = market.sort_values(
        ["code", "date"]
    )

    DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB) as con:

        # 股票池
        stocks.to_sql(
            "stocks",
            con,
            if_exists="replace",
            index=False,
        )

        # 日线数据
        market.to_sql(
            "daily",
            con,
            if_exists="append",
            index=False,
        )

    print("saved rows", len(market))


if __name__ == "__main__":

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--days",
        type=int,
        default=10,
    )

    ap.add_argument(
        "--workers",
        type=int,
        default=4,
    )

    args = ap.parse_args()

    main(
        args.days,
        args.workers,
    )
