from __future__ import annotations
import argparse, sqlite3, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data'/'market.db'; UA='Mozilla/5.0 (compatible; AStockTechnicalBot/5.1)'

def secid(code): return f'1.{code}' if str(code).startswith(('6','68','69')) else f'0.{code}'
def session():
    s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept':'application/json,text/plain,*/*','Referer':'https://quote.eastmoney.com/'}); return s

def stock_list():
    url='https://82.push2.eastmoney.com/api/qt/clist/get'; p={'pn':1,'pz':6000,'po':1,'np':1,'fltt':2,'invt':2,'fid':'f3','fs':'m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23','fields':'f12,f14,f2,f3,f4'}
    r=session().get(url,params=p,timeout=25); r.raise_for_status(); j=r.json(); rows=(j.get('data') or {}).get('diff') or []
    return pd.DataFrame([{'code':str(x.get('f12')).zfill(6),'name':x.get('f14')} for x in rows if x.get('f12')])

def fetch(code, days):
    url='https://push2his.eastmoney.com/api/qt/stock/kline/get'; p={'fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116','ut':'7eea3edcaed734bea9cbfc24409ed989','klt':101,'fqt':1,'secid':secid(code),'beg':'20200101','end':'20991231','lmt':days}
    last=None
    for k in range(3):
        try:
            r=session().get(url,params=p,timeout=25); r.raise_for_status(); j=r.json(); ks=(j.get('data') or {}).get('klines') or []; out=[]
            for x in ks:
                a=x.split(',')
                if len(a)>=7: out.append({'code':code,'trade_date':a[0],'open':a[1],'close':a[2],'high':a[3],'low':a[4],'volume':a[5],'amount':a[6],'pct_chg':a[8] if len(a)>8 else None})
            return pd.DataFrame(out)
        except Exception as e: last=e; time.sleep(1.5*(k+1))
    raise last

def init_db(con):
    con.execute('create table if not exists stocks(code text primary key,name text)')
    con.execute('''create table if not exists daily(code text,trade_date text,open real,high real,low real,close real,volume real,amount real,pct_chg real,primary key(code,trade_date))''')
    con.execute('create index if not exists idx_daily_code_date on daily(code,trade_date)'); con.commit()

def upsert_df(con,df):
    if df.empty:return
    con.executemany('''insert into daily(code,trade_date,open,high,low,close,volume,amount,pct_chg) values(?,?,?,?,?,?,?,?,?) on conflict(code,trade_date) do update set open=excluded.open,high=excluded.high,low=excluded.low,close=excluded.close,volume=excluded.volume,amount=excluded.amount,pct_chg=excluded.pct_chg''', [tuple(x) for x in df[['code','trade_date','open','high','low','close','volume','amount','pct_chg']].itertuples(index=False,name=None)])

def main(days,workers):
    DB.parent.mkdir(parents=True,exist_ok=True); stocks=stock_list(); print('stocks',len(stocks))
    with sqlite3.connect(DB) as con:
        init_db(con); con.executemany('insert into stocks(code,name) values(?,?) on conflict(code) do update set name=excluded.name',stocks[['code','name']].itertuples(index=False,name=None)); con.commit()
    ok=fail=0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs={ex.submit(fetch,c,days):c for c in stocks.code.astype(str)}
        for fut in as_completed(futs):
            code=futs[fut]
            try:
                df=fut.result()
                with sqlite3.connect(DB) as con: upsert_df(con,df); con.commit()
                ok+=1
            except Exception as e: fail+=1; print('FAIL',code,type(e).__name__,str(e)[:180])
    with sqlite3.connect(DB) as con:
        init_db(con)
        n=con.execute('select count(*) from daily').fetchone()[0]; latest=con.execute('select max(trade_date) from daily').fetchone()[0]
    print(f'done ok={ok} fail={fail} daily_rows={n} latest={latest}')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=420); ap.add_argument('--workers',type=int,default=8); a=ap.parse_args(); main(a.days,a.workers)
