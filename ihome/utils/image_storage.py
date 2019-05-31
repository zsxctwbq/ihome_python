# -*- coding: utf-8 -*-
from qiniu import Auth, put_data, etag
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = 'fDvp2lAZFalSx0c6izNXwvHnMeOsrQWPdPSXjSuU'
secret_key = 'R5YlfCaHDG3xPTiPaylNgXldkbYPcIOqGqZI1T8e'

def storage(file_data):
    """
    七牛存储
    参数 file_data:二进制文件
    :return:
    """
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome-python3'

    # 上传后保存的文件名
    # key = 'my-python-logo.png'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    ret, info = put_data(token, None, file_data)
    print(info)
    print("*"*10)
    print(ret)
    if info.status_code == 200:
        # 保存成功
        return ret.get("key")
    else:
        raise Exception(u"保存图片失败...")
    # assert ret['key'] == key
    # assert ret['hash'] == etag(localfile)


if __name__ == '__main__':
    with open("/home/xiaoge/Desktop/a1.jpg", "rb") as f:
        file_data = f.read()
        storage(file_data)