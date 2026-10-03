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
    # Prefer the stock universe already stored in market.db. This avoids the
    # Eastmoney clist endpoint, which can reject GitHub Actions runner IPs.
    if DB.exists():
        try:
            with sqlite3.connect(DB) as con:
                df=pd.read_sql_query('select code,name from stocks where code is not null',con)
            if len(df) > 100:
                print('using cached stock universe',len(df))
                return df
        except Exception as e:
            print('cached stock universe unavailable:',e)
    # Fallback only for a brand-new database.
    url='https://82.push2.eastmoney.com/api/qt/clist/get'; p={'pn':1,'pz':6000,'po':1,'np':1,'fltt':2,'invt':2,'fid':'f3','fs':'m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23','fields':'f12,f14,f2,f3,f4'}
    r=session().get(url,params=p,timeout=25); r.raise_for_status(); j=r.json(); rows=(j.get('data') or {}).get('diff') or []
    return pd.DataFrame([{'code':str(x.get('f12')).zfill(6),'name':x.get('f14')} for x in rows if x.get('f12')])

def tencent_code(code):
    c=str(code).zfill(6)
    return ('sh' if c.startswith(('6','68','69')) else 'sz') + c

def fetch(code, days):
    # Tencent public K-line endpoint is used as the primary fallback because
    # Eastmoney history is intermittently unreachable from cloud runners.
    tc=tencent_code(code)
    url='https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
    p={'param':f'{tc},day,,,{min(max(days,1),640)},qfq'}
    last=None
    for k in range(3):
        try:
            r=requests.get(url,params=p,headers={'User-Agent':UA,'Accept':'application/json,text/plain,*/*','Referer':'https://finance.qq.com/'},timeout=20)
            r.raise_for_status(); j=r.json(); node=(j.get('data') or {}).get(tc) or {}
            ks=node.get('qfqday') or node.get('day') or []
            out=[]
            for a in ks:
                if len(a)>=6:
                    out.append({'code':code,'trade_date':a[0],'open':a[1],'close':a[2],'high':a[3],'low':a[4],'volume':a[5],'amount':None,'pct_chg':None})
            if out:
                df=pd.DataFrame(out)
                df['close']=pd.to_numeric(df['close'],errors='coerce'); prev=df['close'].shift(1)
                df['pct_chg']=((df['close']/prev-1)*100).where(prev.notna())
                return df
            raise RuntimeError('Tencent returned no K-line rows')
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
    DB.parent.mkdir(parents=True,exist_ok=True)
    existing_rows=0
    if DB.exists():
        try:
            with sqlite3.connect(DB) as con:
                existing_rows=con.execute("select count(*) from sqlite_master where type='table' and name='daily'").fetchone()[0]
                if existing_rows:
                    existing_rows=con.execute('select count(*) from daily').fetchone()[0]
        except Exception:
            existing_rows=0
    if existing_rows > 100000 and days >= 420:
        days=10
        print('existing database detected; incremental update days=10')
    stocks=stock_list(); print('stocks',len(stocks))
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
    ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=10); ap.add_argument('--workers',type=int,default=4); a=ap.parse_args(); main(a.days,a.workers)
