from django.db import models
from django.urls import reverse, NoReverseMatch
from config import utils


class Tool(models.Model):
    title = models.CharField(max_length=100, verbose_name="工具名称")
    description = models.TextField(blank=True, verbose_name="工具简介")
    icon = models.ImageField(upload_to=utils.universal_upload_path, blank=True, null=True, verbose_name="图标")
    url_name = models.CharField(max_length=100, verbose_name="URL 别名", help_text="对应 urls.py中的name")
    order = models.PositiveIntegerField(default=0, verbose_name="排序", db_index=True)
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    password = models.CharField(max_length=50, blank=True, verbose_name="访问密码", help_text="留空则无需密码")

    class Meta:
        ordering = ['order']
        verbose_name = "在线工具"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        if self.pk is None:
            max_order = Tool.objects.aggregate(models.Max('order'))['order__max'] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        try:
            return reverse(f"tools:{self.url_name}")
        except:
            return "#"