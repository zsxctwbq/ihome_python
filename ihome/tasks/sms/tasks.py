# coding:utf-8

from ihome.tasks.main import app
from ihome.libs.yuntongxun.sms import CCP


@app.task
def send_template_sms(to, datas, temp_id):
    """
    发送短信 用户手机号 [验证码, 时间] 1
    :return: 0代表成功 -1代表失败
    """
    ccp = CCP()
    ret = ccp.sendTemplateSMS(to, datas, temp_id)
    return ret