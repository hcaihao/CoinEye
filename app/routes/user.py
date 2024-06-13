from flask import blueprints
from flask import request
from flask import current_app
# from flask_login import current_user, login_user, logout_user, login_required
# from flask_principal import identity_changed, Identity, AnonymousIdentity
from werkzeug.exceptions import HTTPException

from app import utility
from app import buffer
from app import hashids
from app.models.models import *
# from app import admin_permission, user_permission, admin_user_permission
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from app.routes import user_required, admin_required

from lxml import etree
import random
import requests
from datetime import timedelta, datetime
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from app import cache

user_blueprint = blueprints.Blueprint("user", __name__, url_prefix='/user')


# http://127.0.0.1:5000/user/send_sms?phone=17721226853
@user_blueprint.route('/send_sms')
@buffer.cached(timeout=60, query_string=True)
def send_sms():
    args = utility.get_args(request)
    phone = args.get('phone', "")
    sms_code = utility.get_rand_number(6)

    url = f"http://api.yiweixx.com/sms.aspx?account=taoge&password=147258&mobile={phone}&content=【币眼】您的验证码是{sms_code}&userid=754&action=send"
    res = requests.get(url)
    html = etree.HTML(res.text.encode(
        'utf-8'))  # '<?xml version="1.0" encoding="gb2312" ?><returnsms>\n <returnstatus>Success</returnstatus>\n <message>ok</message>\n <remainpoint>0</remainpoint>\n <taskID>1381020</taskID>\n <successCounts>1</successCounts></returnsms>'
    ret = html.xpath("//returnstatus")[0].text

    cache.setex(f"sms_code:{phone}", 300, sms_code)

    return {"code": 0, "msg": "执行成功。", "data": ret}


# http://127.0.0.1:5000/user/verify_sms?phone=17721226853&sms_code=123456
@user_blueprint.route('/verify_sms')
def verify_sms():
    args = utility.get_args(request)
    phone = args.get('phone', "")
    sms_code = args.get('sms_code', "")

    if cache.get(f"sms_code:{phone}") != sms_code:
        return {"code": 1, "msg": "验证码错误。"}

    return {"code": 0, "msg": "验证码正确。"}


# http://127.0.0.1:5000/user/register?user_name=17721226853&password=test&sms_code=123456&invite_code=285865
# http://127.0.0.1:5000/user/register?user_name=17721226853&password=test&sms_code=123456&&coupon_code=4b3469ca1fe54f93ac6bb06e4445ec45
@user_blueprint.route('/register')
def register():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    coupon_code = args.get('coupon_code', "")
    invite_code = args.get('invite_code', "")
    sms_code = args.get('sms_code', "")

    if cache.get(f"sms_code:{user_name}") != sms_code:
        return {"code": 1, "msg": "验证码错误。"}

    user = User.query.filter(User.user_name == user_name).first()
    if user != None:
        return {"code": 1, "msg": "用户已存在。"}

    if coupon_code == "" and invite_code == "":
        return {"code": 1, "msg": "仅接受邀请注册。"}

    if coupon_code != "":
        coupon = Coupon.query.filter(Coupon.code == coupon_code).first()
        if coupon == None:
            return {"code": 1, "msg": "邀请码不存在。"}

        if coupon.is_enable == False:
            return {"code": 1, "msg": "邀请码已失效。"}

        if coupon.user_name != "":
            return {"code": 1, "msg": "邀请码已使用。"}

        coupon.user_name = user_name

        user = User()
        user.user_name = user_name
        user.password = utility.get_md5(password)
        user.wechat = ""
        user.email = ""
        user.balance = 0
        user.remark = ""
        user.is_enable = True
        user.superior1 = ""
        user.superior2 = ""
        user.terminate_date = datetime.now() + timedelta(days=coupon.days)
        user.update_time = datetime.now()
        user.create_time = datetime.now()
        db.session.add(user)
        db.session.commit()

        return {"code": 0, "msg": "注册成功。"}

    if invite_code != "":
        invite = User.query.filter(User.id == hashids.decode(invite_code)).first()
        if invite == None:
            return {"code": 1, "msg": "邀请用户不存在。"}

        if invite.is_enable == False:
            return {"code": 1, "msg": "邀请用户已失效。"}

        user = User()
        user.user_name = user_name
        user.password = utility.get_md5(password)
        user.wechat = ""
        user.email = ""
        user.balance = 0
        user.remark = ""
        user.is_enable = True
        user.superior1 = invite.user_name
        user.superior2 = invite.superior1
        user.terminate_date = datetime.now()
        user.update_time = datetime.now()
        user.create_time = datetime.now()
        db.session.add(user)
        db.session.commit()

        return {"code": 0, "msg": "注册成功。"}

    # # 操作记录
    # operate_log = OperateLog()
    # operate_log.admin_id = user.id
    # operate_log.operate = "用户注册"
    # operate_log.remark = "用户名称：{}".format(user_name)
    # operate_log.create_time = datetime.now()
    # db.session.add(operate_log)
    # db.session.commit()


# http://127.0.0.1:5000/user/login?user_name=17721226853&password=test
@user_blueprint.route('/login')
def login():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")

    user = User.query.filter(User.user_name == user_name, User.password == utility.get_md5(password)).first()
    if user is None:
        return {"code": 1, "msg": "用户名或密码错误。"}
    elif not user.is_enable:
        return {"code": 1, "msg": "账号已停用。"}
    else:
        # Keep the user info in the session using Flask-Login
        # login_user(user)
        # Tell Flask-Principal the identity changed
        # identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

        # JWT方式
        access_token = create_access_token(identity=user.id, additional_claims={"is_admin": False}, fresh=True)
        refresh_token = create_refresh_token(identity=user.id, additional_claims={"is_admin": False})
        return {"code": 0, "msg": "登录成功。", "data": {"access_token": access_token, "refresh_token": refresh_token}}


# http://127.0.0.1:5000/user/logout
@user_blueprint.route('/logout')
def logout():
    # Remove the user information from the session
    # logout_user()
    # Tell Flask-Principal the user is anonymous
    # identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return {"code": 0, "msg": "登出成功。"}


# http://127.0.0.1:5000/user/modify_password?user_name=17721226853&password=test&new_password=test2
@user_blueprint.route('/modify_password')
def modify_password():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    new_password = args.get('new_password', "")

    user = User.query.filter(User.user_name == user_name).first()
    if user is None:
        return {"code": 1, "msg": "用户不存在。"}

    if user.password != utility.get_md5(password):
        return {"code": 1, "msg": "密码不正确。"}

    if not user.is_enable:
        return {"code": 1, "msg": "账号已停用。"}

    user.password = utility.get_md5(new_password)
    db.session.commit()

    return {"code": 0, "msg": "修改成功。"}


# http://127.0.0.1:5000/user/reset_password?user_name=17721226853&sms_code=123456&new_password=test2
@user_blueprint.route('/reset_password')
def reset_password():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    sms_code = args.get('sms_code', "")
    new_password = args.get('new_password', "")

    if cache.get(f"sms_code:{user_name}") != sms_code:
        return {"code": 1, "msg": "验证码错误。"}

    user = User.query.filter(User.user_name == user_name).first()
    if user is None:
        return {"code": 1, "msg": "用户不存在。"}

    if not user.is_enable:
        return {"code": 1, "msg": "账号已停用。"}

    user.password = utility.get_md5(new_password)
    db.session.commit()

    return {"code": 0, "msg": "修改成功。"}


# http://127.0.0.1:5000/user/get_info
@user_blueprint.route('/get_info')
# @user_permission.require(http_exception=500)  # 放到route下面
@user_required()
def get_info():
    current_user = User.query.filter(User.id == get_jwt_identity()).first()

    inferior1_count = db.session.query(func.count(User.id)).filter(User.superior1 == current_user.user_name).scalar()
    inferior2_count = db.session.query(func.count(User.id)).filter(User.superior2 == current_user.user_name).scalar()

    data = {c.name: getattr(current_user, c.name) for c in current_user.__table__.columns}
    data["invite_code"] = hashids.encode(current_user.id)
    data["inferior1_count"] = inferior1_count
    data["inferior2_count"] = inferior2_count

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/user/set_info
@user_blueprint.route('/set_info')
# @user_permission.require(http_exception=500)  # 放到route下面
@user_required()
def set_info():
    args = utility.get_args(request)
    wechat = args.get("wechat", "")
    email = args.get("email", "")

    current_user = User.query.filter(User.id == get_jwt_identity()).first()

    current_user.wechat = wechat
    current_user.email = email

    return {"code": 0, "msg": "修改成功。"}


# http://127.0.0.1:5000/user/refresh_token
# Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNjYzNzI0ODMxLCJqdGkiOiIzNzE0Y2RhZC1kZDliLTQ1MTMtODA5MC1hZDQzYzc3OThiMzQiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjo0LCJuYmYiOjE2NjM3MjQ4MzEsImV4cCI6MTY2MzcyODQzMSwiaXNfYWRtaW4iOmZhbHNlfQ.QCZks1T637wFHWhgGJHGYh_KE_jCszTdYySwn5E3JPk
@user_blueprint.route('/refresh_token')  # 携带refresh_token请求此接口，刷新access_token
@user_required(refresh=True)  # 只允许refresh_token访问
def refresh_token():
    access_token = create_access_token(identity=get_jwt_identity(), additional_claims={"is_admin": False}, fresh=False)
    return {"code": 0, "msg": "刷新成功。", "data": {"access_token": access_token}}


# http://127.0.0.1:5000/user/get_reminder
@user_blueprint.route('/get_reminder')
# @user_permission.require(http_exception=500)  # 放到route下面
@user_required()
def get_reminder():
    current_user = User.query.filter(User.id == get_jwt_identity()).first()

    data = []
    for reminder in current_user.reminders:
        item = {c.name: getattr(reminder, c.name) for c in reminder.__table__.columns}
        data.append(item)

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/user/set_reminder?exchange=binance&symbol=btc/usdt&is_sms=1&is_subs=0&is_wechat=1
@user_blueprint.route('/set_reminder')
# @user_permission.require(http_exception=500)  # 放到route下面
@user_required()
def set_reminder():
    args = utility.get_args(request)
    exchange = args.get("exchange", "").lower()
    symbol = args.get("symbol", "").lower()
    is_sms = args.get("is_sms", "") == "1"
    is_subs = args.get("is_subs", "") == "1"
    is_wechat = args.get("is_wechat", "") == "1"

    current_user = User.query.filter(User.id == get_jwt_identity()).first()

    reminder = Reminder.query.filter(Reminder.user_id == current_user.id, Reminder.exchange == exchange, Reminder.symbol == symbol).first()
    if reminder == None:
        reminder = Reminder()
        reminder.user_id = current_user.id
        reminder.exchange = exchange
        reminder.symbol = symbol
        reminder.is_sms = is_sms
        reminder.is_subs = is_subs
        reminder.is_wechat = is_wechat
        reminder.update_time = func.now()
        reminder.create_time = func.now()
        db.session.add(reminder)
        db.session.commit()
    else:
        reminder.is_sms = is_sms
        reminder.is_subs = is_subs
        reminder.is_wechat = is_wechat
        reminder.update_time = func.now()
        db.session.commit()

    return {"code": 0, "msg": "设置成功。"}


# http://127.0.0.1:5000/user/get_inferior
@user_blueprint.route('/get_inferior')
# @user_permission.require(http_exception=500)  # 放到route下面
@user_required()
def get_inferior():
    current_user = User.query.filter(User.id == get_jwt_identity()).first()

    users = User.query.filter(or_(User.superior1 == current_user.user_name, User.superior2 == current_user.user_name)).all()

    data = []
    for user in users:
        item = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        data.append(item)

    return {"code": 0, "msg": "执行成功。", "data": data}
