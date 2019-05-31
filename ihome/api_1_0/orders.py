# coding:utf-8
from . import api
from ihome.models import House, Order
from ihome.utils.commons import login_required
from flask import g, request, current_app, jsonify
from ihome.utils.response_code import RET
from datetime import datetime
from ihome import db, redis_store


@api.route("/orders", methods=["POST"])
@login_required
def save_orders():
    """
    保存订单信息
    传递参数: 房屋id 入住时间 结束时间 格式:json
    :return: 订单id json数据
    """
    # 获取用户的id
    user_id = g.user_id

    # 接收参数
    resp_dict = request.get_json()
    # 获取房屋的id
    house_id = resp_dict.get("house_id")
    # 获取入住时间
    start_date = resp_dict.get("start_date")
    # 获取结束时间
    end_date = resp_dict.get("end_date")

    # 校验参数
    # 判断参数的完整性
    if not all([house_id, start_date, end_date]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 判断是否是合法的入住时间, 结束时间, 入住时间是否小于等于结束时间, 并且计算出天数
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert start_date <= end_date
        # 防止用户入住时间是2019-05-20, 结束时间也是2019-05-20凌晨, 所以这里+1
        days = (end_date - start_date).days +1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.PARAMERR, errmsg=u"日期参数不合法")

    # 判断房屋id是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取房屋信息失败")

    if house is None:
        return jsonify(errnum=RET.NODATA, errms=u"房屋信息不存在")

    # 判断用户是否刷单
    if house.user_id == user_id:
        return jsonify(errnum=RET.ROLEERR, errmsg=u"操作无效")

    try:
        # 查询冲突的房屋订单数量
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取冲突订单信息失败")

    # count>0表示冲突的订单数量
    if count > 0:
        return jsonify(errnum=RET.DATAERR, errmsg=u"该房屋已被下单")

    # 业务处理

    # 计算总金额
    amount = house.price * days

    # 保存订单信息
    order = Order(
        user_id=user_id,
        house_id=house_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errnum=RET.DBERR, errmsg=u"保存订单信息失败")

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"ok", data={"order_id": order.id})


# /api/v1.0/user/orders?role=custom(顾客)  role=landlord(房东)
@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """
    获取用户的订单信息
    接收参数:role 是顾客的身份值为custom, 是房东的身份值为landlord
    :return: 订单信息 格式:json
    """

    # 获取用户的id
    user_id = g.user_id

    # 接收参数
    role = request.args.get("role")

    # 校验参数
    if not role:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数错误")

    # 业务处理
    if role == "landlord":
        # 房东的身份
        try:
            # 查询房东的自己的房子
            houses = House.query.filter(House.user_id == user_id).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errnum=RET.DBERR, errmsg=u"获取房东的房屋信息失败")
        if houses is None:
            return jsonify(errnum=RET.NODATA, errmsg=u"房屋信息不存在")
        # 把房东所有房子的id 提取出来做一个房屋id集合
        house_ids = [house.id for house in houses]

        try:
            # 查询订单的房子id在房东房屋id集合里的所有订单, 并且按创建爱你时间降序排序
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errnum=RET.DBERR, errmsg=u"获取房东的订单信息失败")
    else:
        # 顾客的身份
        # 订单的用户id等于当前用户的id
        try:
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errnum=RET.DBERR, errmsg=u"获取顾客订单信息失败")

    if orders is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"订单不存在")

    # 订单集合
    order_dict_list = []
    # 获取订单id的集合
    for order in orders:
        # order.to_dict() 将order数据转换成字典数据
        order_dict_list.append(order.to_dict())

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"ok", data={"orders": order_dict_list})


# 接单传递action 拒单传递reason存这拒单原因
# 接单accept 拒单reject
@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """
    功能实现: 接单, 拒单
    接收前端传递的参数: 接单:action:存着接单:accept 拒单:reject
                    拒单:reason:存着拒单的原因
    :param order_id:订单的id int类型
    :return: 成功与否  格式json
    """

    # 获取用户的id
    user_id = g.user_id

    # 接收参数
    resp_dict = request.get_json()
    # 接收参数 用户点击接单 或 拒单 传递过来的参数
    action = resp_dict.get("action")

    # 校验参数
    if action not in("accept", "reject"):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数错误")

    try:
        # 判断订单是否存在, 判断订单是不是同一个订单
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"查询订单信息失败")

    if order is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"订单信息不存在")

    # 判断订单属不属于该房东, 这里不能放在filter查询条件里,
    # 因为房屋对订单是 一对多 所以用房屋可以直接获取房屋订单
    # 但是订单对房屋是 多对一 所以不能直接在filter里写(Order.house.user_id == user_id)
    if order.house.user_id != user_id:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"操作无效")

    # 业务处理
    if action == "accept":
        # 将订单的状态改为待付款状态
        order.status = "WAIT_PAYMENT"

    elif action == "reject":
        # 获取拒单原因
        comment = resp_dict.get("reason")
        # 判断是否有填写拒单原因
        if comment is None:
            return jsonify(errnum=RET.NODATA, errmsg=u"请填写拒单原因")
        # 将订单的状态改为拒单
        order.status = "REJECTED"
        # 将订单的评论信息改为拒单原因
        order.comment = comment

    # 将订单信息保存到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errnum=RET.DBERR, errmsg=u"保存订单信息失败")

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"ok")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息
    前端传递参数:comment 格式json
    :param order_id:订单id
    :return: json
    """

    # 获取用户id
    user_id = g.user_id

    # 接收参数
    resp_dict = request.get_json()
    comment = resp_dict.get("comment")

    # 校验参数
    if not comment:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数错误")

    # 判断订单id是有效
    try:
        # 判断订单的id是否是接收的订单id, 该订单是否是待评价状态, 该订单是否是当前用户的订单
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_COMMENT", Order.user_id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取订单信息失败")

    if order is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"订单信息不存在")

    # 业务处理
    # 把订单状态改为已完成
    order.status = "COMPLETE"
    # 把订单的评价改为用户输入的评价
    order.comment = comment
    # 获取该订单的房屋
    house = order.house
    # 把房屋下的订单数量+1
    house.order_count += 1

    # 保存订单信息
    try:
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errnum=RET.DBERR, errmsg=u"保存数据失败")

    # 为了方房屋详情页面的评价信息同步, 删除redis缓存
    try:
        redis_store.delete("house_info_%s" % user_id)
    except Exception as e:
        current_app.logger.error(e)

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"ok")