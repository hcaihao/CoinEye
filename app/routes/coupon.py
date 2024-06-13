from flask import blueprints
from flask import request
from flask import current_app
# from flask_login import current_user, login_user, logout_user, login_required
# from flask_principal import identity_changed, Identity, AnonymousIdentity

from app import utility
from app import buffer
from app.models.models import *
# from app import admin_permission, user_permission, admin_user_permission
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from app.routes import user_required, admin_required

from datetime import timedelta, datetime
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey

coupon_blueprint = blueprints.Blueprint("coupon", __name__, url_prefix='/coupon')


# http://127.0.0.1:5000/coupon/generate?amount=1&days=7&remark=test
@coupon_blueprint.route('/generate')
# @admin_permission.require(http_exception=500)  # 放到route下面
@admin_required()
def generate():
    args = utility.get_args(request)
    amount = args.get('amount', "")
    days = args.get('days', "")
    remark = args.get('remark', "")

    for i in range(int(amount)):
        coupon = Coupon()
        coupon.admin_id = get_jwt_identity()
        coupon.code = utility.get_uuid().replace("-", "")
        coupon.days = days
        coupon.user_name = ""
        coupon.remark = remark
        coupon.is_enable = True
        coupon.update_time = func.now()
        coupon.create_time = func.now()
        db.session.add(coupon)

    # # 操作记录
    # operate_log = OperateLog()
    # operate_log.admin_id = current_user.id
    # operate_log.operate = "生成邀请码"
    # operate_log.remark = "数量：{}".format(amount)
    # operate_log.create_time = func.now()
    # db.session.add(operate_log)
    # db.session.commit()

    return {"code": 0, "msg": "生成成功。"}


# http://127.0.0.1:5000/coupon/query
@coupon_blueprint.route('/query')
# @admin_permission.require(http_exception=500)  # 放到route下面
@admin_required()
def query():
    args = utility.get_args(request)

    coupons = db.session.query(Coupon).all()

    data = []
    for coupon in coupons:
        item = {c.name: getattr(coupon, c.name) for c in coupon.__table__.columns}
        data.append(item)

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/coupon/update?id=1&is_enable=1&remark=test
@coupon_blueprint.route('/update')
# @admin_permission.require(http_exception=500)  # 放到route下面
@admin_required()
def update():
    args = utility.get_args(request)
    id = args.get('id', "")
    remark = args.get('remark', "")
    is_enable = args.get('is_enable', "") == "1"

    coupon = Coupon.query.filter(Coupon.id == id).first()
    if coupon == None:
        return {"code": 1, "msg": "邀请码不存在。"}

    coupon.remark = remark
    coupon.is_enable = is_enable

    return {"code": 0, "msg": "修改成功。"}
