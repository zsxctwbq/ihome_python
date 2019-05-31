# coding:utf-8

from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import User
from sqlalchemy.exc import IntegrityError
from constants import LOGIN_ERROR_MAX_TIMES, LOGIN_ERROR_FORBID_TIME
import re

@api.route("/users", methods=["POST"])
def register():
    """
    注册
    请求参数: 手机号  短信验证码    密码   确认密码
    请求格式: json
    :return:
    """
    # 接收数据
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验数据
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 手机号格式是否正确
    if not re.match(r"1[345678]\d{9}", mobile):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"手机格式不正确")

    # 两次密码是否一直
    if password != password2:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    # 判断验证码是否过期
    if real_sms_code is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"验证码失效")

    # 删除验证码, 防止重复使用
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断验证码是否一直
    if real_sms_code.lower() != sms_code.lower():
        return jsonify(errnum=RET.DATAERR, errmsg=u"验证码输入错误")

    # 业务处理
    # 判断手机号是否存在(我们这里可以借用模型类手机号不能相同, 来让数据库只查询一次)
    # 把用户信息存到数据库中
    user = User(name=mobile, mobile=mobile)
    # 调用模型类的password方法
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errnum=RET.DATAEXIST, errmsg=u"手机号已存在")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errnum=RET.DATAEXIST, errmsg=u"查询数据库异常")

    # 保存用户的登录状态
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """
    用户登录
    传递参数: 手机号  密码
    格式: json
    :return:
    """

    # 接收参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 校验参数
    # 判断参数是否完整
    if not all([mobile, password]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 判断手机格式是否正确
    if not re.match(r"1[345678]\d{9}", mobile):
        return jsonify(errnum=RET.PARAMERR, errms=u"手机格式不正确")

    # 输入错误5次, 封ip10分钟
    # 查询ip
    user_ip = request.remote_addr
    try:
        access_num = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_num is not None and int(access_num) >= LOGIN_ERROR_MAX_TIMES:
            return jsonify(errnum=RET.REQERR, errmsg=u"请求次数过多, 请稍后再试")

    # 根据手机号查询数据库, 判断有没该用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnu=RET.DBERR, errmsg=u"获取用户信息失败")

    # 判断是否有该用户并且进行密码比对
    if user is None or not user.check_password(password):
        # 记录登录次数, 并且设置有效期
        try:
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip, LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errnum=RET.ROLEERR, errmsg=u"没有该用户")



    # 业务处理
    # 保存用户登录状态到session中
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    # 返回应答
    return  jsonify(errnum=RET.OK, errmsg=u"登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """查询用户的登录"""
    # 由于前端要把用户名显示在页面所以, 我们只查询name来判断
    name = session.get("name")

    if name is not None:
        return jsonify(errnum=RET.OK, errmsg="true", data={"name":name})
    else:
        return jsonify(errnum=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    """用户退出登录"""
    csrf_token = session.get("csrf_token")
    session.clear()
    session["csrf_token"] = csrf_token
    return jsonify(errnum=RET.OK, errmsg=u"退出成功")