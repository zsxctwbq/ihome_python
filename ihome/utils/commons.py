# coding:utf-8
from werkzeug.routing import BaseConverter
from ihome.utils.response_code import RET
from flask import session, g, jsonify
import functools

class ReConverter(BaseConverter):
    """自定义转换器"""
    def __init__(self, url_map, regex):
        super(ReConverter, self).__init__(url_map)

        # 保存文件名
        self.regex = regex


# 定义的验证登录状态的装饰器
def login_required(view_func):
    """"""

    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            # 用户已登录
            # 把用户id保存在g对象中
            g.user_id = user_id
            # 返回你调用的函数及参数
            return view_func(*args, **kwargs)
        else:
            return jsonify(errnum=RET.SESSIONERR, errmsg=u"用户未登录")

    return wrapper