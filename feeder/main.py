import sys
import time

sys.path.append(r"../app")

from cryptofeed import FeedHandler
from cryptofeed.defines import ASK, BEQUANT, HITBTC, BID, L2_BOOK, ORDER_INFO, BALANCES, TRANSACTIONS, TICKER, CANDLES, \
    TRADES
from cryptofeed.exchanges import Binance, Coinbase, Gateio, Huobi, OKX, FTX
from cryptofeed.backends.aggregate import OHLCV
from decimal import Decimal
import datetime
import asyncio
import threading
import redis
import pymysql
import utility
import db
import configparser
from cryptofeed import symbols
from utility import frenquecy, static
from rediscluster import RedisCluster

# 设置币种分隔符
symbols.Symbol.symbol_sep = "/"

cf = configparser.ConfigParser()
cf.read(["config.ini", "../config.ini"], encoding="utf-8-sig")  # 带有签名的utf-8
reminder_channel_key = cf.get("setting", "reminder_channel_key")
reminder_list_key = cf.get("setting", "reminder_list_key")
big_amount = cf.getint("setting", "big_amount")
redis_expire_seconds = cf.getint("setting", "redis_expire_seconds")
redis_reminder_seconds = cf.getint("setting", "redis_reminder_seconds")
redis_zset_length = cf.getint("setting", "redis_zset_length")
redis_list_length = cf.getint("setting", "redis_list_length")
reminder_amount = cf.getint("setting", "reminder_amount")
reminder_netflow = cf.getint("setting", "reminder_netflow")
reminder_rate = cf.getfloat("setting", "reminder_rate")
exchanges = utility.get_dict(cf.get("setting", "exchanges").upper())
hot_symbols = utility.get_dict(cf.get("setting", "hot_symbols").upper())

# redis cluster 集群最少三主三从
# startup_nodes = [
#     {"host": "127.0.0.1", "port": 7001},
#     {"host": "127.0.0.1", "port": 7002},
#
#     {"host": "127.0.0.1", "port": 7003},
#     {"host": "127.0.0.1", "port": 7004},
#
#     {"host": "127.0.0.1", "port": 7005},
#     {"host": "127.0.0.1", "port": 7006}
# ]
# cache = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

cache = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


# https://www.cnblogs.com/sunshine-long/p/12706868.html
# print(cache.mget(["binance:btc-usdt:20220811:netflow", "coinbase:btc-usdt:20220811:netflow"]))
# print(cache.keys("*20220812:*"))
# print(cache.expire(netflow_key, 60*60*24*7))
# print(cache.expireat(netflow_key, 1660142207))
# print(cache.pexpireat(netflow_key, 1660142287000))
# print(cache.exists('foo'))
# print(cache.ttl(netflow_key))
# print(cache.persist(netflow_key))
# print(cache.pttl(netflow_key))
# print(cache.setex(netflow_key, 100, "val"))


def print_symbols(refresh):
    exchanges = {}
    symbols = Binance.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["BINANCE"] = symbols
    symbols = Coinbase.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["COINBASE"] = symbols
    symbols = Huobi.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["HUOBI"] = symbols
    symbols = Gateio.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["GATEIO"] = symbols
    symbols = FTX.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["FTX"] = symbols
    symbols = OKX.symbols(refresh=refresh)
    symbols = [symbol for symbol in symbols if symbol.endswith(("/USDT", "/BUSD", "/USD"))]
    exchanges["OKX"] = symbols
    utility.write_log(utility.get_json(exchanges))


def record_trade(t, scope):
    exchange_symbol = f"{t.exchange.lower()}:{t.symbol.lower()}"

    open_price_key = f"{exchange_symbol}:open_price:{scope}"
    now_price_key = f"{exchange_symbol}:now_price:{scope}"
    amount_key = f"{exchange_symbol}:amount:{scope}"
    netflow_key = f"{exchange_symbol}:netflow:{scope}"
    # inflow_key = f"{exchange_symbol}:inflow:{scope}"
    # outflow_key = f"{exchange_symbol}:outflow:{scope}"
    rate_key = f"{exchange_symbol}:rate:{scope}"
    buy_count_key = f"{exchange_symbol}:buy_count:{scope}"
    sell_count_key = f"{exchange_symbol}:sell_count:{scope}"

    if not cache.exists(open_price_key):
        cache.setex(open_price_key, redis_expire_seconds, float(t.price))  # 设置初始价格过期时间
    if not cache.exists(now_price_key):
        cache.setex(now_price_key, redis_expire_seconds, float(t.price))  # 设置最新价格过期时间
    if not cache.exists(amount_key):
        cache.setex(amount_key, redis_expire_seconds, 0)  # 设置交易额过期时间
    if not cache.exists(netflow_key):
        cache.setex(netflow_key, redis_expire_seconds, 0)  # 设置净流入过期时间
    # if not cache.exists(inflow_key):
    #     cache.setex(inflow_key, redis_expire_seconds, 0)  # 设置流入过期时间
    # if not cache.exists(outflow_key):
    #     cache.setex(outflow_key, redis_expire_seconds, 0)  # 设置流出过期时间
    if not cache.exists(rate_key):
        cache.setex(rate_key, redis_expire_seconds, 0)  # 设置涨幅时间
    if not cache.exists(buy_count_key):
        cache.setex(buy_count_key, redis_expire_seconds, 0)  # 设置买单数量时间
    if not cache.exists(sell_count_key):
        cache.setex(sell_count_key, redis_expire_seconds, 0)  # 设置卖单数量时间

    cache.set(now_price_key, float(t.price))  # 更新最新价格

    open_price = float(cache.get(open_price_key))
    now_price = float(cache.get(now_price_key))
    cache.set(rate_key, (now_price / open_price - 1) * 100)  # 更新涨幅

    cost = float(t.amount * t.price)
    cache.incrbyfloat(amount_key, cost)  # 更新交易金额

    # 更新净流入金额
    if t.side == "buy":
        cache.incrbyfloat(netflow_key, cost)
        # cache.incrbyfloat(inflow_key, cost)
        cache.incr(buy_count_key)
    elif t.side == "sell":
        cache.incrbyfloat(netflow_key, -cost)
        # cache.incrbyfloat(outflow_key, cost)
        cache.incr(sell_count_key)


@static(last_reminder={})
def check_reminder(t):
    exchange_symbol = f"{t.exchange.lower()}:{t.symbol.lower()}"

    # 检查提醒时间
    if exchange_symbol in check_reminder.last_reminder:
        if utility.get_current_timestamp() - check_reminder.last_reminder[exchange_symbol] < redis_reminder_seconds:
            return
    check_reminder.last_reminder[exchange_symbol] = utility.get_current_timestamp()

    # 当前交易的时间
    now = utility.ts_2_dt(int(t.timestamp))

    day = datetime.datetime.strftime(now, '%Y%m%d')
    day_open_price_key = f"{exchange_symbol}:open_price:{day}"
    day_now_price_key = f"{exchange_symbol}:now_price:{day}"
    day_buy_count_key = f"{exchange_symbol}:buy_count:{day}"
    day_sell_count_key = f"{exchange_symbol}:sell_count:{day}"

    minute = datetime.datetime.strftime(now, '%Y%m%d%H%M')
    minute_open_price_key = f"{exchange_symbol}:open_price:{minute}"
    minute_now_price_key = f"{exchange_symbol}:now_price:{minute}"

    minute3_amount = 0
    minute3_netflow = 0
    # minute3_inflow = 0
    # minute3_outflow = 0
    minute3_buy_count = 0
    minute3_sell_count = 0
    minute3_list = utility.get_date_list(3, delta=datetime.timedelta(minutes=1), format="%Y%m%d%H%M", now=now)
    for minute3 in minute3_list:
        minute3_amount_key = f"{exchange_symbol}:amount:{minute3}"
        minute3_netflow_key = f"{exchange_symbol}:netflow:{minute3}"
        # minute3_inflow_key = f"{exchange_symbol}:inflow:{minute3}"
        # minute3_outflow_key = f"{exchange_symbol}:outflow:{minute3}"
        minute3_buy_count_key = f"{exchange_symbol}:buy_count:{minute3}"
        minute3_sell_count_key = f"{exchange_symbol}:sell_count:{minute3}"

        minute3_amount = minute3_amount + float(cache.get(minute3_amount_key) or 0)
        minute3_netflow = minute3_netflow + float(cache.get(minute3_netflow_key) or 0)
        # minute3_inflow = minute3_inflow + float(cache.get(minute3_inflow_key) or 0)
        # minute3_outflow = minute3_outflow + float(cache.get(minute3_outflow_key) or 0)
        minute3_buy_count = minute3_buy_count + int(cache.get(minute3_buy_count_key) or 0)
        minute3_sell_count = minute3_sell_count + int(cache.get(minute3_sell_count_key) or 0)

    day_open_price = float(cache.get(day_open_price_key))
    day_now_price = float(cache.get(day_now_price_key))
    day_rate = (day_now_price / day_open_price - 1) * 100

    day_buy_count = int(cache.get(day_buy_count_key))
    day_sell_count = int(cache.get(day_sell_count_key))

    minute_open_price = float(cache.get(minute_open_price_key))
    minute_now_price = float(cache.get(minute_now_price_key))
    minute_rate = (minute_now_price / minute_open_price - 1) * 100

    events = []
    if abs(minute_rate) >= reminder_rate and minute3_amount > 20000:
        events.append("急涨急跌")
    if minute3_amount >= reminder_amount:
        events.append("交易量激增")
    if abs(minute3_netflow) >= reminder_netflow:
        events.append("净流入激增")
    if events:
        day_zero_timestamp = utility.dts_2_ts(day, format='%Y%m%d')
        minute3_zero_timestamp = utility.dts_2_ts(minute3_list[2], format='%Y%m%d%H%M')
        trade_ids_key = f"{exchange_symbol}:trade_ids"
        big_trade_ids_key = f"{exchange_symbol}:big_trade_ids"

        # 3分钟交易数
        minute3_count = cache.zcount(trade_ids_key, minute3_zero_timestamp, t.timestamp)

        # 3分钟大单数
        minute3_big_count = cache.zcount(big_trade_ids_key, minute3_zero_timestamp, t.timestamp)

        # 今日交易数
        day_count = cache.zcount(trade_ids_key, day_zero_timestamp, t.timestamp)

        # 今日大单数
        day_big_count = cache.zcount(big_trade_ids_key, day_zero_timestamp, t.timestamp)

        value = utility.get_json({"event": ",".join(events), "exchange": t.exchange.lower(), "symbol": t.symbol.lower(),
                                  "minute_rate": minute_rate, "day_rate": day_rate, "amount": minute3_amount,
                                  "netflow": minute3_netflow, "price": minute_now_price, "minute3_count": minute3_count,
                                  "minute3_big_count": minute3_big_count, "day_count": day_count,
                                  "day_big_count": day_big_count,
                                  "minute3_buy_count": minute3_buy_count, "minute3_sell_count": minute3_sell_count,
                                  "day_buy_count": day_buy_count, "day_sell_count": day_sell_count, "time": now})

        cache.publish(reminder_channel_key, value)
        cache.lpush(reminder_list_key, value)
        utility.write_log(f"{utility.get_json(value)}")

    cache.ltrim(reminder_list_key, 0, redis_list_length - 1)


async def trade_callback(t, receipt_timestamp):
    try:
        print(f"Trade received at {receipt_timestamp}: {t}")

        exchange_symbol = f"{t.exchange.lower()}:{t.symbol.lower()}"

        # 当前交易的时间
        now = utility.ts_2_dt(int(t.timestamp))

        day = datetime.datetime.strftime(now, '%Y%m%d')
        hour = datetime.datetime.strftime(now, '%Y%m%d%H')
        minute = datetime.datetime.strftime(now, '%Y%m%d%H%M')

        trade_info_key = f"{exchange_symbol}:trade_info:{t.id}"
        cache.setex(trade_info_key, redis_expire_seconds, utility.get_json(t.to_dict()))  # 记录原始数据

        trade_ids_key = f"{exchange_symbol}:trade_ids"
        if cache.zadd(trade_ids_key, {t.id: t.timestamp}) != 1:  # 记录id集合
            raise Exception(f"{t.exchange} record trade failed: {str(t.raw)}")
        # cache.zremrangebyrank(trade_ids_key, 0, -redis_zset_length - 1)
        cache.zremrangebyscore(trade_ids_key, 0, utility.get_current_timestamp() - redis_expire_seconds)

        big_trade_ids_key = f"{exchange_symbol}:big_trade_ids"
        cost = float(t.amount * t.price)
        if cost > big_amount:
            if cache.zadd(big_trade_ids_key, {t.id: t.timestamp}) != 1:  # 记录大单id集合
                raise Exception(f"{t.exchange} record big trade failed: {str(t.raw)}")
            # cache.zremrangebyrank(big_trade_ids_key, 0, -redis_zset_length - 1)
            cache.zremrangebyscore(big_trade_ids_key, 0, utility.get_current_timestamp() - redis_expire_seconds)

        # 行情记录
        record_trade(t, day)
        record_trade(t, hour)
        record_trade(t, minute)

        # 异动检查
        check_reminder(t)

        # if cost > 300000:
        #     utility.write_log(t.raw)
        #
        #     Trade = db.Trade.model(t.exchange)
        #     trade = Trade()
        #     trade.id = t.id
        #     trade.symbol = t.symbol
        #     trade.exchange = t.exchange
        #     trade.side = t.side
        #     trade.amount = t.amount
        #     trade.price = t.price
        #     trade.cost = cost
        #     trade.timestamp = t.timestamp
        #     db.session.add(trade)
        #     db.session.commit()

    except Exception as err:
        utility.write_log(err)


async def candle_callback(c, receipt_timestamp):
    print(f"Candle received at {receipt_timestamp}: {c}")


async def book_callback(book, receipt_timestamp):
    print(
        f'Book received at {receipt_timestamp} for {book.exchange} - {book.symbol}, with {len(book.book)} entries. Top of book prices: {book.book.asks.index(0)[0]} - {book.book.bids.index(0)[0]}')
    if book.delta:
        print(f"Delta from last book contains {len(book.delta[BID]) + len(book.delta[ASK])} entries.")
    if book.sequence_number:
        assert isinstance(book.sequence_number, int)


# a = utility.get_current_timestamp(13)
# for i in range(10000):
#     cache.zremrangebyrank("abc", 0, -redis_zset_length - 1)
#     # cache.zadd("abc", {i: 1000000+i})
# b = utility.get_current_timestamp(13)
# print(b-a)


# pubsub_channel = 'task:pubsub:channel'

# def test():
#     while True:
#         cache.publish(pubsub_channel, "hello")
#         time.sleep(1)
#
# thread = threading.Thread(target=test)
# thread.start()
#
# ps = cache.pubsub()
# ps.subscribe(pubsub_channel)
#
# for i in ps.listen():
#     print(i)
#     if i['type'] == 'message':
#         print("Message", i['data'])


if __name__ == '__main__':
    fh = FeedHandler()

    # print_symbols(True)

    # fh.add_feed(Binance(symbols=exchanges["BINANCE"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")
    # # fh.add_feed(Coinbase(symbols=exchanges["COINBASE"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")
    # fh.add_feed(Gateio(symbols=exchanges["GATEIO"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")
    # fh.add_feed(Huobi(symbols=exchanges["HUOBI"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")
    # # fh.add_feed(FTX(symbols=exchanges["FTX"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")
    # fh.add_feed(OKX(symbols=exchanges["OKX"], channels=[CANDLES], callbacks={CANDLES: candle_callback}), candle_interval="1m")

    # fh.add_feed(Binance(symbols=exchanges["BINANCE"], channels=[TRADES], callbacks={TRADES: trade_callback}))
    # fh.add_feed(Coinbase(symbols=exchanges["COINBASE"], channels=[TRADES], callbacks={TRADES: trade_callback}))
    # fh.add_feed(Gateio(symbols=exchanges["GATEIO"], channels=[TRADES], callbacks={TRADES: trade_callback}))
    # fh.add_feed(Huobi(symbols=exchanges["HUOBI"], channels=[TRADES], callbacks={TRADES: trade_callback}))
    # fh.add_feed(FTX(symbols=exchanges["FTX"], channels=[TRADES], callbacks={TRADES: trade_callback}))
    # fh.add_feed(OKX(symbols=exchanges["OKX"], channels=[TRADES], callbacks={TRADES: trade_callback}))

    fh.add_feed(Binance(
        symbols=[symbol for symbol in Binance.symbols(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))
    fh.add_feed(Gateio(
        symbols=[symbol for symbol in Gateio.symbols(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))
    fh.add_feed(Huobi(
        symbols=[symbol for symbol in Huobi.symbols(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))
    fh.add_feed(Coinbase(
        symbols=[symbol for symbol in Coinbase.symbols(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))
    fh.add_feed(FTX(
        symbols=[symbol for symbol in FTX.symbols(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))
    fh.add_feed(OKX(
        symbols=[symbol for symbol in Gateio.OKX(refresh=True) if symbol.endswith(("/USDT", "/BUSD", "/USD"))],
        channels=[TRADES], callbacks={TRADES: trade_callback}))

    fh.run()
