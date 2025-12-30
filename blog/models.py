from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from simple_history.models import HistoricalRecords
from django.conf import settings

######################################################################
# 分类
######################################################################
class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="分类名称")
    slug = models.SlugField("URL别名", unique=True, allow_unicode=True)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

######################################################################
# 标签
######################################################################
class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name="标签名称")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="URL别名")

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

######################################################################
# 文章
######################################################################
STATUS_CHOICES = (("draft", "草稿"),("published", "已发布"),)
class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="文章标题")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="URL别名", help_text="用于生成文章链接")
    excerpt = models.TextField(blank=True, verbose_name="摘要", help_text="可留空，留空时自动从正文生成")
    content = models.TextField(verbose_name="正文 (Markdown)")

    history = HistoricalRecords() # 历史

    # 关联关系
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,  verbose_name="作者",related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="分类")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="标签")

    # 状态与权限
    status = models.CharField(max_length=10,choices=STATUS_CHOICES, default="draft", verbose_name="状态")
    password = models.CharField(max_length=50, blank=True, verbose_name="访问密码", help_text="留空则无需密码")

    # 统计与时间
    views = models.PositiveIntegerField(default=0, verbose_name="阅读量")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    class Meta:
        verbose_name = "文章"
        verbose_name_plural = verbose_name
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == "published" and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_encrypted(self):
        """判断文章是否加密"""
        return bool(self.password)