import time
import requests
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
    if df is None or len(df) == 0:
        return pd.DataFrame()
    m = {
        '日期':'Date','开盘':'Open','收盘':'Close','最高':'High','最低':'Low',
        '成交量':'Volume','成交额':'Amount','时间':'Date','day':'Date',
        'open':'Open','close':'Close','high':'High','low':'Low','volume':'Volume',
        'amount':'Amount'
    }
    x = df.rename(columns=m).copy()
    for c in ['Date','Open','High','Low','Close','Volume']:
        if c not in x:
            return pd.DataFrame()
    x['Date'] = pd.to_datetime(x['Date'], errors='coerce')
    for c in ['Open','High','Low','Close','Volume']:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    if 'Amount' not in x:
        x['Amount'] = x['Close'] * x['Volume']
    return (x[['Date','Open','High','Low','Close','Volume','Amount']]
            .dropna(subset=['Date','Close'])
            .sort_values('Date')
            .drop_duplicates('Date')
            .set_index('Date'))


def _yf_symbol(code):
    code = str(code).zfill(6)
    return code + ('.SS' if code.startswith(('6','68','60')) else '.SZ')


def _eastmoney_daily(code, start='20200101'):
    """Direct Eastmoney K-line request; avoids depending on an AkShare wrapper."""
    code = str(code).zfill(6)
    market = '1' if code.startswith(('6','68')) else '0'
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
        'ut': '7eea3edcaed734bea9cbfc24409ed989',
        'klt': '101',
        'fqt': '1',
        'secid': f'{market}.{code}',
        'beg': str(start),
        'end': '20991231',
        'lmt': '5000',
    }
    r = requests.get(url, params=params, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; AStockTechnicalSystem/4.1)'
    })
    r.raise_for_status()
    payload = r.json()
    data = (payload.get('data') or {}).get('klines') or []
    rows = []
    for item in data:
        p = item.split(',')
        if len(p) < 6:
            continue
        rows.append({
            'Date': p[0], 'Open': p[1], 'Close': p[2],
            'High': p[3], 'Low': p[4], 'Volume': p[5],
            'Amount': p[6] if len(p) > 6 else None,
        })
    return _norm(pd.DataFrame(rows))


@st.cache_data(ttl=3600, show_spinner=False)
def daily(code, start='20200101'):
    code = str(code).strip().zfill(6)
    errors = []

    # 1. Direct Eastmoney first: simple and independent of AkShare internals.
    try:
        n = _eastmoney_daily(code, start)
        if len(n) > 0:
            return n
        errors.append('Eastmoney returned no rows')
    except Exception as e:
        errors.append(f'Eastmoney: {type(e).__name__}: {e}')

    # 2. AkShare fallback.
    if ak:
        try:
            x = ak.stock_zh_a_hist(
                symbol=code, period='daily', start_date=start,
                end_date='20991231', adjust='qfq', timeout=15
            )
            n = _norm(x)
            if len(n) > 0:
                return n
            errors.append('AkShare returned no rows')
        except Exception as e:
            errors.append(f'AkShare: {type(e).__name__}: {e}')

    # 3. Yahoo fallback.
    if yf:
        try:
            x = yf.download(
                _yf_symbol(code),
                start=pd.to_datetime(start).strftime('%Y-%m-%d'),
                auto_adjust=False, progress=False, timeout=15
            )
            if isinstance(x.columns, pd.MultiIndex):
                x.columns = x.columns.get_level_values(0)
            x = x.reset_index().rename(columns={'Adj Close':'Close'})
            n = _norm(x)
            if len(n) > 0:
                return n
            errors.append('Yahoo returned no rows')
        except Exception as e:
            errors.append(f'Yahoo: {type(e).__name__}: {e}')

    # Keep the diagnostic available to the UI/logs instead of silently hiding it.
    daily.last_error = ' | '.join(errors)
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def intraday60(code, days=30):
    code = str(code).strip().zfill(6)
    errors = []

    # Prefer Eastmoney's current minute interface for 60m data.
    try:
        market_code = ('sh' if code.startswith(('6','68')) else 'sz') + code
        start = (pd.Timestamp.now() - pd.Timedelta(days=max(days, 30))).strftime('%Y-%m-%d %H:%M:%S')
        x = ak.stock_zh_a_hist_min_em(
            symbol=code, start_date=start, end_date='2099-12-31 15:00:00',
            period='60', adjust='qfq'
        ) if ak else pd.DataFrame()
        n = _norm(x)
        if len(n):
            return n.tail(max(200, days * 8))
        errors.append('Eastmoney 60m returned no rows')
    except Exception as e:
        errors.append(f'60m Eastmoney/AkShare: {type(e).__name__}: {e}')

    if ak:
        try:
            x = ak.stock_zh_a_minute(symbol=market_code, period='60', adjust='qfq')
            n = _norm(x)
            if len(n):
                return n.tail(max(200, days * 8))
            errors.append('Sina 60m returned no rows')
        except Exception as e:
            errors.append(f'Sina 60m: {type(e).__name__}: {e}')

    if yf:
        try:
            x = yf.download(_yf_symbol(code), period='30d', interval='60m', auto_adjust=False, progress=False, timeout=15)
            if isinstance(x.columns, pd.MultiIndex):
                x.columns = x.columns.get_level_values(0)
            x = x.reset_index().rename(columns={'Datetime':'Date','Adj Close':'Close'})
            n = _norm(x)
            if len(n):
                return n.tail(max(200, days * 8))
            errors.append('Yahoo 60m returned no rows')
        except Exception as e:
            errors.append(f'Yahoo 60m: {type(e).__name__}: {e}')

    intraday60.last_error = ' | '.join(errors)
    return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def universe():
    if ak:
        try:
            x = ak.stock_zh_a_spot_em()
            ren = {'代码':'Code','名称':'Name','总市值':'MarketCap','流通市值':'FloatCap'}
            x = x.rename(columns=ren)
            cols = [c for c in ['Code','Name','MarketCap','FloatCap'] if c in x]
            x = x[cols].copy()
            x['Code'] = x['Code'].astype(str).str.zfill(6)
            for c in ['MarketCap','FloatCap']:
                if c in x:
                    x[c] = pd.to_numeric(x[c], errors='coerce')
            return x.drop_duplicates('Code')
        except Exception:
            pass
    return pd.DataFrame(columns=['Code','Name','MarketCap','FloatCap'])
