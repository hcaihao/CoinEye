import random
import re

from flask import blueprints
from flask import request

import os
import pandas
import ccxt
import datetime
import time
import configparser

from app import utility
from app import buffer
from app import cache

# 读取配置文件
cf = configparser.ConfigParser()
cf.read("config.ini", encoding="utf-8-sig")  # 带有签名的utf-8
exchanges = utility.get_dict(cf.get("setting", "exchanges").lower())
hot_symbols = utility.get_dict(cf.get("setting", "hot_symbols").lower())
reminder_list_key = cf.get("setting", "reminder_list_key")

interface_blueprint = blueprints.Blueprint("interface", __name__, url_prefix='/interface')


# http://127.0.0.1:5000/interface/market?scope=20220929&show=hot
@interface_blueprint.route('/market')
@buffer.cached(timeout=1, query_string=True)
def market():
    args = utility.get_args(request)
    show = args.get("show", "").lower()
    scope = args.get("scope", utility.get_current_time(format='%Y%m%d'))

    data = {}
    for exchange in exchanges:
        data[exchange] = {}
        for symbol in exchanges[exchange]:
            try:
                if show == "hot" and symbol not in hot_symbols:
                    continue

                open_price = float(cache.get(f"{exchange}:{symbol}:open_price:{scope}"))
                now_price = float(cache.get(f"{exchange}:{symbol}:now_price:{scope}"))
                amount = float(cache.get(f"{exchange}:{symbol}:amount:{scope}"))
                netflow = float(cache.get(f"{exchange}:{symbol}:netflow:{scope}"))
                rate = float(cache.get(f"{exchange}:{symbol}:rate:{scope}"))

                item = {
                    "open": open_price,
                    "now": now_price,
                    "rate": rate,
                    "amount": amount,
                    "netflow": netflow,
                }
                data[exchange][symbol] = item
            except Exception as err:
                pass

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/interface/rank?scope=20220929&show=hot&order=desc
@interface_blueprint.route('/rank')
@buffer.cached(timeout=1, query_string=True)
def rank():
    args = utility.get_args(request)
    show = args.get("show", "").lower()
    order = args.get("order", "desc")
    scope = args.get("scope", utility.get_current_time(format='%Y%m%d'))

    data = []
    for exchange in exchanges:
        for symbol in exchanges[exchange]:
            try:
                if show == "hot" and symbol not in hot_symbols:
                    continue

                open_price = float(cache.get(f"{exchange}:{symbol}:open_price:{scope}"))
                now_price = float(cache.get(f"{exchange}:{symbol}:now_price:{scope}"))
                amount = float(cache.get(f"{exchange}:{symbol}:amount:{scope}"))
                netflow = float(cache.get(f"{exchange}:{symbol}:netflow:{scope}"))
                rate = float(cache.get(f"{exchange}:{symbol}:rate:{scope}"))

                item = {
                    "exchange": exchange,
                    "symbol": symbol,
                    "open": open_price,
                    "now": now_price,
                    "rate": rate,
                    "amount": amount,
                    "netflow": netflow,
                }
                data.append(item)
            except Exception as err:
                pass

    if order == "asc":
        data.sort(key=lambda k: (k.get('rate', 0)))
    elif order == "desc":
        data.sort(key=lambda k: (k.get('rate', 0)), reverse=True)

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/interface/detail?exchange=binance&symbol=BTC/USDT
@interface_blueprint.route('/detail')
@buffer.cached(timeout=1, query_string=True)
def detail():
    args = utility.get_args(request)
    exchange = args.get("exchange", "").lower()
    symbol = args.get("symbol", "").lower()
    days = int(args.get("days", "7"))
    hours = int(args.get("hours", "24"))
    minutes = int(args.get("minutes", "60"))

    # day = utility.get_current_time(format='%Y%m%d')
    # hour = utility.get_current_time(format='%Y%m%d%H')
    # minute = utility.get_current_time(format='%Y%m%d%H%M')

    # day_ts = utility.dts_2_ts(day, format='%Y%m%d')
    # hour_ts = utility.dts_2_ts(hour, format='%Y%m%d%H')
    # minute_ts = utility.dts_2_ts(minute, format='%Y%m%d%H%M')

    days = utility.get_date_list(days, delta=datetime.timedelta(days=1), format='%Y%m%d')
    hours = utility.get_date_list(hours, delta=datetime.timedelta(hours=1), format='%Y%m%d%H')
    minutes = utility.get_date_list(minutes, delta=datetime.timedelta(minutes=1), format='%Y%m%d%H%M')

    data = {}
    data[exchange] = {}
    data[exchange][symbol] = {}
    data[exchange][symbol]["trade"] = {}

    # 最近交易
    data[exchange][symbol]["trade"]["last"] = []
    trade_ids = cache.zrevrange("{}:{}:trade_ids".format(exchange, symbol), start=0, end=49, withscores=False)
    for trade_id in trade_ids:
        trade_info = cache.get("{}:{}:trade_info:{}".format(exchange, symbol, trade_id))
        data[exchange][symbol]["trade"]["last"].append(utility.get_dict(trade_info.lower()))

    # 大单交易
    data[exchange][symbol]["trade"]["big"] = []
    # trade_ids = cache.zrevrangebyscore("{}:{}:big_trade_ids".format(exchange, symbol), min=day_ts, max=utility.get_current_timestamp(), start=0, num=3, withscores=False)
    big_trade_ids = cache.zrevrange("{}:{}:big_trade_ids".format(exchange, symbol), start=0, end=19, withscores=False)
    for big_trade_id in big_trade_ids:
        big_trade_info = cache.get("{}:{}:trade_info:{}".format(exchange, symbol, big_trade_id))
        data[exchange][symbol]["trade"]["big"].append(utility.get_dict(big_trade_info.lower()))

    # 统计数据
    data[exchange][symbol]["market"] = {}

    data[exchange][symbol]["market"]["day"] = {}
    for day in days:
        try:
            open_price = float(cache.get(f"{exchange}:{symbol}:open_price:{day}"))
            now_price = float(cache.get(f"{exchange}:{symbol}:now_price:{day}"))
            amount = float(cache.get(f"{exchange}:{symbol}:amount:{day}"))
            netflow = float(cache.get(f"{exchange}:{symbol}:netflow:{day}"))
            rate = float(cache.get(f"{exchange}:{symbol}:rate:{day}"))

            item = {
                "open": open_price,
                "now": now_price,
                "rate": rate,
                "amount": amount,
                "netflow": netflow,
            }
            data[exchange][symbol]["market"]["day"][day] = item
        except Exception as err:
            pass

    data[exchange][symbol]["market"]["hour"] = {}
    for hour in hours:
        try:
            open_price = float(cache.get(f"{exchange}:{symbol}:open_price:{hour}"))
            now_price = float(cache.get(f"{exchange}:{symbol}:now_price:{hour}"))
            amount = float(cache.get(f"{exchange}:{symbol}:amount:{hour}"))
            netflow = float(cache.get(f"{exchange}:{symbol}:netflow:{hour}"))
            rate = float(cache.get(f"{exchange}:{symbol}:rate:{hour}"))

            item = {
                "open": open_price,
                "now": now_price,
                "rate": rate,
                "amount": amount,
                "netflow": netflow,
            }
            data[exchange][symbol]["market"]["hour"][hour] = item
        except Exception as err:
            pass

    data[exchange][symbol]["market"]["minute"] = {}
    for minute in minutes:
        try:
            open_price = float(cache.get(f"{exchange}:{symbol}:open_price:{minute}"))
            now_price = float(cache.get(f"{exchange}:{symbol}:now_price:{minute}"))
            amount = float(cache.get(f"{exchange}:{symbol}:amount:{minute}"))
            netflow = float(cache.get(f"{exchange}:{symbol}:netflow:{minute}"))
            rate = float(cache.get(f"{exchange}:{symbol}:rate:{minute}"))

            item = {
                "open": open_price,
                "now": now_price,
                "rate": rate,
                "amount": amount,
                "netflow": netflow,
            }
            data[exchange][symbol]["market"]["minute"][minute] = item
        except Exception as err:
            pass

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/interface/trade?exchange=binance&symbol=BTC/USDT&count=10
@interface_blueprint.route('/trade')
@buffer.cached(timeout=1, query_string=True)
def trade():
    args = utility.get_args(request)
    exchange = args.get("exchange", "").lower()
    symbol = args.get("symbol", "").lower()
    count = int(args.get("count", "50"))

    data = {}
    data[exchange] = {}
    data[exchange][symbol] = {}
    data[exchange][symbol]["trade"] = {}

    # 最近交易
    data[exchange][symbol]["trade"]["last"] = []
    trade_ids = cache.zrevrange("{}:{}:trade_ids".format(exchange, symbol), start=0, end=count - 1, withscores=False)
    for trade_id in trade_ids:
        trade_info = cache.get("{}:{}:trade_info:{}".format(exchange, symbol, trade_id))
        data[exchange][symbol]["trade"]["last"].append(utility.get_dict(trade_info.lower()))

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/interface/reminder?count=50
@interface_blueprint.route('/reminder')
@buffer.cached(timeout=1, query_string=True)
def reminder():
    args = utility.get_args(request)
    count = int(args.get("count", "50"))

    data = []
    list = cache.lrange(reminder_list_key, 0, count-1)
    for item in list:
        data.append(item)

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/interface/rate?currency=usd
@interface_blueprint.route('/rate')
@buffer.cached(timeout=1, query_string=True)
def rate():
    args = utility.get_args(request)
    currency = args.get("currency", "usd")

    # https://api.exchangerate-api.com/v4/latest/USD
    data = utility.get(f"https://v6.exchangerate-api.com/v6/8d198bb9a570f29065bad931/latest/{currency}").json()

    return {"code": 0, "msg": "执行成功。", "data": data}
