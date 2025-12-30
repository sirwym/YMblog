from django.contrib.admin.apps import AdminConfig
from constance.apps import ConstanceConfig as BaseConstanceConfig


class MyAdminConfig(AdminConfig):
    default_site = 'config.sites.MyAdminSite'


class MyConstanceConfig(BaseConstanceConfig):
    verbose_name = "系统配置中心"