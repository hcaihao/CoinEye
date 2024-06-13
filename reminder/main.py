import sys

sys.path.append(r"../app")

import binascii
import random
from ctypes import *
from ctypes import wintypes
import time
import datetime
import json
import redis
import enum
import threading
import re
import utility
import asyncio
import configparser

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger

from state import wework, Model, models

cf = configparser.ConfigParser()
cf.read(["config.ini", "../config.ini"], encoding="utf-8-sig")  # 带有签名的utf-8
interval = cf.getint("setting", "interval", fallback=1)
conversation_ids = utility.str_split(cf.get("setting", "conversation_ids", fallback=""))
reminder_channel_key = cf.get("setting", "reminder_channel_key")
reminder_list_key = cf.get("setting", "reminder_list_key")

cache = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

ps = cache.pubsub()
ps.subscribe(reminder_channel_key)

for i in ps.listen():
    if i['type'] == 'message':
        data = utility.get_dict(i['data'])
        # if data["event"] == "急涨急跌":
        #     content = f'事件：{data["event"]}\n交易所：{data["exchange"]}\n币种：{data["symbol"]}\n1分钟涨幅：{data["minute_rate"]:.2f}%\n今日涨幅：{data["day_rate"]:.2f}%\n现价：${data["price"]}\n时间：{data["time"]}'
        # elif data["event"] == "交易量激增":
        #     content = f'事件：{data["event"]}\n交易所：{data["exchange"]}\n币种：{data["symbol"]}\n3分钟交易额：${data["amount"]:.2f}\n今日涨幅：{data["day_rate"]:.2f}%\n现价：${data["price"]}\n时间：{data["time"]}'
        # elif data["event"] == "净流入激增":
        #     content = f'事件：{data["event"]}\n交易所：{data["exchange"]}\n币种：{data["symbol"]}\n3分钟净流入：${data["netflow"]:.2f}\n今日涨幅：{data["day_rate"]:.2f}%\n现价：${data["price"]}\n时间：{data["time"]}'

        content = []
        if "event" in data:
            content.append(f'{data["event"]}')
        if "exchange" in data:
            content.append(f'交易所：{data["exchange"]}')
        if "symbol" in data:
            content.append(f'币种：{data["symbol"]}')
        if "price" in data:
            content.append(f'现价：${data["price"]}')
        if "day_rate" in data:
            content.append(f'今日涨幅：{data["day_rate"]:.2f}%')
        if "minute_rate" in data:
            content.append(f'1分钟涨幅：{data["minute_rate"]:.2f}%')
        if "amount" in data:
            content.append(f'3分钟交易额：${data["amount"] / 10000:.2f}万')
        # if "inflow" in data:
        #     content.append(f'3分钟流入：${data["inflow"] / 10000:.2f}万')
        # if "outflow" in data:
        #     content.append(f'3分钟流出：${data["outflow"] / 10000:.2f}万')
        if "netflow" in data:
            content.append(f'3分钟净流入：${data["netflow"] / 10000:.2f}万')
        if "minute3_count" in data and "minute3_big_count" in data:
            content.append(f'3分钟交易/大单数：{data["minute3_count"]}/{data["minute3_big_count"]}')
        if "minute3_buy_count" in data and "minute3_sell_count" in data:
            content.append(f'3分钟买/卖单数：{data["minute3_buy_count"]}/{data["minute3_sell_count"]}')
        if "day_count" in data and "day_big_count" in data:
            content.append(f'今日交易/大单数：{data["day_count"]}/{data["day_big_count"]}')
        if "day_buy_count" in data and "day_sell_count" in data:
            content.append(f'今日买/卖单数：{data["day_buy_count"]}/{data["day_sell_count"]}')
        if "time" in data:
            content.append(f'时间：{data["time"]}')

        try:
            for conversation_id in conversation_ids:
                wework.send_text(conversation_id=conversation_id, content="\n".join(content))  # S:1688854365275155_7881299548950983
                utility.write_log("{}----{}".format(conversation_id, " ".join(content)))
        except Exception as err:
            utility.write_log(err)
