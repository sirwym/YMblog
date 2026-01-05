from django.contrib import admin
from django.forms import CheckboxInput
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from .models import Tool
from unfold.widgets import UnfoldAdminImageFieldWidget


class CustomImageWidget(UnfoldAdminImageFieldWidget):
    template_name = "admin/widgets/custom_image_input.html"


@admin.register(Tool)
class ToolAdmin(ModelAdmin):
    """工就管理"""
    list_display = ['title', 'url_name', 'password','is_active']
    list_editable = ('is_active',)
    search_fields = ('title', 'url_name')

    exclude = ('order',)

    ordering_field = "order"

    list_per_page = 30
    hide_ordering_field = True

    list_filter = [
        ("is_active", BooleanRadioFilter),
    ]
    list_filter_submit = True

    fieldsets = (
        (None, {
            "fields": ("title", 'description','icon',('url_name', 'password'),'is_active'),
            "classes": ("wide",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 找到 file 字段，把它的 widget 换掉
        if 'icon' in form.base_fields:
            widget = CustomImageWidget()
            widget.attrs['placeholder'] = "点击选择文件 (支持 .jpg, .png)"
            form.base_fields['icon'].widget = widget
        return form

