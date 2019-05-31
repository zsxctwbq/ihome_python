# coding:utf-8

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, db
from ihome.utils.response_code import RET
from constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES, SEND_SMS_INTERVAL
from flask import current_app, jsonify, make_response, request
from ihome.models import User
# from ihome.libs.yuntongxun.sms import CCP
from ihome.tasks.sms.tasks import send_template_sms
import random

@api.route("/image_codes/<image_code_id>")
def get_image_codes(image_code_id):
    """"""
    # 接收数据(不用)

    # 校验数据(不用)

    # 业务处理
    # 生成验证码图片
    name, text, image_data = captcha.generate_captcha()

    # 把验证码图片的编号和真实数据验证码存储到redis
    try:
        redis_store.setex("image_code_%s"%image_code_id, IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg="save image code id failed")

    # 返回应答
    # 返回图片
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/jpg"
    return response

# # api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route("/sms_codes/<re(r'1[345678]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     """获取短信验证码"""
#     # 接收数据
#     image_code = request.args.get("image_code")
#     image_code_id = request.args.get("image_code_id")
#
#     # 校验数据
#     if not all([image_code, image_code_id]):
#         return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")
#
#     # 业务处理
#     # 从redis获取图片验证码真是数据
#     try:
#         real_image_code = redis_store.get("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errnum=RET.DBERR, errmsg=u"redis数据库异常")
#
#     # 判断是否过期
#     if real_image_code is None:
#         # 图片验证码过期
#         return jsonify(errnum=RET.NODATA, errmsg=u"图片验证码失效")
#
#     # 删除验证码, 防止用户用image_code_id一直尝试(一个验证码只能输入一次)
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 对比用户的输入
#     if real_image_code.lower() != image_code.lower():
#         return jsonify(errnum=RET.DATAERR, errmsg=u"用户输入有误")
#
#     # 判断用户输入的手机号我们在60秒内发送过短信没, 超过60秒,
#     # 我们跟他生成一条短信, 超过60秒我们不做任何操作
#     try:
#         send_flag = redis_store.get("send_sms_code_%s" % mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             return jsonify(errnum=RET.REQERR, errmsg=u"操作频繁, 请60秒后重试")
#
#     # 判断手机号是否存在
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             return jsonify(errnum=RET.DATAEXIST, errmsg=u"手机号已存在")
#
#     # 生成短信验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存真是的短信验证码
#     try:
#         redis_store.setex("sms_code_%s" % mobile, SMS_CODE_REDIS_EXPIRES, sms_code)
#         redis_store.setex("send_sms_code_%s" % mobile, SEND_SMS_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errnum=RET.DATAERR, errmsg=u"redis保存短信验证码失败")
#
#     # 发送短信验证码
#     try:
#         ccp = CCP()
#         result = ccp.sendTemplateSMS(mobile, [sms_code, int(SMS_CODE_REDIS_EXPIRES/60)], 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errnum=RET.THIRDERR, errmsg=u"发送短信失败")
#
#     # 返回应答
#     if result == 0:
#         # 发送成功
#         return jsonify(errnum=RET.OK, errmsg=u"发送成功")
#     else:
#         # 发送失败
#         return jsonify(errnum=RET.THIRDERR, errmsg=u"发送失败")


# api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
@api.route("/sms_codes/<re(r'1[345678]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 接收数据
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    # 校验数据
    if not all([image_code, image_code_id]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 业务处理
    # 从redis获取图片验证码真是数据
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"redis数据库异常")

    # 判断是否过期
    if real_image_code is None:
        # 图片验证码过期
        return jsonify(errnum=RET.NODATA, errmsg=u"图片验证码失效")

    # 删除验证码, 防止用户用image_code_id一直尝试(一个验证码只能输入一次)
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 对比用户的输入
    if real_image_code.lower() != image_code.lower():
        return jsonify(errnum=RET.DATAERR, errmsg=u"用户输入有误")

    # 判断用户输入的手机号我们在60秒内发送过短信没, 超过60秒,
    # 我们跟他生成一条短信, 超过60秒我们不做任何操作
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            return jsonify(errnum=RET.REQERR, errmsg=u"操作频繁, 请60秒后重试")

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            return jsonify(errnum=RET.DATAEXIST, errmsg=u"手机号已存在")

    # 生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真是的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile, SMS_CODE_REDIS_EXPIRES, sms_code)
        redis_store.setex("send_sms_code_%s" % mobile, SEND_SMS_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DATAERR, errmsg=u"redis保存短信验证码失败")

    # 发送短信验证码
    # try:
    #     ccp = CCP()
    #     result = ccp.sendTemplateSMS(mobile, [sms_code, int(SMS_CODE_REDIS_EXPIRES/60)], 1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errnum=RET.THIRDERR, errmsg=u"发送短信失败")

    # result是一个对象
    # ('result:', < AsyncResult: e64e5d3a-57a3-4de3-b48b-15b96e2bd230 >)
    # ('result.id:', 'e64e5d3a-57a3-4de3-b48b-15b96e2bd230')
    # ("ret:", 0)
    result = send_template_sms.delay(mobile, [sms_code, int(SMS_CODE_REDIS_EXPIRES / 60)], 1)
    print("result:", result)
    # result.id 是去 这个任务的id
    print("result.id:", result.id)
    # get方法获取这个任务执行的返回结果 这里是堵塞的 只有celery执行完了 这里才能继续
    ret = result.get()
    print(ret)
    return jsonify(errnum=RET.OK, errmsg=u"发送成功")

    # 返回应答
    # if result == 0:
    #     # 发送成功
    #     return jsonify(errnum=RET.OK, errmsg=u"发送成功")
    # else:
    #     # 发送失败
    #     return jsonify(errnum=RET.THIRDERR, errmsg=u"发送失败")