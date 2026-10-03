from __future__ import annotations
import argparse, sqlite3, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'market.db'
UA = 'Mozilla/5.0 (compatible; AStockTechnicalBot/5.0)'

def secid(code):
    return f"1.{code}" if code.startswith(('6','68','69')) else f"0.{code}"

def session():
    s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept':'application/json,text/plain,*/*'}); return s

def stock_list():
    url='https://82.push2.eastmoney.com/api/qt/clist/get'
    p={'pn':1,'pz':6000,'po':1,'np':1,'fltt':2,'invt':2,'fid':'f3','fs':'m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23','fields':'f12,f14,f2,f3,f4'}
    r=session().get(url,params=p,timeout=20); r.raise_for_status(); j=r.json(); rows=(j.get('data') or {}).get('diff') or []
    return pd.DataFrame([{'code':x.get('f12'),'name':x.get('f14')} for x in rows if x.get('f12')])

def fetch(code, days):
    url='https://push2his.eastmoney.com/api/qt/stock/kline/get'
    p={'fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116','ut':'7eea3edcaed734bea9cbfc24409ed989','klt':101,'fqt':1,'secid':secid(code),'beg':'20200101','end':'20991231','lmt':days}
    last=None
    for k in range(3):
        try:
            r=session().get(url,params=p,timeout=20); r.raise_for_status(); j=r.json(); ks=(j.get('data') or {}).get('klines') or []
            out=[]
            for x in ks:
                a=x.split(',')
                if len(a)>=7: out.append({'code':code,'trade_date':a[0],'open':a[1],'close':a[2],'high':a[3],'low':a[4],'volume':a[5],'amount':a[6],'pct_chg':a[8] if len(a)>8 else None})
            return pd.DataFrame(out)
        except Exception as e: last=e; time.sleep(1.5*(k+1))
    raise last

def main(days, workers):
    DB.parent.mkdir(parents=True,exist_ok=True)
    stocks=stock_list(); print('stocks',len(stocks))
    con=sqlite3.connect(DB); stocks.to_sql('stocks',con,if_exists='replace',index=False); con.execute('create index if not exists idx_stocks_code on stocks(code)'); con.commit(); con.close()
    ok=fail=0
    with sqlite3.connect(DB) as con:
        con.execute('''create table if not exists daily(code text, trade_date text, open real, high real, low real, close real, volume real, amount real, pct_chg real, primary key(code,trade_date))''')
        con.commit()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs={ex.submit(fetch,c,days):c for c in stocks.code.astype(str)}
        for fut in as_completed(futs):
            code=futs[fut]
            try:
                df=fut.result()
                if not df.empty:
                    with sqlite3.connect(DB) as con: df.to_sql('daily',con,if_exists='append',index=False)
                ok+=1
            except Exception as e:
                fail+=1; print('FAIL',code,type(e).__name__,str(e)[:160])
    with sqlite3.connect(DB) as con:
        con.execute('create index if not exists idx_daily_code_date on daily(code,trade_date)'); con.commit()
    print('done ok=',ok,'fail=',fail)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=420); ap.add_argument('--workers',type=int,default=8); a=ap.parse_args(); main(a.days,a.workers)
