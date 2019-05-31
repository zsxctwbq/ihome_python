# coding:utf-8
from . import api
from ihome.utils.commons import login_required
from flask import request, current_app, g, jsonify, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db
from constants import QINIU_URL_FILELD


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    接收参数: 图片 用户id
    :return:
    """
    # 接收参数
    user_id = g.user_id
    image_avatar = request.files.get("avatar")

    # 校验参数
    # 判断图片是否为空
    if image_avatar is None:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"未上传图片")

    # 读取图片的值
    image_data = image_avatar.read()

    # 保存在七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.THIRDERR, errmsg=u"图片上传失败")

    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"图片保存失败")

    # 返回应答
    avatar_user = QINIU_URL_FILELD + file_name
    return jsonify(errnum=RET.OK, errmsg=u"图片上传成功", data={"avatar_user":avatar_user})


@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """
    接收参数: 用户名 用户id
    格式: json
    :return:
    """

    # 接收参数
    req_dict = request.get_json()
    user_id = g.user_id
    user_name = req_dict.get("name")

    # 校验参数
    if user_name is None:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"未上传用户名")

    try:
        User.query.filter_by(id=user_id).update({"name":user_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"用户名保存失败")

    # 更新session的name
    session["name"] = user_name

    # 反回应答
    return jsonify(errnum=RET.OK, errmsg=u"用户名保存成功", data={"name":user_name})


@api.route("/user", methods=["GET"])
@login_required
def get_user_profile():
    """获取用户信息"""

    # 获取用户的id
    user_id = g.user_id

    # 查询数据库, 读取用户的名称, 手机号
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取用户信息失败")

    # 判断用户是否为None
    if user is None:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"用户不存在")

    return jsonify(errnum=RET.OK, errmsg="ok", data=user.to_dict())


@api.route("/user/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户的真是信息"""

    # 获取用户id
    user_id = g.user_id

    # 查询数据库, 读取用户的真是姓名和身份证信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"获取用户信息失败")

    # 判断用户是否为None
    if user is None:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"用户不存在")

    return jsonify(errnum=RET.OK, errmsg="ok", data=user.auth_to_dict())


@api.route("/user/auth", methods=["POST"])
@login_required
def set_user_auth():
    """
    设置用户的真时姓名和身份证信息
    传递参数: 用户的真是姓名, 身份证信息
    格式: json
    :return:
    """

    # 获取用户id
    user_id = g.user_id

    # 接受数据
    resp_dict = request.get_json()

    # 判断数据是否为空
    if resp_dict is None:
        return jsonify(errnum=RET.PARAMERR, errmsg=u"用户未填写数据")

    # 获取用户的真是姓名和身份证信息
    real_name = resp_dict.get("real_name")
    id_card = resp_dict.get("id_card")

    # 校验参数
    if not all([real_name, id_card]):
        return jsonify(errnum=RET.PARAMERR, errmsg=u"参数不完整")

    # 查询数据库读取用户信息
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None)\
            .update({"real_name":real_name, "id_card":id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errnum=RET.DBERR, errmsg=u"数据库异常")

    return jsonify(errnum=RET.OK, errmsg="ok")