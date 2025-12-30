from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import ImageUpload
from unfold.contrib.filters.admin import RelatedDropdownFilter, RangeDateFilter # 记得导入这些
from unfold.widgets import UnfoldAdminImageFieldWidget

class CustomImageWidget(UnfoldAdminImageFieldWidget):
    template_name = "admin/widgets/custom_image_input.html"

@admin.register(ImageUpload)
class ImageUploadAdmin(ModelAdmin):

    # sql join user
    list_select_related = ["user"]

    list_display = ["preview_image", "file_info", "copy_markdown", "user", "created_at"]
    search_fields = ["name"]

    list_filter = [
        ("user", RelatedDropdownFilter),
        ("created_at", RangeDateFilter)
    ]

    show_full_result_count = False

    # 设为只读，防止随意修改已经上传的文件属性
    readonly_fields = ["width", "height", "size", "created_at", "preview_large", "user_name_display"]

    # 在详情页只显示这些
    fieldsets = (
        ("详细信息", {
            "fields": ("file", "name", "user_name_display", "created_at"),
            "classes": ("wide",),
        }),
        ("规格", {
            "fields": (("width", "height", "size"),),
            "classes": ("wide",),
        }),
    )

    add_fieldsets = (
        (None, {
            "fields": ("file", "name"),
            "classes": ("wide",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 找到 file 字段，把它的 widget 换掉
        if 'file' in form.base_fields:
            widget = CustomImageWidget()
            widget.attrs['placeholder'] = "点击选择文件 (支持 .jpg, .png)"
            form.base_fields['file'].widget = widget
        return form


    def save_model(self, request, obj, form, change):
        # 自动关联当前登录用户
        if not obj.user_id:
            obj.user = request.user

        if not obj.name and obj.file:
            # obj.file.name 获取的是上传的文件名 (包含后缀)
            obj.name = obj.file.name
        super().save_model(request, obj, form, change)

    # --- 自定义显示 ---
    @display(description="用户")
    def user_name_display(self, obj):
        username = obj.user.nickname if obj.user.nickname else obj.user.username
        return username

    @display(description="预览")
    def preview_image(self, obj):
        """列表页小图预览"""
        if obj.file:
            return format_html(
                '<img src="{}" loading="lazy" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.file.url
            )
        return "-"

    @display(description="大图预览")
    def preview_large(self, obj):
        if obj.file:
            return format_html(
                '<img id="id_image_preview" src="{}" style="max-width: 100%; max-height: 400px; border-radius: 8px; transition: all 0.3s ease;" />',
                obj.file.url
            )
        # 如果是新增页面，默认显示一个占位图或者空的 img 标签
        return format_html(
            '<img id="id_image_preview" src="" style="display: none; max-width: 100%; max-height: 400px; border-radius: 8px;" />'
        )

    @display(description="文件信息")
    def file_info(self, obj):
        return f"{obj.width}x{obj.height} | {obj.size}KB"

    @display(description="调用链接")
    def copy_markdown(self, obj):
        """一键复制 Markdown 代码的按钮"""
        if not obj.file:
            return "-"

        file_url = obj.file.url
        markdown_code = f"![{obj.name}]({file_url})"

        return format_html(
            '''
            <span 
                class="cursor-pointer text-xs font-bold transition-colors
                        hover:text-primary-600 dark:hover:text-primary-500"
                onclick="navigator.clipboard.writeText('{code}').then(() => {{ this.innerText = '已复制!'; setTimeout(() => {{ this.innerText = '复制 MD'; }}, 2000); }})"
            >
                复制 MD
            </span>
            ''',
            code=markdown_code
        )

