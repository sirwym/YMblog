from unfold.sites import UnfoldAdminSite
from constance import config
from django.conf import settings


class MyAdminSite(UnfoldAdminSite):


    def each_context(self, request):
        context = super().each_context(request)

        # 3. 获取配置
        # 注意：这里 getattr 的第三个参数必须是具体的字符串，不能是 settings.XXX (除非你在 settings 里真的定义了)
        site_name = getattr(config, "SITE_NAME", settings.SITE_NAME)
        site_header = f"{site_name} 管理后台"
        site_title = site_name
        site_subheader = settings.SITE_SUBHEADER
        login_image = getattr(config, "LOGIN_IMAGE", settings.LOGIN_IMAGE)
        site_icon = getattr(config, "SITE_LOGO", settings.SITE_LOGO)
        site_favicons = settings.SITE_FAVICONS
        site_symbol = settings.SITE_SYMBOL
        context.update({
            "site_header": site_header,
            "site_title": site_title,
            "site_subheader": site_subheader,
            "login_image": login_image,
            # "site_logo": site_logo,
            "site_icon": site_icon,
            "site_favicons": site_favicons,
            "site_symbol": site_symbol,
        })
        return context