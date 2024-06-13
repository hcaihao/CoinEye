from flask import blueprints
from flask import request

import pandas
import ccxt
import datetime
import time

from app import utility
from app import buffer

market_blueprint = blueprints.Blueprint("market", __name__, url_prefix='/market')

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}
# proxies = {
#     'http': 'socks5://127.0.0.1:7890',
#     'https': 'socks5h://127.0.0.1:7890'
# }

exchanges = {
    "binance": ccxt.binance({
        'apiKey': '3mJHu54JKbygBXYS5ArkjuxLMPt64YYdiNcDEXZJnSWu123BBEYf8LQiBCgAkaY2',
        'secret': '8mDQKpTZF7wCmWJJc7ZPqWTExNMamG5vLVkR4fNw5HfVOORFDBA9a3QEf6ueMuhM',
        'proxies': proxies
    }),
    "huobi": ccxt.huobi({
        'apiKey': '5da23294-1qdmpe4rty-649c2fae-352e5',
        'secret': '340d6b39-11f7912b-fd4dc615-60417',
        'proxies': proxies
    }),
    "gate": ccxt.gate({
        'apiKey': 'fa1147d9bb42c91cf81a2fd77d6680d8',
        'secret': '05875cdad3f9b1ca6b1b6849352cd1422cbe51377a680a7c412d104c1b81ae40',
        'proxies': proxies
    }),
    "ftx": ccxt.ftx({
        'apiKey': '_CmbJt63-0riiJlz3T7VDcYmK2bwieK3pvCi8tU9',
        'secret': '41LMD-xqoczx16mGd1VJIs-qlrzB9vDtDfdjbd_O',
        'proxies': proxies
    }),
    "okx": ccxt.okex5({
        'apiKey': '5a81ffd2-8ce6-4792-9d6c-23fbfa7c5574',
        'secret': '935090D57C91A47CF2592F2964ED439A',
        'password': "E5Ro&Djq",
        'proxies': proxies  # 需要socks5
    }),
    "coinbase": ccxt.coinbase({
        'apiKey': 'tMCfzC7vXMV7CR5v',
        'secret': 'TjF8zHnCd3AnxvXxExlwvxxZxgdF5o1Q',
        'proxies': proxies
    }),
}


# http://127.0.0.1:5000/market/markets?exchange=binance
@market_blueprint.route('/markets')
@buffer.cached(timeout=10, query_string=True)
def markets():
    args = utility.get_args(request)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_markets()}


# http://127.0.0.1:5000/market/status?exchange=binance
@market_blueprint.route('/status')
@buffer.cached(timeout=10, query_string=True)
def status():
    args = utility.get_args(request)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_status()}


# http://127.0.0.1:5000/market/currencies?exchange=binance
@market_blueprint.route('/currencies')
@buffer.cached(timeout=10, query_string=True)
def currencies():
    args = utility.get_args(request)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_currencies()}


# http://127.0.0.1:5000/market/time?exchange=binance
@market_blueprint.route('/time')
@buffer.cached(timeout=10, query_string=True)
def time():
    args = utility.get_args(request)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_time()}


# http://127.0.0.1:5000/market/rate?code=USDT&exchange=binance
@market_blueprint.route('/rate')
@buffer.cached(timeout=10, query_string=True)
def rate():
    args = utility.get_args(request)
    code = args.get("code", "USDT").upper()
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_borrow_rate(code)}


# http://127.0.0.1:5000/market/orders?symbol=ETH/BTC&exchange=binance
@market_blueprint.route('/orders')
@buffer.cached(timeout=10, query_string=True)
def orders():
    args = utility.get_args(request)
    symbol = args.get("symbol", "BTC/USDT").upper()
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_order_book(symbol=symbol)}


# http://127.0.0.1:5000/market/tickers?symbols=BTC/USD&exchange=ftx
# http://127.0.0.1:5000/market/ticker?symbol=BTC/USDT&exchange=binance
# https://docs.ccxt.com/en/latest/manual.html#ticker-structure
'''
{
  "code": 0, 
  "data": {
    "ask": 23727.88, 
    "askVolume": 0.00211, 
    "average": 23784.47, 
    "baseVolume": 151451.28561,     24h成交量(BTC)
    "bid": 23727.45, 
    "bidVolume": 0.02682, 
    "change": -115.74, 
    "close": 23726.6, 
    "datetime": "2022-07-31T01:18:43.462Z", 
    "high": 24668.0,    24h最高价
    "info": {
      "askPrice": "23727.88000000", 
      "askQty": "0.00211000", 
      "bidPrice": "23727.45000000", 
      "bidQty": "0.02682000", 
      "closeTime": "1659230323462", 
      "count": "4784289", 
      "firstId": "1544497321", 
      "highPrice": "24668.00000000", 
      "lastId": "1549281609", 
      "lastPrice": "23726.60000000", 
      "lastQty": "0.00200000", 
      "lowPrice": "23502.25000000", 
      "openPrice": "23842.34000000", 
      "openTime": "1659143923462", 
      "prevClosePrice": "23841.79000000", 
      "priceChange": "-115.74000000", 
      "priceChangePercent": "-0.485", 
      "quoteVolume": "3642695545.76329560", 
      "symbol": "BTCUSDT", 
      "volume": "151451.28561000", 
      "weightedAvgPrice": "24051.92885020"
    }, 
    "last": 23726.6, 
    "low": 23502.25,    24h最低价
    "open": 23842.34, 
    "percentage": -0.485, 
    "previousClose": 23841.79, 
    "quoteVolume": 3642695545.7632957,  24h成交额(USDT)
    "symbol": "BTC/USDT", 
    "timestamp": 1659230323462, 
    "vwap": 24051.9288502
  }
}
'''


@market_blueprint.route('/ticker')
@buffer.cached(timeout=10, query_string=True)
def ticker():
    args = utility.get_args(request)
    symbol = args.get("symbol", "BTC/USDT").upper()
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    # if not exchange.has['fetchTicker']:
    #     raise Exception("No fetchTicker")
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_ticker(symbol=symbol)}


# http://127.0.0.1:5000/market/tickers?symbols=SOL/USD,FTT/USD&exchange=ftx
# http://127.0.0.1:5000/market/tickers?symbols=BTC/USDT,ETH/USDT,ETC/USDT,BNB/USDT,UNFI/USDT,FORTH/USDT,ADA/USDT,WING/USDT,MATIC/USDT,AVAX/USDT,FIL/USDT,DOT/USDT,LINK/USDT,XRP/USDT,APE/USDT,GALA/USDT,WTC/USDT,ICP/USDT,GMT/USDT,NEAR/USDT,DOGE/USDT,ROSE/USDT,SHIB/USDT,BTCST/USDT,FTM/USDT,ATOM/USDT,RUNE/USDT,AXS/USDT&exchange=binance
@market_blueprint.route('/tickers')
@buffer.cached(timeout=10, query_string=True)
def tickers():
    args = utility.get_args(request)
    symbols = args.get("symbols", "BTC/USDT,ETH/USDT").upper().split(',')
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_tickers(symbols=symbols)}


# http://127.0.0.1:5000/market/trades?symbol=BTC/USDT&exchange=binance
# http://127.0.0.1:5000/market/trades?symbol=BTC/USDT&since=1659196800000&limit=100&exchange=binance
@market_blueprint.route('/trades')
@buffer.cached(timeout=10, query_string=True)
def trades():
    args = utility.get_args(request)
    symbol = args.get("symbol", "BTC/USDT").upper()
    since = args.get("since", None)
    limit = args.get("limit", None)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    if since != None:
        since = int(since)
    if limit != None:
        limit = int(limit)
    return {"code": 0, "msg": "执行成功。", "data": exchange.fetch_trades(symbol=symbol, since=since, limit=limit)}


# http://127.0.0.1:5000/market/ohlcv?symbol=BTC/USDT&time_frame=1d&since=1656604800000&limit=10&exchange=binance
@market_blueprint.route('/ohlcv')
@buffer.cached(timeout=10, query_string=True)
def ohlcv():
    args = utility.get_args(request)
    symbol = args.get("symbol", "BTC/USDT").upper()
    time_frame = args.get("time_frame", "1m")
    since = args.get("since", None)
    limit = args.get("limit", None)
    exchange = args.get("exchange", "binance")

    exchange = exchanges[exchange]
    if since != None:
        since = int(since)
    if limit != None:
        limit = int(limit)
    ohlcv = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_frame, since=since, limit=limit)
    df_ohlcv = pandas.DataFrame(ohlcv, columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    # df_ohlcv["DateTime"] = df_ohlcv['DateTime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000).strftime('%Y-%m-%d %H:%M:%S'))
    return {"code": 0, "msg": "执行成功。", "data": df_ohlcv.to_dict(orient="records")}
