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

admin_blueprint = blueprints.Blueprint("admin", __name__, url_prefix='/admin')


# http://127.0.0.1:5000/admin/login?user_name=test&password=test
@admin_blueprint.route('/login')
def login():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")

    admin = Admin.query.filter(Admin.user_name == user_name, Admin.password == utility.get_md5(password)).first()
    if admin is None:
        return {"code": 1, "msg": "用户名或密码错误。"}
    elif not admin.is_enable:
        return {"code": 1, "msg": "账号已停用。"}
    else:
        # Keep the user info in the session using Flask-Login
        # login_user(admin)
        # Tell Flask-Principal the identity changed
        # identity_changed.send(current_app._get_current_object(), identity=Identity(admin.id))

        # JWT方式
        access_token = create_access_token(identity=admin.id, additional_claims={"is_admin": True}, fresh=True)
        refresh_token = create_refresh_token(identity=admin.id, additional_claims={"is_admin": True})
        return {"code": 0, "msg": "登录成功。", "data": {"access_token": access_token, "refresh_token": refresh_token}}


# http://127.0.0.1:5000/admin/logout
@admin_blueprint.route('/logout')
def logout():
    # Remove the user information from the session
    # logout_user()
    # Tell Flask-Principal the user is anonymous
    # identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    return {"code": 0, "msg": "登出成功。"}


# http://127.0.0.1:5000/admin/modify_password?user_name=17721226853&password=test&new_password=test2
@admin_blueprint.route('/modify_password')
def modify_password():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    new_password = args.get('new_password', "")

    admin = Admin.query.filter(Admin.user_name == user_name).first()
    if admin is None:
        return {"code": 1, "msg": "管理员不存在。"}

    if admin.password != utility.get_md5(password):
        return {"code": 1, "msg": "密码不正确。"}

    if not admin.is_enable:
        return {"code": 1, "msg": "账号已停用。"}

    admin.password = utility.get_md5(new_password)
    db.session.commit()

    return {"code": 0, "msg": "修改成功。"}


# http://127.0.0.1:5000/admin/get_info
@admin_blueprint.route('/get_info')
# @admin_permission.require(http_exception=500)  # 放到route下面
@admin_required()
def get_info():
    current_user = Admin.query.filter(Admin.id == get_jwt_identity()).first()
    data = {c.name: getattr(current_user, c.name) for c in current_user.__table__.columns}
    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/admin/query_user
@admin_blueprint.route('/query_user')
# @admin_permission.require(http_exception=500)  # 放到route下面
@admin_required()
def query_user():
    args = utility.get_args(request)

    users = db.session.query(User).all()

    data = []
    for user in users:
        item = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        data.append(item)

    return {"code": 0, "msg": "执行成功。", "data": data}


# http://127.0.0.1:5000/admin/refresh_token
@admin_blueprint.route('/refresh_token')  # 携带refresh_token请求此接口，刷新access_token
@admin_required(refresh=True)  # 只允许refresh_token访问
def refresh_token():
    access_token = create_access_token(identity=get_jwt_identity(), additional_claims={"is_admin": True}, fresh=False)
    return {"code": 0, "msg": "刷新成功。", "data": {"access_token": access_token}}
