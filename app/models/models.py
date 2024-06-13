from app import db
# from flask_login import UserMixin, AnonymousUserMixin

# https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html
AdminRole = db.Table('admins_roles',
                     db.Column('admin_id', db.Integer, db.ForeignKey('admins.id'), primary_key=True, nullable=False),
                     db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True, nullable=False)
                     )


# http://blog.csdn.net/abcd1f2/article/details/50934406
class Log(object):
    _mapper = {}

    @staticmethod
    def model(month):
        class_name = 'Log' + month

        ModelClass = Log._mapper.get(class_name, None)
        if ModelClass is None:
            ModelClass = type(class_name, (db.Model,), {
                '__module__': __name__,
                '__name__': class_name,
                '__tablename__': "logs_" + month,

                'id': db.Column(db.Integer, primary_key=True, nullable=False),
                'ip': db.Column(db.String(191), index=True, nullable=False),
                'country': db.Column(db.String(191), index=True, nullable=True),
                'region': db.Column(db.String(191), index=True, nullable=True),
                'city': db.Column(db.String(191), index=True, nullable=True),
                'uri': db.Column(db.String(191), index=True, nullable=False),
                'args': db.Column(db.Text, nullable=False),
                'result': db.Column(db.Text, nullable=False),
                'create_time': db.Column(db.DateTime, nullable=False)
            })
            Log._mapper[class_name] = ModelClass

        return ModelClass

    @staticmethod
    def get_months():
        result = []
        table_names = db.engine.table_names()
        for table_name in table_names:
            if table_name.startswith("logs_"):
                result.append(table_name[5:])
        return result


class OperateLog(db.Model):
    __tablename__ = 'operates_logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    operate = db.Column(db.String(191), index=True, nullable=False)
    remark = db.Column(db.String(191), index=True, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<OperateLog %r>' % self.id


class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    code = db.Column(db.String(191), unique=True, index=True, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(191), nullable=False)
    remark = db.Column(db.String(191), nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Coupon %r>' % self.id


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), unique=True, nullable=False)
    description = db.Column(db.String(191), unique=True, nullable=False)

    def __repr__(self):
        return '<Role %r>' % self.id


# http://docs.sqlalchemy.org/en/rel_1_0/orm/self_referential.html
# lazy="dynamic"只可以用在一对多和多对多关系中，不可以用在一对一和多对一中
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String(191), unique=True, nullable=False)
    password = db.Column(db.String(191), nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    coupons = db.relationship('Coupon', lazy='dynamic', backref='admin')
    operate_logs = db.relationship('OperateLog', lazy='dynamic', backref='admin')
    # roles = db.relationship('Role', secondary=AdminRole, lazy='dynamic', backref=db.backref('admins', lazy='dynamic'))
    # roles = [Role(name="admin", description="管理员")]

    def __repr__(self):
        return '<Admin %r>' % self.id

    # def get_role_names(self):
    #     result = []
    #     for role in self.roles:
    #         result.append(role.description)
    #     return ",".join(result)

    # 从UserMixin类继承，该类提供了四个方法的默认的实现，不覆盖只会返回id
    def get_id(self):
        return "admin.{}".format(self.id)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String(191), unique=True, index=True, nullable=False)
    password = db.Column(db.String(191), nullable=False)
    wechat = db.Column(db.String(191), nullable=False)
    email = db.Column(db.String(191), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False)
    remark = db.Column(db.String(191), nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    superior1 = db.Column(db.String(191), nullable=False)
    superior2 = db.Column(db.String(191), nullable=False)
    terminate_date = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    # roles = [Role(name="user", description="用户")]
    reminders = db.relationship('Reminder', lazy='dynamic', backref='user')
    orders = db.relationship('Order', lazy='dynamic', backref='user')
    messages = db.relationship('Message', lazy='dynamic', backref='user')

    def __repr__(self):
        return '<User %r>' % self.id

    # 从UserMixin类继承，该类提供了四个方法的默认的实现，不覆盖只会返回id
    def get_id(self):
        return "user.{}".format(self.id)

    # @property
    # def is_authenticated(self):
    #     return True
    #
    # @property
    # def is_active(self):
    #     return True
    #
    # @property
    # def is_anonymous(self):
    #     return False


class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange = db.Column(db.String(191), nullable=False)
    symbol = db.Column(db.String(191), nullable=False)
    is_sms = db.Column(db.Boolean, nullable=False)  # 短信
    is_subs = db.Column(db.Boolean, nullable=False)  # 公众号
    is_wechat = db.Column(db.Boolean, nullable=False)  # 微信
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'exchange', 'symbol', name='uix_1'),)

    def __repr__(self):
        return '<Reminder %r>' % self.id


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    method = db.Column(db.String(191), nullable=False)  # 支付宝/微信/银行卡
    account = db.Column(db.String(191), nullable=False)  # 支付账户
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 支付金额
    bonus = db.Column(db.Numeric(10, 2), nullable=False)  # 返利金额
    remark = db.Column(db.String(191), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Order %r>' % self.id


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    method = db.Column(db.String(191), nullable=False)  # 通知方式
    content = db.Column(db.String(191), nullable=False)  # 通知内容
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 扣费金额
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Message %r>' % self.id


# class Ohlcv(db.Model):
#     __tablename__ = 'ohlcvs'
#     date_time = db.Column(db.DateTime, nullable=False)
#     open = db.Column(db.Numeric(16, 8), nullable=False)
#     high = db.Column(db.Numeric(16, 8), nullable=False)
#     low = db.Column(db.Numeric(16, 8), nullable=False)
#     close = db.Column(db.Numeric(16, 8), nullable=False)
#     volume = db.Column(db.Numeric(16, 8), nullable=False)
#
#     def __repr__(self):
#         return '<Ohlcv %r>' % self.id

class Trade(object):
    _mapper = {}

    @staticmethod
    def model(exchange, symbol, month):
        class_name = 'Trade' + f"{exchange}{symbol}{month}"

        ModelClass = Log._mapper.get(class_name, None)
        if ModelClass is None:
            ModelClass = type(class_name, (db.Model,), {
                '__module__': __name__,
                '__name__': class_name,
                '__tablename__': "logs_" + month,

                'id': db.Column(db.Integer, primary_key=True, nullable=False),
                'ip': db.Column(db.String(191), index=True, nullable=False),
                'country': db.Column(db.String(191), index=True, nullable=True),
                'region': db.Column(db.String(191), index=True, nullable=True),
                'city': db.Column(db.String(191), index=True, nullable=True),
                'uri': db.Column(db.String(191), index=True, nullable=False),
                'args': db.Column(db.Text, nullable=False),
                'result': db.Column(db.Text, nullable=False),
                'create_time': db.Column(db.DateTime, nullable=False)
            })
            Log._mapper[class_name] = ModelClass

        return ModelClass

    @staticmethod
    def get_months():
        result = []
        table_names = db.engine.table_names()
        for table_name in table_names:
            if table_name.startswith("logs_"):
                result.append(table_name[5:])
        return result
