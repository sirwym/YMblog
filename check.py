# 在项目根目录下运行: python check_path.py
import os
import sys

# 假设你的项目结构是标准的 Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.conf import settings

print(f"Django 认为文件应该写在这里: {settings.JUDGE_HOST_DIR}")
print(f"Docker 实际上挂载的是这里:   {os.path.join(os.getcwd(), 'judge', 'judge_run_data')}")

if str(settings.JUDGE_HOST_DIR) != str(os.path.join(os.getcwd(), 'judge', 'judge_run_data')):
    print("❌ 路径不匹配！请修改 settings.py")
else:
    print("✅ 路径匹配！")