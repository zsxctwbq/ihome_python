# coding:utf-8
from . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from ihome.utils.response_code import RET
from alipay import AliPay
from flask import g, current_app, jsonify, request
from ihome import db
from constants import ALIPAY_DOMAIN_NAME
import os


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """
    调用支付宝接口, 返回支付宝支付链接
    :param order_id: 接收订单的id
    :return: 链接地址 格式json
    """
    # 读取用户的id
    user_id = g.user_id

    # 校验该订单
    try:
        # 判断是否有该订单, 订单是否属于该用户, 订单是否是待支付状态
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"查询订单数据异常")

    if order is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"该订单不存在")

    # 业务处理
    # 创建支付宝sdk
    alipay = AliPay(
        appid="2016092500596768",  # 沙箱appid 或 线上appid
        app_notify_url=None,  # 默认回调url  不写的话这里用None
        app_private_key_path=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),  # 私钥
        alipay_public_key_path=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False   沙箱环境把这里设置为True
    )

    # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string 这是线上环境
    # 手机网站支付, 需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string 这是沙箱环境
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # 订单编号
        total_amount=str(order.amount/100.0),  # 总金额
        subject="爱家租房 %s" % order.id,  # 订单标题 随便写个字符串
        return_url="http://172.16.66.238:5000/payComplete.html",  # 返回的链接地址
        notify_url=None  # 可选, 不填则使用默认notify url  不填这里写None
    )

    pay_url = ALIPAY_DOMAIN_NAME + order_string

    return jsonify(errnum=RET.OK, errmsg=u"ok", data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """
    修改订单的状态, 保存支付宝交易号到数据库
    :return: 返回成功与否 格式json
    """

    # 接收参数, 并将参数装换成字典
    alipay_dict = request.form.to_dict()

    # 提取支付宝签名验证sign
    alipay_sign = alipay_dict.pop("sign")

    # 创建支付宝sdk
    alipay = AliPay(
        appid="2016092500596768",  # 沙箱appid 或 线上appid
        app_notify_url=None,  # 默认回调url  不写的话这里用None
        app_private_key_path=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),  # 私钥
        alipay_public_key_path=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False   沙箱环境把这里设置为True
    )

    # 判断是否是支付宝发送过来
    result = alipay.verify(alipay_dict, alipay_sign)

    if result:
        # 获取订单id
        order_id = alipay_dict.get("out_trade_no")
        # 获取交易号
        trade_no = alipay_dict.get("trade_no")
        try:
            Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

        return jsonify(errnum=RET.OK, errmsg=u"ok")