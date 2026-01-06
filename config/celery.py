import os
from celery import Celery

# 设置默认 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # 注意：把 'config.settings' 换成你实际的 settings 路径，看你的 wsgi.py 里是怎么写的，通常是 '项目名.settings'

app = Celery('YMblog') # 项目名

# 从 Django settings 加载配置，所有 Celery 配置项都以 CELERY_ 开头
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各个 app 下的 tasks.py
app.autodiscover_tasks()