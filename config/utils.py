import os
import uuid
from datetime import datetime

def universal_upload_path(instance: object, filename):
    """
    通用上传路径生成器 按照模型名和日期年/月文件夹
    路径格式: {model_name}s/{year}/{month}/{old_filename}_{uuid[:10]}.{ext}
    """
    old_filename, ext = os.path.splitext(filename)
    new_filename = f"{old_filename}_{uuid.uuid4().hex[:10]}{ext}"
    model_name = instance._meta.model_name

    now = datetime.now()

    return os.path.join(
        f"{model_name}s",  # 根目录: games 或 posts (复数形式)
        str(now.year),  # 年: 2025
        str(now.month),  # 月: 12
        new_filename
    )

if __name__ == "__main__":

    print(universal_upload_path("blog", "abc.png"))

