# coding:utf-8

from celery import Celery
from ihome.tasks import config

# 创建celery对象
app = Celery("ihome")

# 引用配置文件
app.config_from_object(config)

# 自动搜索任务
app.autodiscover_tasks(["ihome.tasks.sms"])