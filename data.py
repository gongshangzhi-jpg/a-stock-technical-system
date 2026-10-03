import time
import pandas as pd
import streamlit as st

try:
    import akshare as ak
except Exception:
    ak = None

try:
    import yfinance as yf
except Exception:
    yf = None


def _norm(df):
    if df is None or len(df)==0: return pd.DataFrame()
    m={'日期':'Date','开盘':'Open','收盘':'Close','最高':'High','最低':'Low','成交量':'Volume','成交额':'Amount','时间':'Date'}
    x=df.rename(columns=m).copy()
    for c in ['Date','Open','High','Low','Close','Volume']:
        if c not in x: return pd.DataFrame()
    x['Date']=pd.to_datetime(x['Date'])
    for c in ['Open','High','Low','Close','Volume']:
        x[c]=pd.to_numeric(x[c],errors='coerce')
    if 'Amount' not in x: x['Amount']=x['Close']*x['Volume']
    return x[['Date','Open','High','Low','Close','Volume','Amount']].dropna(subset=['Date','Close']).sort_values('Date').drop_duplicates('Date').set_index('Date')


def _yf_symbol(code):
    code=str(code).zfill(6)
    if code.startswith(('6','68','60')): return code+'.SS'
    return code+'.SZ'

@st.cache_data(ttl=3600, show_spinner=False)
def daily(code, start='20200101'):
    code=str(code).zfill(6)
    if ak:
        try:
            x=ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start, adjust='qfq')
            n=_norm(x)
            if len(n)>0: return n
        except Exception:
            pass
    if yf:
        try:
            x=yf.download(_yf_symbol(code), start=pd.to_datetime(start).strftime('%Y-%m-%d'), auto_adjust=False, progress=False)
            if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
            x=x.reset_index().rename(columns={'Adj Close':'Close'})
            return _norm(x)
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def intraday60(code, days=30):
    code=str(code).zfill(6)
    if ak:
        try:
            sym=('sh' if code.startswith('6') else 'sz')+code
            x=ak.stock_zh_a_minute(symbol=sym, period='60', adjust='qfq')
            n=_norm(x)
            if len(n): return n.tail(max(200,days*8))
        except Exception:
            pass
    if yf:
        try:
            x=yf.download(_yf_symbol(code), period='30d', interval='60m', auto_adjust=False, progress=False)
            if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
            x=x.reset_index().rename(columns={'Datetime':'Date','Adj Close':'Close'})
            return _norm(x)
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def universe():
    if ak:
        try:
            x=ak.stock_zh_a_spot_em()
            ren={'代码':'Code','名称':'Name','总市值':'MarketCap','流通市值':'FloatCap'}
            x=x.rename(columns=ren)
            cols=[c for c in ['Code','Name','MarketCap','FloatCap'] if c in x]
            x=x[cols].copy()
            x['Code']=x['Code'].astype(str).str.zfill(6)
            for c in ['MarketCap','FloatCap']:
                if c in x: x[c]=pd.to_numeric(x[c],errors='coerce')
            return x.drop_duplicates('Code')
        except Exception:
            pass
    return pd.DataFrame(columns=['Code','Name','MarketCap','FloatCap'])
