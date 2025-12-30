from django.db import models
from django.contrib.auth.models import AbstractUser
from config.utils import universal_upload_path

class User(AbstractUser):
    """ 继承自 AbstractUser """
    first_name = None
    last_name = None

    nickname = models.CharField(max_length=50, blank=True, verbose_name="昵称")
    avatar = models.ImageField(upload_to=universal_upload_path, verbose_name="头像", blank=True, null=True)
    bio = models.TextField(blank=True, verbose_name="个人简介")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname if self.nickname else self.username

    def get_full_name(self):
        return self.nickname if self.nickname else self.username
