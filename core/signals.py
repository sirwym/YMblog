from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings

from blog.models import Post
from game.models import Game
from account.models import User

# 新增(save) 还是 删除(delete)，都触发
@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Game)
@receiver([post_save, post_delete], sender=User)
def clear_dashboard_cache(sender, **kwargs):
    """
    当题目、试卷或用户发生变动时，清空仪表盘的统计缓存。
    下次访问仪表盘时，会自动重新计算最新数据。
    """
    cache.delete(settings.CACHE_KEYS["DASHBOARD_COUNTS"])
    # print(f"检测到 {sender.__name__} 变动，已清除仪表盘缓存！") # 开发调试用，生产环境可注释