# coding:utf-8

from CCPRestSDK import REST
import ConfigParser

#主帐号
accountSid= '8aaf07086a58b9ec016a6e30b0510f39'

#主帐号Token
accountToken= '9289d50ff4e64191b44be58ae11d0b6b'

#应用Id
appId='8aaf07086a58b9ec016a6e30b0aa0f40'

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

#请求端口 
serverPort='8883'

#REST版本号
softVersion='2013-12-26'


class CCP(object):

    instance = None

    def __new__(cls):
        """"""
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)
            # 初始化REST yuntongxun
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj
        return obj

    def sendTemplateSMS(self, to, datas, temp_id):
        result = self.rest.sendTemplateSMS(to, datas, temp_id)

        # for k, v in result.iteritems():
        #
        # if k == 'templateSMS':
        # for k, s in v.iteritems():
        # print '%s:%s' % (k, s)
        # else:
        # print '%s:%s' % (k, v)
        # smsMessageSid:33ed7925d31c4cd5a5fe6dbf5edb6130
        # dateCreated:20190430211300
        # statusCode:000000

        status_code = result.get("statusCode")

        if status_code == "000000":
            # 发送成功
            return 0
        else:
            # 发送失败
            return -1

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id

    # for k,v in result.iteritems():
    #
    #     if k=='templateSMS' :
    #             for k,s in v.iteritems():
    #                 print '%s:%s' % (k, s)
    #     else:
    #         print '%s:%s' % (k, v)
    
   
#sendTemplateSMS(手机号码,内容数据,模板Id)

if __name__ == '__main__':
    ccp = CCP()
    res = ccp.sendTemplateSMS("17754416426", ["1234", 5], 1)
    print (res)