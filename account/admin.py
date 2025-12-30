from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group,Permission
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Count
from django import forms
from unfold.widgets import UnfoldAdminSelect2MultipleWidget,UnfoldAdminSelectMultipleWidget


from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from unfold.decorators import display
from account.models import User as MyUser

# 注销组
admin.site.unregister(Group)

######################################################################
# 用户管理
######################################################################
@admin.register(MyUser)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "nickname", 'is_active', 'is_staff','last_login_display', 'date_joined_display')

    search_fields = ['username',]

    readonly_fields = ['last_login_display', 'date_joined_display', 'username_display']

    fieldsets = (
        ("基本信息", {
            'classes': ('tab',),
            'fields': (('username_display', 'nickname'), ('avatar', 'password'),'bio')
        }),
        ("权限设置", {
            'classes': ('tab',),
            'fields': ('is_active', 'is_staff', 'groups')
        }),
        ("重要日期", {
            'classes': ('tab',),
            'fields': ('last_login_display', 'date_joined_display')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (('username', 'nickname'),'avatar', 'bio', 'password1', 'password2'),
        }),
    )
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        groups = form.base_fields.get('groups')
        if groups:
            groups.widget = UnfoldAdminSelect2MultipleWidget()
        return form

    # def get_queryset(self, request):
    #     """超级管理员不可见"""
    #     qs = super().get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     return qs.filter(is_superuser=False)

    def has_change_permission(self, request, obj=None):
        """
        修改权限控制：
        1. 必须有基本的 change_user 权限。
        2. 如果试图修改的对象(obj)是超级管理员，且当前用户(request.user)不是超级管理员 -> 禁止。
        """
        has_perm = super().has_change_permission(request, obj)
        if not has_perm:
            return False
        if obj is None:
            return True

        if obj.is_superuser and not request.user.is_superuser:
            return False

        return True

    def has_delete_permission(self, request, obj=None):
        """
        删除权限控制：逻辑同上
        """
        has_perm = super().has_delete_permission(request, obj)
        if not has_perm:
            return False

        if obj is None:
            return True

        if obj.is_superuser and not request.user.is_superuser:
            return False

        return True

    @display(description="用户名")
    def username_display(self, obj):
        return obj.username

    @display(description="上次登录")
    def last_login_display(self, user):
        if not user.last_login:
            return "-"
        return timezone.localtime(user.last_login).strftime("%Y-%m-%d %H:%M")

    @display(description="加入日期")
    def date_joined_display(self, user):
        if not user.date_joined:
            return "-"
        return timezone.localtime(user.date_joined).strftime("%Y-%m-%d %H:%M")

######################################################################
# 组管理
######################################################################
class PermissionModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        """
        自定义每个选项的显示文本
        obj 是一个 Permission 对象
        """
        # 获取 App 名称 (例如 'blog')
        app_label = obj.content_type.app_label

        # 获取模型名称 (例如 '文章')
        model_name = obj.content_type.model_class()._meta.verbose_name

        action = obj.name
        if 'Can add' in action:
            action_cn = "新增"
        elif 'Can change' in action:
            action_cn = "修改"
        elif 'Can delete' in action:
            action_cn = "删除"
        elif 'Can view' in action:
            action_cn = "查看"
        else:
            action_cn = action  # 其他情况保持原样

        # 最终返回的格式：【Blog】 文章 - 新增
        return f"【{app_label.title()}】 {model_name} - {action_cn}"

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    list_display = ("name", 'users_count_display')


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "permissions":
            # 排除掉不需要的app
            exclude_apps = ['admin', 'contenttypes', 'sessions', 'auth']

            qs = Permission.objects.exclude(content_type__app_label__in=exclude_apps)
            kwargs["queryset"] = qs
            kwargs["form_class"] = PermissionModelMultipleChoiceField
            kwargs["widget"] = UnfoldAdminSelectMultipleWidget(
                attrs={"style": "height: 400px;"}
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(user_count=Count('user'))

    @display(description="用户数量", label=True)
    def users_count_display(self, user):
        return user.user_count