import psutil
from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.contrib.auth import get_user_model
from django.conf import settings


def dashboard_callback(request, context):
    # =========================================================================
    # 1. 硬件监控
    # =========================================================================
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        mem_used_gb = round(mem.used / 1024 ** 3, 1)
        mem_total_gb = round(mem.total / 1024 ** 3, 1)

        # 这里返回的是你的 CSS 类名
        if disk.percent > 90:
            disk_color_class = "dashboard-bg-danger"
        elif disk.percent > 70:
            disk_color_class = "dashboard-bg-warning"
        else:
            disk_color_class = "dashboard-bg-primary"

    except Exception:
        cpu_percent, mem_used_gb, mem_total_gb = 0, 0, 0
        mem = type('obj', (object,), {'percent': 0})
        disk = type('obj', (object,), {'percent': 0})
        disk_color_class = "dashboard-bg-primary"

    # =========================================================================
    # 2. 业务数据
    # =========================================================================
    def get_business_data():
        from blog.models import Post
        from game.models import Game
        from upload.models import ImageUpload
        User = get_user_model()

        counts = {
            'post': Post.objects.count(),
            'game': Game.objects.count(),
            'image': ImageUpload.objects.count(),
            'user': User.objects.count(),
        }
        return counts

    # 缓存 5 分钟
    counts = cache.get_or_set(settings.CACHE_KEYS["DASHBOARD_COUNTS"],
                              get_business_data, settings.CACHE_TIMEOUTS["DASHBOARD_COUNTS"])

    # =========================================================================
    # 3. 构造数据 (这里不含 HTML，只含数据)
    # =========================================================================

    # 隐藏 Unfold 默认的应用列表 (如果你不想在仪表盘显示那个巨大的列表)
    context['available_apps'] = []

    context.update({
        # KPI 卡片数据
        "kpi": [
            {
                "title": _("CPU 负载"),
                "metric": f"{cpu_percent}%",
                # 我们这里不传 HTML，而是传进度条所需的数据，在模板里渲染
                "has_progress": True,
                "progress_val": cpu_percent,
            },
            {
                "title": _("内存使用"),
                "metric": f"{mem.percent}%",
                "footer": f"{mem_used_gb}GB / {mem_total_gb}GB",
            },
            {
                "title": _("内容总数"),
                "metric": counts['post'] + counts['game'],
                "footer": f"{counts['post']} 篇文章, {counts['game']} 个游戏",
            },
            {
                "title": _("用户总数"),
                "metric": counts['user'],
                "footer": f"累计上传 {counts['image']} 张图片",
            },
        ],

        # 进度条卡片数据
        "progress": [
            {
                "title": _("系统盘"),
                "description": f"已用 {disk.percent}%",
                "value": disk.percent,
                "color_class": disk_color_class,  # 这里传你的 CSS 类名
            },
        ],

        # 快捷导航数据
        "navigation": [
            {
                "title": _("写文章"),
                "text": _("发布新的博客内容"),
                "link": reverse_lazy("admin:blog_post_add"),
                "icon": "edit_note",
            },
            {
                "title": _("发游戏"),
                "text": _("添加新的小游戏"),
                "link": reverse_lazy("admin:game_game_add"),
                "icon": "sports_esports",
            },
            {
                "title": _("传图片"),
                "text": _("上传素材到图床"),
                "link": reverse_lazy("admin:upload_imageupload_add"),
                "icon": "add_a_photo",
            },
            {
                "title": _("看用户"),
                "text": _("管理注册用户"),
                "link": reverse_lazy("admin:account_user_changelist"),
                "icon": "people",
            },
        ],
    })

    return context