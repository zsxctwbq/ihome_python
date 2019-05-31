# coding:utf-8
import redis


class Config(object):
    """配置"""
    SECRET_KEY = "abcde"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@172.16.66.238:3306/ihome_python3"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 配置redis
    REDIS_HOST = "172.16.66.238"
    REDIS_PORT = 6379

    # 配置session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME =86400  # 设置session的有效期


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductConfig(Config):
    """生产环境配置"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductConfig
}