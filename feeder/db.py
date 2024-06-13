from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from decimal import Decimal

engine = create_engine("", echo=True)
metadata = MetaData(engine)
base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Trade(object):
    _mapper = {}

    @staticmethod
    def model(exchange):
        class_name = 'Trade' + exchange.capitalize()
        model_class = Trade._mapper.get(class_name, None)
        if model_class is None:
            model_class = type(class_name, (base,), {
                '__module__': __name__,
                '__name__': class_name,
                '__tablename__': "trades_" + exchange.lower(),

                'id': Column(String(191), primary_key=True),
                'symbol': Column(String(191)),
                'exchange': Column(String(191)),
                'side': Column(String(191)),
                'amount': Column(Numeric(38, 8)),
                'price': Column(Numeric(38, 8)),
                'cost': Column(Numeric(38, 8)),
                'timestamp': Column(Numeric(13, 3)),
            })
            Trade._mapper[class_name] = model_class

        return model_class


class Market(base):
    __tablename__ = 'markets'

    id = Column(Integer, primary_key=True)
    phone = Column(String(191), unique=True)
    email = Column(String(191))
    password = Column(String(191))
    client_id = Column(String(191))
    update_time = Column(Integer)
    is_enable = Column(Boolean)

    def __repr__(self):
        return "<Market %r>" % self.id


# TradeBinance = Trade.model("Binance")
# TradeBinance.__table__.create(session.bind, checkfirst=True)
# TradeCoinbase = Trade.model("Coinbase")
# TradeCoinbase.__table__.create(session.bind, checkfirst=True)
# TradeGateio = Trade.model("Gateio")
# TradeGateio.__table__.create(session.bind, checkfirst=True)
# TradeHuobi = Trade.model("Huobi")
# TradeHuobi.__table__.create(session.bind, checkfirst=True)
# TradeOkx = Trade.model("OKX")
# TradeOkx.__table__.create(session.bind, checkfirst=True)

# Trade = Trade.model("Binance")
# trade = Trade()
# trade.id = "1"
# trade.symbol = "1"
# trade.exchange = "2"
# trade.side = "3"
# trade.amount = 1.0
# trade.price = 2.0
# trade.cost = 3.0
# trade.timestamp = 4
# session.add(trade)
# session.commit()