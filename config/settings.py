from pathlib import Path
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS
from datetime import datetime

import environ

######################################################################
# 基础路径 & 环境变量
######################################################################
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)

environ.Env.read_env(BASE_DIR / ".env")


######################################################################
# 通用配置
######################################################################
DEBUG = env("DEBUG")

SECRET_KEY = env("SECRET_KEY", default="dev-secret-key")
######################################################################
# 域名
######################################################################
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"]
)

######################################################################
# 应用安装
######################################################################
INSTALLED_APPS = [
    # Unfold Admin
    "unfold.apps.BasicAppConfig",
    "unfold_markdown",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.simple_history",
    "unfold.contrib.constance",

    # Django 自带应用
    # 'django.contrib.admin',
    'config.admin_apps.MyAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 第三方应用
    'debug_toolbar',
    "config.admin_apps.MyConstanceConfig",
    "constance.backends.database",
    "simple_history",
    "django_htmx",

    # 项目自定义应用
    'blog.apps.BlogConfig',
    'game.apps.GameConfig',
    'account.apps.AccountConfig',
    'upload.apps.UploadConfig',
    'core.apps.CoreConfig', # 放通用的逻辑
    "tools.apps.ToolsConfig",
]

######################################################################
# 中间件
######################################################################
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware", # debug中间件
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    "django_htmx.middleware.HtmxMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

######################################################################
# URL 配置
######################################################################
ROOT_URLCONF = 'config.urls'

######################################################################
# 模板配置
######################################################################
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 项目全局模板目录
        'APP_DIRS': True,                   # 启用各 app 的 templates 目录
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',   # 在模板中可使用 request
                'django.contrib.auth.context_processors.auth',  # 提供 user、perms 等
                'django.contrib.messages.context_processors.messages',  # 提供 messages
                'constance.context_processors.config',
            ],
        },
    },
]

######################################################################
# WSGI 配置
######################################################################
WSGI_APPLICATION = 'config.wsgi.application'

######################################################################
# 数据库配置
######################################################################
# 默认使用 SQLite，本地开发简单快速
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("DB_NAME", default="YMmysql"),       # 数据库名
        'USER': env("DB_USER", default="YMmysql"),         # 数据库用户名
        'PASSWORD': env("DB_PASSWORD", default="YMmysql123456"), # 数据库密码
        'HOST': env("DB_HOST", default="127.0.0.1"),    # 数据库主机
        'PORT': env("DB_PORT", default="3306"),         # 数据库端口
        'OPTIONS': {
            'charset': 'utf8mb4',                       # 支持emoji等特殊字符
        },
    }
}

######################################################################
# 密码验证
######################################################################
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

######################################################################
# 国际化
######################################################################
LANGUAGE_CODE = 'zh-hans'  # 中文简体
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

######################################################################
# 静态文件
######################################################################
STATIC_URL = 'static/'  # 静态资源 URL 前缀
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


######################################################################
# 自定义用户模型
######################################################################
AUTH_USER_MODEL = 'account.User'

######################################################################
# debug
######################################################################
INTERNAL_IPS = [
    "127.0.0.1",
]

######################################################################
# 缓存
######################################################################
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # redis://:密码@IP:端口/数据库编号
        # 本地通常是：redis://127.0.0.1:6379/1 (使用数据库 1)
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # 可选：连接池配置，高并发时有用
            # "CONNECTION_POOL_KWARGS": {"max_connections": 100},
        }
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 缓存常量
CACHE_KEYS = {
    "DASHBOARD_COUNTS": "dashboard:counts:v1",
}

CACHE_TIMEOUTS = {
    "DASHBOARD_COUNTS": 300,
}

# ==============================================================================
# 网站静态信息配置
# ==============================================================================
SITE_SUBHEADER = "内容创作与管理中心"
SITE_NAME = "YM blog"
SITE_DESCRIPTION = "分享 C++、算法与编程创作（含小游戏实践）的技术博客"
SITE_KEYWORDS = 'C++, Python, Django, turbowarp'
ICP_NUMBER = '豫ICP备2023025597号-1'
SITE_LOGO = "/static/img/ym-logo.png"
SITE_ICON = "/static/img/ym-icon.png"
LOGIN_IMAGE = '/static/img/login.png'
SITE_SYMBOL = "YM"
SITE_FAVICONS = [
    {
        "rel": "icon",
        "type": "image/svg+xml",
        "href": "/static/img/favicon/favicon.svg",
    },
    {
        "rel": "icon",
        "type": "image/x-icon",
        "href": "/static/img/favicon/favicon.ico",
    },
    {
        "rel": "icon",
        "type": "image/png",
        "sizes": "96x96",
        "href": "/static/img/favicon/favicon-96x96.png",
    },
    {
        "rel": "apple-touch-icon",
        "sizes": "180x180",
        "href": "/static/img/favicon/apple-touch-icon.png",
    },
    {
        "rel": "manifest",
        "href": "/static/img/favicon/site.webmanifest",
    },
]

# ==============================================================================
# CONSTANCE (动态配置)
# ==============================================================================
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_ADDITIONAL_FIELDS = {
    **UNFOLD_CONSTANCE_ADDITIONAL_FIELDS,
    "optional_str": [
        "django.forms.fields.CharField", # 依然使用 CharField
        {
            "required": False,  # 🟢 关键：允许为空
            # "widget": "unfold.widgets.UnfoldAdminTextInputWidget", # 保持 Unfold 的漂亮样式
            # 如果公告比较长，想用多行文本框，就把上面这行改成:
            "widget": "unfold.widgets.UnfoldAdminTextareaWidget",
        },
    ],
}
# 指定 'default' 缓存
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'

# 在服务启动时自动加载所有配置到内存中
CONSTANCE_DBS_CACHE_AUTOLOAD = True

#  定义配置项
CONSTANCE_CONFIG = {
    # --- 全局设置 ---
    'SITE_NAME': (SITE_NAME, '网站名称', str),
    'SITE_DESCRIPTION': (SITE_DESCRIPTION, '网站描述', 'optional_str'),
    'SITE_KEYWORDS': (SITE_KEYWORDS, 'SEO 关键词', str),
    'ICP_NUMBER': (ICP_NUMBER, 'ICP备案号', str),
    'MAINTENANCE_MODE': (False, '维护模式', bool),
}

# 分组显示
CONSTANCE_CONFIG_FIELDSETS = {
    '基本设置': ('SITE_NAME', 'SITE_DESCRIPTION', 'SITE_KEYWORDS', 'ICP_NUMBER'),
    '系统开关': ('MAINTENANCE_MODE',),
}

######################################################################
# unfold
######################################################################
UNFOLD = {
    "SITE_URL": "/",

    # 界面功能开关
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,

    # 🎨 颜色配置：深海蓝 (替换默认的紫色)
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",  # 主色调
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },

    # 🗂️ 侧边栏导航配置
    "SIDEBAR": {
        "show_all_applications": False,  # 关闭默认的应用列表，完全使用自定义导航
        "navigation": [
            {
                "title": _("概览"),
                "separator": False,
                "items": [
                    {
                        "title": _("仪表盘"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_staff,
                    },
                ],
            },
            {
                "title": _("内容管理"),
                "separator": True,
                "collapsible": False,  # 可折叠，平时不看
                "items": [
                    {
                        "title": _("撰写新文章"),
                        "icon": "edit_note",
                        "link": reverse_lazy("admin:blog_post_add"),
                        "permission": lambda request: request.user.has_perm("blog.add_post"),
                    },
                    {
                        "title": _("文章列表"),
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "permission": lambda request: request.user.has_perm("blog.view_post") or request.user.has_perm("blog.change_post"),
                    },
                    {
                        "title": _("文章分类"),
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                        "permission": lambda request: request.user.has_perm("blog.view_category"),
                    },
                    {
                        "title": _("文章标签"),
                        "icon": "label",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                        "permission": lambda request: request.user.has_perm("blog.view_tag"),
                    },
                ],
            },
            {
                "title": _("游戏中心"),
                "separator": True,
                "collapsible": True,  # 可折叠，平时不看
                "items": [
                    {
                        "title": _("所有游戏"),
                        "icon": "sports_esports",
                        "link": reverse_lazy("admin:game_game_changelist"),
                        "permission": lambda request: request.user.has_perm("game.view_game"),
                    },
                    {
                        "title": _("发布游戏"),
                        "icon": "upload_file",
                        "link": reverse_lazy("admin:game_game_add"),
                        "permission": lambda request: request.user.has_perm("game.add_game"),
                    },
                    {
                        "title": _("游戏分类"),
                        "icon": "category",
                        "link": reverse_lazy("admin:game_gamecategory_changelist"),
                        "permission": lambda request: request.user.has_perm("game.view_gamecategory"),
                    },
                    {
                        "title": _("游戏标签"),
                        "icon": "label",
                        "link": reverse_lazy("admin:game_gametag_changelist"),
                        "permission": lambda request: request.user.has_perm("game.view_gametag"),
                    },
                ],
            },
            {
                "title": _("工具箱"),
                "separator": True,
                "collapsible": True,  # 可折叠，平时不看
                "items": [
                    {
                        "title": _("所有工具"),
                        "icon": "home_repair_service",
                        "link": reverse_lazy("admin:tools_tool_changelist"),
                        "permission": lambda request: request.user.has_perm("tools.view_tool"),
                    },
                    {
                        "title": _("添加工具"),
                        "icon": "add_circle",
                        "link": reverse_lazy("admin:tools_tool_add"),
                        "permission": lambda request: request.user.has_perm("tools.add_tool"),
                    },
                ],
            },
            {
                "title": _("资源管理"),
                "separator": True,
                "collapsible": True,  # 可折叠，平时不看
                "items": [
                    {
                        "title": _("图床相册"),
                        "icon": "photo_library",  # 图标：相册
                        "link": reverse_lazy("admin:upload_imageupload_changelist"),
                        "permission": lambda request: request.user.has_perm("upload.view_imageupload"),
                    },
                    {
                        "title": _("上传新图片"),
                        "icon": "add_a_photo",    # 图标：添加图片
                        "link": reverse_lazy("admin:upload_imageupload_add"),
                        "permission": lambda request: request.user.has_perm("upload.add_imageupload"),
                    },
                ],
            },
            {
                "title": _("系统设置"),
                "collapsible": True,
                "separator": True,
                "items": [
                    {
                        "title": _("用户管理"),
                        "icon": "people",
                        "link": reverse_lazy("admin:account_user_changelist"),
                        "permission": lambda request: request.user.has_perm("account.view_user"),
                    },
                    {
                        "title": _("用户组"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.has_perm("auth.view_group") and request.user.is_superuser,
                    },
                    {
                        "title": _("网站配置"),
                        "icon": "settings",  # 图标
                        "link": reverse_lazy("admin:constance_config_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },

    "DASHBOARD_CALLBACK": "core.dashboard.dashboard_callback",
    "STYLES": [
        lambda request: static("admin/css/dashboard.css"),
        lambda request: static("css/katex.min.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/katex.min.js"),
        lambda request: static("js/auto-render.min.js"),
        lambda request: static("admin/js/admin_katex_config.js"),
    ],
}


######################################################################
# iframe 设置
######################################################################
X_FRAME_OPTIONS = 'SAMEORIGIN'

######################################################################
# 评测机 设置
######################################################################
GO_JUDGE_BASE_URL = env('GO_JUDGE_BASE_URL', default="http://localhost:5050")
MEMORY_LIMIT_MB = env.int('MEMORY_LIMIT_MB', default=256)
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_MB * 1024 * 1024


######################################################################
# 日志 设置
######################################################################
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{process}] {name}: {message}',
            'style': '{',
        },
    },

    'handlers': {
        # 1. 业务日志文件 (记录 INFO 及以上)
        # 使用 RotatingFileHandler 限制大小
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 20 * 1024 * 1024,  # 单个文件最大 20MB (调小一点)
            'backupCount': 5,  # 保留 5 个备份 (共 100MB)
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # 2. 错误日志文件 (只记录 ERROR 及以上，包含堆栈)
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/error.log',
            'maxBytes': 20 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },

    # 根日志：兜底用的，防止有漏网之鱼
    'root': {
        'handlers': ['error_file', 'console'],  # 根日志只记录到错误文件和控制台
        'level': 'WARNING',  # ✅ 调高：平时不记录废话，除非有警告或错误
    },

    'loggers': {
        # 1. Django 框架日志
        'django': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'WARNING',  # ✅ 关键：设为 WARNING。忽略掉普通的 HTTP 200 请求记录，除非出错了。
            'propagate': False,
        },
        'tools': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',  # ✅ 保持 INFO：你需要知道代码有没有开始编译、有没有收到请求。
            'propagate': False,
        },
        'game': {'handlers': ['file', 'error_file'], 'level': 'INFO', 'propagate': False},
        'blog': {'handlers': ['file', 'error_file'], 'level': 'INFO', 'propagate': False},
        'httpx': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
######################################################################
# AI key
######################################################################
LLM_API_KEY = env('LLM_API_KEY', default=None)
LLM_API_URL = env('LLM_API_URL', default=None)

######################################################################
# 安全设置
######################################################################
if not DEBUG:

    # 1. 强制 HTTPS 重定向
    # 确保你的服务器(Nginx)配置了SSL证书，否则开启后会导致无限循环重定向
    SECURE_SSL_REDIRECT = True

    # 2. Cookie 安全
    # 只有在 HTTPS 下才发送 Cookie，防止会话劫持
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # 3. HSTS (HTTP Strict Transport Security)
    # 告诉浏览器未来一年内只能通过 HTTPS 访问，防止降级攻击
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # 4. 内容安全策略 (可选，如果遇到样式/脚本加载报错需微调)
    # SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_BROWSER_XSS_FILTER = True

    # 5. 信任的代理设置 (配合 Nginx 使用)
    # 告诉 Django 它是运行在 Nginx 代理后面的，信任 Nginx 传来的 HTTPS 头
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

######################################################################
# 异步设置
######################################################################
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/2'  # 任务队列
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/3' # 结果存储
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'