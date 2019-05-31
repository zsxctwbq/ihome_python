# coding:utf-8
from . import api
from ihome.utils.commons import login_required
from flask import request, current_app, g, jsonify, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome import db, redis_store
from constants import QINIU_URL_FILELD, AREA_INFO_REDIS_CACHE_EXPIRES, HOME_PAGE_DATA_REDIS_EXPIRES, HOME_PAGE_MAX_HOUSES, HOUSE_DETAIL_REDIS_EXPIRE_SECOND, HOUSE_LIST_PAGE_DATE_BARS, HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES
from datetime import datetime
import json


@api.route("/areas", methods=["GET"])
def get_areas_info():

    # 尝试从redis中获取, 城区信息
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.info("hit redis area_info")
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库, 获取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    # 将获取到的城区信息装换成字典
    area_dict_li = []
    for area in area_li:
        # 去看area的模型类就只到了, 这是模型类的一个方法
        area_dict_li.append(area.to_dict())

    resp_dict = dict(errnum=RET.OK, errmsg="ok", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 把获取的城区信息, 保存到redis
    try:
        redis_store.setex("area_info",AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """
    保存房子的信息
    接收参数
    {
        房屋标题
        "title":"",
        房屋价格
        "price":"",
        所在城区
        "area_id":"",
        详细地址
        "address":"",
        房屋数量
        "room_count":"",
        房屋面积
        "acreage":"",
        房屋描述
        "unit":"",
        房屋能住人数
        "capacity":"",
        房屋卧床配置
        "beds":"",
        房屋押金
        "deposit":"",
        最少入住天数
        "min_days":"",
        最多入住天数
        "max_days":"",
        房间设施配置(可传可不传)
        "facility":[]
    }
    格式:json
    return: 房屋id 格式json
    """

    # 接收参数
    user_id = g.user_id
    house_dict = request.get_json()

    title = house_dict.get("title")
    price = house_dict.get("price")
    area_id = house_dict.get("area_id")
    address = house_dict.get("address")
    room_count = house_dict.get("room_count")
    acreage = house_dict.get("acreage")
    unit = house_dict.get("unit")
    capacity = house_dict.get("capacity")
    beds = house_dict.get("beds")
    deposit = house_dict.get("deposit")
    min_days = house_dict.get("min_days")
    max_days = house_dict.get("max_days")

    # 校验参数
    # 判断参数是否完整
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 判断房屋价格 和 押金输入是否合法
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.PARAMERR, errmsg=u"输入参数不合法")

    # 判断城区id是否合法
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    if area is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"城区不存在")

    # 判断房屋数目 房屋人数 房屋面积 最少入住天数 最多入住天数是否合法
    try:
        room_count = int(room_count)
        capacity = int(capacity)
        acreage = float(acreage)
        min_days = int(min_days)
        max_days = int(max_days)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数错误")

    # 业务处理
    # 创建房屋模型类对象, 把用户填写的数据添加进去
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 接收房屋设施信息
    facility_ids = house_dict.get("facility")

    if facility_ids:
        # 用有效数据
        # 查询数据库, 读取设施信息
        # select * from ih_facility_info where id in [] 等价于下面的那条查询语句
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errnum=RET.DBERR, errmsg=u"数据库查询失败")

        if facilities:
            # 把房屋设施信息添加到house对象中, 会自动添加到第三张表中
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errnum=RET.DBERR, errmsg=u"保存房屋数据失败")

    # 返回应答
    # 保存成功
    return jsonify(errnum=RET.OK, errmsg=u"保存成功", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存房屋图片
    接收数据: 图片 房屋di
    :return: 图片链接 json数据
    """

    # 接收数据
    house_id = request.form.get("house_id")
    house_image = request.files.get("house_image")

    # 校验数据
    # 判断参数是否完整
    if not all([house_id, house_image]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 判断房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    if house is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"房屋不存在")

    # 业务处理
    # 读取房屋图片数据
    image_data = house_image.read()

    # 保存在七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.THIRDERR, errmsg=u"保存图片失败")

    # 把如果House下的index_image_url为空时, 图片链接保存在House下的index_image_url 和 HouseImage下的url
    if not house.index_image_url:
        # 表示房屋下的index_image_url为空, index_image_url必须保存一张房屋的主图片
        house.index_image_url = file_name
        db.session.add(house)


    house_image = HouseImage(
        house_id=house_id,
        url=file_name
    )
    db.session.add(house_image)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"保存数据失败")

    # 构造上下文
    image_url = QINIU_URL_FILELD + file_name

    # 返回应答
    return jsonify(errnum=RET.OK, errmsg=u"保存图片成功", data={"image_url": image_url})


# @api.route("/user/houses", methods=["GET"])
# @login_required
# def get_user_houses():
#     """
#     获取用户发布的房源信息
#     :return:
#     """
#     # 获取用户的id
#     user_id = g.user_id
#
#     # 根据用户id查询房屋信息
#     try:
#         user = User.query.get(user_id)
#         # 这个用户发布的房源
#         houses = user.houses
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")
#
#     # 将查询到的房屋信息转换成字典存放在列表中
#     houses_list = []
#     if houses:
#         for house in houses:
#             # 把每间房子的基本信息都存放在这个houses_list里
#             houses_list.append(house.to_basic_dict())
#         return jsonify(errnum=RET.NODATA, errmsg=u"房屋信息不存在")
#
#     return jsonify(errnum=RET.OK, errmsg="ok", data={"houses_list": houses_list})
#
#
# @api.route("/houses/index", methods=["GET"])
# def get_houses_index():
#     """
#     获取首页幻灯片的房屋信息
#     :return: 房屋信息 格式:json
#     """
#
#     # 根据房屋的订单信息, 查询数据库
#     try:
#         houses = House.query.filter(House.order_count.desc).limit()


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """
    获取房东发布的房源信息
    :return:
    """

    # 获取用户的id
    user_id = g.user_id

    # 跟用户id 在用户铭心类查询房屋信息
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库库异常")

    # 校验数据
    if houses is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"房屋数据不存在")

    houses_list = []

    # 将房屋信息转换成字典数据
    for house in houses:
        houses_list.append(house.to_basic_dict())

    json_houses = json.dumps(houses_list)

    # 反回应答
    return '{"errnum":"0", "errmsg":"ok", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/index", methods=["GET"])
def get_houses_index():
    """获取首页房源信息"""

    # 先尝试从redis中获取
    try:
        result = redis_store.get("house_page_data")
    except Exception as e:
        current_app.logger.error(e)
        result = None
    if result:
        current_app.logger.info("hit house index info redis")
        return '{"errnum":"0", "errmsg":"ok", "data":%s}' % result, 200, {"Content-Type": "application/json"}

    # 根据订单量, 降序排序查, 最多显示5条数句
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    if houses is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"房屋信息不存在")

    house_li = []
    # 将房屋数据转换成字典
    for house in houses:
        if not house.index_image_url:
            continue
        house_li.append(house.to_basic_dict())

    json_house = json.dumps(house_li)

    # 将查询到的数据缓存到redis中
    try:
        redis_store.setex("house_page_data", HOME_PAGE_DATA_REDIS_EXPIRES, json_house)
    except Exception as e:
        current_app.logger.error(e)

    # 返回应答
    return '{"errnum":"0", "errmsg":"ok", "data":%s}' % json_house, 200, {"Content-Type": "application/json"}


@api.route("/house/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """
    获取房屋详情信息
    接收房屋的id
    :return:
    """
    # 获取用户的id 凡是这里我没有判断用户的登录, 说以只能从session里面取
    user_id = session.get("user_id", "-1")

    # 尝试从redis 缓存中提取数据
    try:
        result = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        result = None
    else:
        if result:
            current_app.logger.info("hit house detail info redis")
            return '{"errnum":"0", "errmsg":"ok", "data":{"user_id":%s, "house":%s}}' % (user_id, result), 200, \
                   {"Content-Type": "application/json"}

    # 从数据库里面, 读取房屋细信息
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    if house is None:
        return jsonify(errnum=RET.NODATA, errmsg=u"房屋信息不存在")

    # 将房屋信息转换成字典数据
    try:
        house_dict = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DATAERR, errmsg=u"数据出错")

    json_house = json.dumps(house_dict)

    # 将数据存储带redis缓存中
    try:
        redis_store.setex("house_info_%s" % house_id, HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    # 返回应答
    return '{"errnum":"0", "errmsg":"ok", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), 200, \
           {"Content-Type": "application/json"}


# GET /api/v1.0/houses?sd=2019-05-20&ed=2019-05-20&aid=area_id&sk=new&p=1
@api.route("/houses", methods=["GET"])
def get_house_list():
    """获取房屋列表信息"""

    # 接收参数
    start_date = request.args.get("sd", "")
    end_date = request.args.get("ed", "")
    area_id = request.args.get("aid", "")
    sort_key = request.args.get("sk", "new")
    page = request.args.get("p")

    # 校验参数
    try:
        # 判断用户是否填写入住日期
        if start_date:
            # strptime 是 字符串装换成时间
            # strftime 是 时间转换成字符串
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        # 判断用户是否填写结束日期
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # 判断入住日期是否小于结束日期
        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.PARAMERR, errmsg=u"日期参数错误")

    # 判断城区id是否存在
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

        if area is None:
            return jsonify(errnum=RET.NODATA, errmsg=u"城区信息不存在")

    # 判断是否传递页码
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 创建redis的缓存的哈希值的键
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}


    # 业务处理
    # 查询冲突的房子, 因为这里我们不等用订单来查询, 这样的话会忽略那些没下过订单的房子
    # 当用户传入了 入住日期 和 结束日期
    try:
        if start_date and end_date:
            orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        # 当用户只传入 入住日期
        elif start_date:
            orders = Order.query.filter(Order.end_date >= start_date).all()
        # 当用户只传入 结束日期
        elif end_date:
            orders = Order.query.filter(Order.begin_date <= end_date).all()
        else:
            orders = None
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取订单信息失败")

    # 根据订单对象, 提取出房屋id
    if orders:
        house_ids = [order.house_id for order in orders]
    else:
        house_ids = None

    # 条件参数列表容器
    condition_params = []
    if house_ids:
        condition_params.append(House.id.notin_(house_ids))

    if area_id:
        condition_params.append(House.area_id == area_id)

    # 查询数据库
    if sort_key == "booking":  # 入住最多
        house_query = House.query.filter(*condition_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":  # 价钱低到高
        house_query = House.query.filter(*condition_params).order_by(House.price.asc())
    elif sort_key == "price-des":  # 价钱高到低
        house_query = House.query.filter(*condition_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*condition_params).order_by(House.create_time.desc())

    # 获取分页对象
    try:
        #                               档期内页码         每页展示的数据                       自动错误警告
        page_obj = house_query.paginate(page=page, per_page=HOUSE_LIST_PAGE_DATE_BARS, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"分页出错")

    # 房子列表容器
    house_li = []
    # 获取当前页的数据
    houses = page_obj.items
    for house in houses:
        house_li.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    # 返回应答
    # 返回当前页的数据
    # return jsonify(errnum=RET.OK, errmsg=u"ok", data={"total_page": total_page, "houses": house_li, "current_page": page})

    # 将返回的数据转换成字典
    resp_dict = dict(errnum=RET.OK, errmsg=u"ok", data={"total_page": total_page, "houses": house_li, "current_page": page})

    # 将字典数据转换成json数据
    resp_json = json.dumps(resp_dict)

    # 创建redis缓存中的键
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)

    # 用户的输入页码大于总页数时不做缓存
    if page < total_page:
        # 使用redis缓存, 我们这里用哈希, 由于一次执行多条redis语句, 防止语句变成永久有效, 我们这里用到pipeline
        try:
            # 创建redis管道, 管道的用法和redis的用法一样
            pipeline = redis_store.pipeline()

            # 开启一次执行多条语句的任务
            pipeline.multi()

            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)

            # 执行语句
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}