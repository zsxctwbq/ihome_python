# coding:utf-8

from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_session import Session
import redis
import logging
from logging.handlers import RotatingFileHandler
from ihome.utils.commons import ReConverter

redis_store = None

db = SQLAlchemy()

# 配置日志信息
# 设置日志的记录等级
# 这个DEBUG这种设置只有在非调试的模式下才会成功
logging.basicConfig(level=logging.WARNING)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小(1024*1024*100)、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)


# 工厂模式
def create_app(config_name):
    """
    创建app
    :param config_name: str ("develop") ("product")
    :return: app
    """
    app = Flask(__name__)

    config_class = config_map.get(config_name)

    app.config.from_object(config_class)

    db.init_app(app)

    CSRFProtect(app)

    Session(app)

    # 自定义转换器注册到app里
    app.url_map.converters["re"] = ReConverter

    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # 注册蓝图
    from . import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    # 注册静态文件蓝图
    from ihome.web_html import html
    app.register_blueprint(html)

    return app