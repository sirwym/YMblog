from django.contrib import admin
from unfold.admin import ModelAdmin
from django.db.models import Count
from django.db import models
from .models import Category, Tag, Post
from unfold.decorators import display
from unfold_markdown.widgets import MarkdownWidget
from unfold.widgets import UnfoldAdminTextareaWidget
from simple_history.admin import SimpleHistoryAdmin
from django.utils import timezone
from django import forms
from django.utils.html import format_html
from unfold.contrib.filters.admin import (
    RangeDateFilter,
    RelatedDropdownFilter,
    MultipleRelatedDropdownFilter,
    ChoicesRadioFilter
)

######################################################################
# 文章分类管理
######################################################################
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    # 列表页
    list_display = ("name", "slug", "post_count_display")
    # 搜索
    search_fields = ("name",)

    # 自动生成URL
    prepopulated_fields = {"slug": ("name",)}

    # 分页
    list_per_page = 30

    def get_queryset(self, request):
        """查询"""
        qs = super().get_queryset(request)
        return qs.annotate(post_count=Count('post'))

    @display(description="文章数", label=True)
    def post_count_display(self, obj):
        return obj.post_count

######################################################################
# 文章标签管理
######################################################################
@admin.register(Tag)
class TagAdmin(ModelAdmin):
    # 列表页
    list_display = ("name", "slug", "post_count_display", )
    # 搜索
    search_fields = ("name",)
    # 自动url
    prepopulated_fields = {"slug": ("name",)}

    # 分页
    list_per_page = 30

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(post_count=Count('post'))

    @display(description="文章数", label=True)
    def post_count_display(self, obj):
        return obj.post_count

######################################################################
# 文章管理
######################################################################


class UnfoldHistoryAdmin(ModelAdmin, SimpleHistoryAdmin):
    pass

class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            "excerpt": UnfoldAdminTextareaWidget(
                attrs={
                    "rows": 2,
                    "placeholder": "在此输入简短的摘要...",
                }
            ),
            "content": MarkdownWidget(),
        }


@admin.register(Post)
class PostAdmin(UnfoldHistoryAdmin):

    form = PostAdminForm

    list_select_related = ['category']

    show_full_result_count = False

    # 列表页
    list_display = ['title', 'category', 'is_encrypted_icon', 'views', 'status_badge', 'published_at', 'updated_at_display']

    # 历史分页
    history_list_per_page = 50


    # 筛选
    list_filter = [
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("published_at", RangeDateFilter),
        ("status",ChoicesRadioFilter)
    ]
    list_filter_submit = True

    # 隐藏字段
    exclude = ('author',)

    # 搜索
    search_fields = ['title', 'excerpt', 'content']

    # 自动填写slug
    prepopulated_fields = {'slug': ('title',)}

    # 下拉框
    autocomplete_fields = ['category', 'tags']

    # 只读
    readonly_fields = ["views", "updated_at_display", "published_at_display"]

    # 选择框
    radio_fields = {"status": admin.HORIZONTAL}

    # 详情页
    fieldsets = (
        ("基本信息", {
            "fields": (("title", "slug"), ("category", "tags"),"excerpt","password","status","published_at_display","updated_at_display"),
            "classes": ("tab",),
        }),
        ("内容创作", {
            "fields": ("content",),
            "classes": ("tab",),
        }),
    )

    # 添加页
    add_fieldsets = (
        ("基本信息", {
            "fields": (("title", "slug"), ("category", "tags"), "excerpt", "password","status"),
            "classes": ("tab",),  # Unfold 特性：让这个分组看起来更紧凑
        }),
        ("内容创作", {
            "fields": ("content",),
            "classes": ("tab",),  # 宽屏显示
        }),
    )

    # 分页
    list_per_page = 30

    formfield_overrides = {
        models.TextField: {"widget": MarkdownWidget}
    }

    def get_form(self, request, obj=None, **kwargs):
        """form禁用一些按钮"""
        form = super().get_form(request, obj, **kwargs)
        for field_name in ['tags', 'category']:
            field = form.base_fields.get(field_name)
            if field:
                field.widget.can_add_related = False
                field.widget.can_change_related = False
                field.widget.can_view_related = False
                field.widget.can_delete_related = False

        return form

    @display(description="变更详情")
    def changes_summary(self, obj):
        """
        计算当前版本与上一个版本的差异。
        如果是 'content' 这种大字段，只显示“内容已更新”，不显示具体文字。
        """
        # 获取上一条记录 (如果没有上一条，说明是新建)
        prev_record = obj.prev_record
        if not prev_record:
            return "✨ 首次创建"

        # 计算差异
        delta = obj.diff_against(prev_record)
        changes = []

        for change in delta.changes:
            field_name = change.field

            # 🟢 关键逻辑：针对大字段进行特殊处理
            if field_name == "content":
                # 对于文章正文，只显示一个标记，不显示几千字的内容
                changes.append('<span class="text-blue-600 font-bold">📝 正文内容已更新</span>')
            elif field_name == "title":
                # 对于短字段，可以显示变化 (旧 -> 新)
                changes.append(f"标题: {change.old} &rarr; {change.new}")
            elif field_name == "status":
                changes.append(f"状态: {change.old} &rarr; {change.new}")
            else:
                # 其他字段
                changes.append(f"{field_name} 已变更")

        if not changes:
            return "无实质修改"

        # 用 HTML 换行连接所有变更
        return format_html("<br>".join(changes))

    @display(description="状态", label={
        "草稿": "warning",
        "已发布": "success",
    })
    def status_badge(self, obj):
        return obj.get_status_display()

    @display(description="上次更新")
    def updated_at_display(self, obj):
        if not obj.updated_at:
            return "-"
        return timezone.localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M")

    @display(description="发布时间")
    def published_at_display(self, obj):
        if not obj.published_at:
            return "-"
        return timezone.localtime(obj.published_at).strftime("%Y-%m-%d %H:%M")

    @display(description="分类", label=True)
    def category_badge(self, obj):
        return obj.category.name if obj.category else "-"

    @display(description="加密", boolean=True)
    def is_encrypted_icon(self, obj):
        return obj.is_encrypted

    def save_model(self, request, obj, form, change):
        """自动填入用户"""
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


    class Media:
        css = {
            "all": (
                "admin/css/admin_extra.css",
            )
        }

