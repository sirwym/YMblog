import os
import shutil
import uuid
import tempfile
from pathlib import Path
import zipfile
from django.conf import settings

class FileManager:
    BASE_DIR = Path(settings.JUDGE_HOST_DIR)

    @classmethod
    def create_run_dir(cls) -> str:
        """返回 uuid 字符串，而不是路径对象，方便后续拼接"""
        run_id = uuid.uuid4().hex
        host_path = cls.BASE_DIR / run_id
        host_path.mkdir(parents=True, exist_ok=True)
        return run_id  # 只返回 ID

    @classmethod
    def get_host_path(cls, run_id: str) -> Path:
        """获取 Django 视角的路径 (用于写文件)"""
        return cls.BASE_DIR / run_id

    @classmethod
    def get_container_path(cls, run_id: str) -> str:
        """获取 Docker 视角的路径 (用于传给 API)"""
        return f"{settings.JUDGE_CONTAINER_DIR}/{run_id}"

    @classmethod
    def write_file(cls, run_id: str, filename: str, content: str):
        """写入代码文件"""
        path = cls.get_host_path(run_id) / filename
        if not content: return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    @classmethod
    def remove_run_dir(cls, run_id: str):
        """清理目录"""
        path = cls.get_host_path(run_id)
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    @classmethod
    def read_head(cls, file_path: str, length: int = 1000) -> str:
        """读取文件前 N 个字符用于预览"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(length)
        except Exception:
            return "Preview unavailable"

    @classmethod
    def pack_run_data(cls, run_id: str, zip_name: str = "data.zip") -> str:
        """
        将 run_id 目录下的所有相关文件 (.in, .out, .py, .cpp) 打包成 zip
        返回 zip 文件的绝对路径
        """
        dir_path = cls.get_host_path(run_id)
        zip_file_path = dir_path / zip_name

        # 使用 zipfile 库进行压缩
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 遍历目录
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    # 排除掉 zip 文件本身，防止递归死循环
                    if file == zip_name:
                        continue

                    # 排除掉可能存在的临时文件或系统文件 (.DS_Store 等)
                    if file.startswith('.'):
                        continue

                    # 构造文件的绝对路径
                    abs_path = os.path.join(root, file)
                    # 构造 zip 包内的相对路径 (不包含 run_id 这一层文件夹，直接展开就是文件)
                    rel_path = os.path.relpath(abs_path, dir_path)

                    zf.write(abs_path, rel_path)

        return str(zip_file_path)