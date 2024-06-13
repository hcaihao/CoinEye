import time

import ntwork
import pydevd
import requests

from transitions import Machine
from transitions import State
from transitions.extensions.states import add_state_features, Tags, Timeout

wait_seconds = 60
models = {}

wework = ntwork.WeWork()

# https://dldir1.qq.com/wework/work_weixin/WeCom_4.0.8.6027.exe
# 打开pc企业微信, smart: 是否管理已经登录的微信
wework.open(smart=True)

# 等待登录
wework.wait_login()


# 注册消息回调
@wework.msg_register(ntwork.MT_RECV_TEXT_MSG)
def on_recv_text_msg(wework_instance: ntwork.WeWork, message):
    pydevd.settrace(suspend=False, trace_only_current_thread=True)

    self_id = wework_instance.get_login_info()["user_id"]
    self_name = wework_instance.get_login_info()["username"]

    type = message["type"]
    data = message["data"]
    sender_id = data["sender"]  # wework_instance.get_contact_detail(receiver_id)
    sender_name = data["sender_name"]
    receiver_id = data["receiver"]  # self_id
    send_time = data["send_time"]
    content = data["content"]
    content_type = data["content_type"]
    conversation_id = data["conversation_id"]

    # 判断消息不是自己发的并且不是群消息时，回复对方
    if sender_id == self_id or conversation_id.startswith("R:"):
        return

    if conversation_id != "S:1688851065080128_7881299548950983":
        return

    # wework_instance.send_text(conversation_id=conversation_id, content=f"你发送的消息是: {data['content']}")

    if sender_id not in models:
        model = Model(self_id, sender_id, conversation_id, sender_name)
        models[sender_id] = model

    try:
        models[sender_id].input(content=content, content_type=content_type)
    except Exception as err:
        print(err)


@add_state_features(Timeout)
class CustomStateMachine(Machine):
    pass


class Model:
    def __init__(self, self_id, sender_id, conversation_id, sender_name):
        self.machine = CustomStateMachine(model=self, states=states, transitions=transitions, initial='wait_message', send_event=True)  # queued=True
        self.self_id = self_id
        self.sender_id = sender_id
        self.conversation_id = conversation_id
        self.sender_name = sender_name

    def __del__(self):
        pass

    def prepare(self, event):
        content = event.kwargs.get('content')
        content_type = event.kwargs.get('content_type')
        if content_type == 2 and content == "x":
            wework.send_text(conversation_id=self.conversation_id, content="已退出系统，请重新开始。")
            self.to_wait_message()
            # self.machine.set_state("wait_message")
            raise Exception("exit")  # 不raise会继续状态

    def check_one(self, event):
        content = event.kwargs.get('content')
        content_type = event.kwargs.get('content_type')
        if content_type == 2 and content == "1":
            return True
        return False

    def check_two(self, event):
        content = event.kwargs.get('content')
        content_type = event.kwargs.get('content_type')
        if content_type == 2 and content == "2":
            return True
        return False

    def check_exchange(self, event):
        content = event.kwargs.get('content')
        content_type = event.kwargs.get('content_type')
        if content_type == 2 and not content.isdigit():
            return True

        wework.send_text(conversation_id=self.conversation_id, content="请输入有效的交易所。")
        return False

    def check_symbol(self, event):
        content = event.kwargs.get('content')
        content_type = event.kwargs.get('content_type')
        if content_type == 2 and not content.isdigit():
            return True

        wework.send_text(conversation_id=self.conversation_id, content="请输入有效的交易对。")
        return False

    def wait_input(self, event):
        # print(event.transition.source)
        wework.send_text(conversation_id=self.conversation_id, content="[拥抱]{}您好，请选择功能：\n1、按交易所查询\n2、按交易对查询\n----------------\n回复\"x\"退出系统".format(self.sender_name))
        print("wait_input")

    def wait_exchange(self, event):
        wework.send_text(conversation_id=self.conversation_id, content="请输入交易所。")
        print("wait_exchange")

    def wait_symbol(self, event):
        wework.send_text(conversation_id=self.conversation_id, content="请输入交易对。")
        print("wait_symbol")

    def query_exchange(self, event):

        wework.send_text(conversation_id=self.conversation_id, content="query_exchange。")
        self.to_wait_message()

    def query_symbol(self, event):
        wework.send_text(conversation_id=self.conversation_id, content="query_symbol。")
        self.to_wait_message()

    def timeout(self, event):
        wework.send_text(conversation_id=self.conversation_id, content="输入超时，请重新开始。")
        print("timeout")
        self.to_wait_message()


states = [
    {'name': 'wait_message'},
    {'name': 'wait_input', "on_enter": "wait_input", 'timeout': wait_seconds, 'on_timeout': 'timeout'},

    {'name': 'wait_exchange', "on_enter": "wait_exchange", 'timeout': wait_seconds, 'on_timeout': 'timeout'},
    {'name': 'query_exchange', "on_enter": "query_exchange"},

    {'name': 'wait_symbol', "on_enter": "wait_symbol", 'timeout': wait_seconds, 'on_timeout': 'timeout'},
    {'name': 'query_symbol', "on_enter": "query_symbol"},
]

# 定义状态转移
transitions = [
    {'trigger': 'input', 'source': 'wait_message', 'dest': 'wait_input'},

    {'trigger': 'input', 'source': 'wait_input', 'dest': 'wait_exchange', 'conditions': 'check_one', 'prepare': 'prepare'},  # prepare在conditions之前执行，用来随时中止
    {'trigger': 'input', 'source': 'wait_input', 'dest': 'wait_symbol', 'conditions': 'check_two', 'prepare': 'prepare'},

    {'trigger': 'input', 'source': 'wait_exchange', 'dest': 'query_exchange', 'conditions': 'check_exchange', 'prepare': 'prepare'},

    {'trigger': 'input', 'source': 'wait_symbol', 'dest': 'query_symbol', 'conditions': 'check_symbol', 'prepare': 'prepare'},

]
