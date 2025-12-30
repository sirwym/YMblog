from django.db import models
from django.conf import settings
from config.utils import universal_upload_path  # 复用之前的通用路径生成器


class ImageUpload(models.Model):
    # 关联用户 (知道是谁传的)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name="上传者")

    file = models.ImageField(upload_to=universal_upload_path, verbose_name="图片文件")

    name = models.CharField("图片名称", max_length=255, blank=True, help_text="留空，则使用文件名")
    size = models.PositiveIntegerField("文件大小(KB)", default=0)
    width = models.PositiveIntegerField("宽", default=0)
    height = models.PositiveIntegerField("高", default=0)
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "图片素材"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.file.name

    def save(self, *args, **kwargs):
        # 自动计算文件大小和文件名
        if self.file:
            if not self.name:
                self.name = self.file.name
            # 计算大小 (KB)
            self.size = self.file.size // 1024
            # 获取宽高 (需要 Pillow)
            # 这一步是可选的，如果为了性能可以去掉，但有宽高数据管理更方便
            try:
                from PIL import Image
                self.file.open()  # 确保文件已打开
                img = Image.open(self.file)
                self.width, self.height = img.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def url(self):
        """返回图片的完整 URL"""
        return self.file.url