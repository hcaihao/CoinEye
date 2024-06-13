from app import utility

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
# from flask_principal import Principal, Permission, RoleNeed
from flask_caching import Cache
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request

import redis
from hashids import Hashids
from IP2Location import IP2Location

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger

import os
import datetime

# BASE_DIR = os.path.dirname(__file__) # app.root_path

app = Flask(__name__)
app.json_encoder = utility.CJsonEncoder

app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)
app.config['SECRET_KEY'] = "88888888"  # flash依赖于session，需要设置秘钥
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = ""
# app.config['SQLALCHEMY_DATABASE_URI'] = ""
app.config['SQLALCHEMY_ECHO'] = False
app.config['JWT_SECRET_KEY'] = '88888888'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=12)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(weeks=1)

# 创建数据库对象
# base.ischema_names['tinyint'] = base.BOOLEAN    #reflect后可以显示true/false
db = SQLAlchemy(app)

# 创建JWT对象
jwt = JWTManager(app)

# 创建Login对象
# https://www.jianshu.com/p/01384ee741b6
# http://blog.csdn.net/smalltankpy/article/details/53616053
# login_manager = LoginManager(app)
# login_manager.session_protection = "strong"
# login_manager.login_view = "/"  # 未登录时访问@login_required函数跳转
# login_manager.login_message = ""

# Principal
# principal = Principal(app)
# admin_permission = Permission(RoleNeed('admin'))
# user_permission = Permission(RoleNeed('user'))
# admin_user_permission = admin_permission.union(user_permission)

# IP2Location
ip2location = IP2Location()
ip2location.open(os.path.join(app.root_path, 'static/ip/IP2LOCATION-LITE-DB11.BIN'))
# ip2location.close()

# Hashids
hashids = Hashids(salt="88888888", min_length=6, alphabet="0123456789cfhistu")

# 创建Redis对象
cache = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# buffer
buffer = Cache()
buffer.init_app(app=app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/1'})

# 定时任务
scheduler = BackgroundScheduler()

# # swagger文档
# from flask_swagger_ui import get_swaggerui_blueprint
# SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
# API_URL = 'http://petstore.swagger.io/v2/swagger.json'  # Our API url (can of course be a local resource)
# # Call factory function to create our blueprint
# swaggerui_blueprint = get_swaggerui_blueprint(
#     SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
#     API_URL,
#     config={  # Swagger UI config overrides
#         'app_name': "CoinEye"
#     },
# )
# app.register_blueprint(swaggerui_blueprint)


# 注册蓝图（放最后）
from app.routes.coupon import coupon_blueprint
from app.routes.market import market_blueprint
from app.routes.admin import admin_blueprint
from app.routes.user import user_blueprint
from app.routes.interface import interface_blueprint

app.register_blueprint(coupon_blueprint)
app.register_blueprint(market_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(interface_blueprint)
