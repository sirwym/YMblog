from django.db import models
from config.utils import universal_upload_path


class GameCategory(models.Model):
    """游戏分类 (例如: 动作, 射击, 解谜)"""
    name = models.CharField("分类名称", max_length=50)
    slug = models.SlugField("URL别名", unique=True, allow_unicode=True)

    class Meta:
        verbose_name = "游戏分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class GameTag(models.Model):
    """游戏标签 (例如: Pixel, 2D, Hardcore)"""
    name = models.CharField("标签名称", max_length=50)
    slug = models.SlugField("URL别名", unique=True, allow_unicode=True)

    class Meta:
        verbose_name = "游戏标签"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class Game(models.Model):
    title = models.CharField(max_length=100, verbose_name="游戏名称")
    slug = models.SlugField(unique=True, verbose_name="URL别名", allow_unicode=True)
    description = models.TextField(blank=True, verbose_name="游戏简介")
    cover = models.ImageField(upload_to=universal_upload_path, blank=True, null=True, verbose_name="封面图")
    game_file = models.FileField(upload_to=universal_upload_path, verbose_name="游戏文件 (.html/.js)")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")

    category = models.ForeignKey(GameCategory, on_delete=models.SET_NULL,  null=True, blank=True,verbose_name="游戏分类")
    tags = models.ManyToManyField(GameTag,blank=True,verbose_name="游戏标签")

    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "小游戏"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title