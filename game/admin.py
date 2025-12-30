from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import MultipleRelatedDropdownFilter,RelatedDropdownFilter,RangeDateFilter
from .models import Game, GameCategory, GameTag

######################################################################
# 游戏分类
######################################################################
@admin.register(GameCategory)
class GameCategoryAdmin(ModelAdmin):
    # 列表页
    list_display = ["name", "slug", "game_count_display"]
    # 搜索
    search_fields = ["name"]
    # 自动url
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(game_count=Count('game'))

    @display(description="游戏数量", label=True)
    def game_count_display(self, obj):
        return obj.game_count

######################################################################
# 游戏标签
######################################################################
@admin.register(GameTag)
class GameTagAdmin(ModelAdmin):
    # 列表页
    list_display = ["name", "slug", "game_count_display"]
    # 搜索
    search_fields = ["name"]
    # 自动url
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(game_count=Count('game'))

    @display(description="游戏数量", label=True)
    def game_count_display(self, obj):
        return obj.game_count

######################################################################
# 游戏管理
######################################################################
@admin.register(Game)
class GameAdmin(ModelAdmin):

    # SQL JOIN Category
    list_select_related = ["category"]

    # 列表页
    list_display = ["title", "category_badge", "is_public", "created_at"]

    # 关闭全量计数
    show_full_result_count = False

    # 筛选
    list_filter = [
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("created_at",RangeDateFilter),
        "is_public",
    ]
    list_filter_submit = True

    search_fields = ["title", "description"]

    autocomplete_fields = ["category", "tags"]

    prepopulated_fields = {"slug": ("title",)}

    readonly_fields = ["created_at", "updated_at"]

    # 详情页布局优化
    fieldsets = (
        ("基本信息", {
            "fields": (("title", "slug"), ("category", "tags")),
            "classes": ("tab",),
        }),
        ("资源上传", {
            "fields": ("game_file", "cover", "description"),
            "classes": ("tab",),
        }),
        ("发布设置", {
            "fields": ("is_public", "created_at", "updated_at"),
            "classes": ("tab",),
        }),
    )

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


    @display(description="分类", label=True)
    def category_badge(self, obj):
        return obj.category.name if obj.category else "未分类"