# coding:utf-8

# 图片验证码数据保存在redis的时间 单位:秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码数据保存在redis的时间 单位:秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信的间隔时间 单位:秒
SEND_SMS_INTERVAL = 60

# 登录错误尝试的次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误限制的时间, 单位:秒
LOGIN_ERROR_FORBID_TIME = 600

# 七牛的域名
QINIU_URL_FILELD = "http://pqxmtapmt.bkt.clouddn.com/"

# 缓存在redis城区数据保存时间 单位: 秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页展示做多的房间数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的Redis缓存时间, 单位: ,秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页展示评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据redis缓存时间, 单位:秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 反顾我列表每页展示的数据
HOUSE_LIST_PAGE_DATE_BARS = 2

# 房屋列表页面的缓存时间, 单位:秒
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# alipay的域名
ALIPAY_DOMAIN_NAME = "https://openapi.alipaydev.com/gateway.do?"