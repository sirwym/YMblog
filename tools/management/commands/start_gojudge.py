import subprocess
import time
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = '启动 go-judge 容器并自动配置环境 (Debian 13 版)'

    # ==========================================
    # 🛠️ 配置区域 (Debian/Ubuntu 包名)
    # ==========================================
    TARGET_PACKAGES = [
        "build-essential",  # C++ 核心 (g++, gcc, make)
        # "python3",  # Python3
        # "python3-pip",  # Pip (可选)

        # --- 其他语言参考 ---
        # "openjdk-17-jdk-headless", # Java
        # "golang",                  # Go
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制删除旧容器并重建 (并重新自动安装环境)'
        )

    def handle(self, *args, **options):
        container_name = "go-judge"
        image_name = "criyle/go-judge:latest"
        port_mapping = "5050:5050"
        shm_size = "256m"

        self.stdout.write(f"正在检查容器状态: {container_name} ...")

        # 1. 检查容器
        check_cmd = ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        exists = result.stdout.strip() == container_name

        # 2. 判断逻辑
        if exists:
            if options['force']:
                self.stdout.write(self.style.WARNING(f"检测到 --force，正在删除旧容器..."))
                subprocess.run(["docker", "rm", "-f", container_name], check=True)
            else:
                self.stdout.write(self.style.SUCCESS(f"容器已存在，正在确保启动..."))
                subprocess.run(["docker", "start", container_name], check=True)
                self.stdout.write(self.style.SUCCESS(f"✅ 容器已就绪! (假设环境已安装)"))
                return

        # 3. 启动新容器
        self.stdout.write(self.style.SUCCESS(f"正在启动纯净容器 (SHM: {shm_size})..."))
        run_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--restart", "always",
            "--privileged",
            "-p", port_mapping,
            f"--shm-size={shm_size}",
            image_name
        ]

        try:
            subprocess.run(run_cmd, check=True)
            self.stdout.write(self.style.SUCCESS(f"容器启动成功! 等待 3 秒准备初始化环境..."))
            time.sleep(3)

            # === 4. 自动执行环境安装 ===
            self.install_environment(container_name)

        except subprocess.CalledProcessError as e:
            raise CommandError(f"操作失败: {e}")

    def install_environment(self, container_name):
        """在 Debian 容器内部执行 apt-get 命令安装环境"""
        packages_str = ", ".join(self.TARGET_PACKAGES)
        self.stdout.write(self.style.WARNING(f"⚡️ 开始自动安装环境 (Debian 13): [{packages_str}]"))
        self.stdout.write("提示: 这一步取决于网速，可能需要 1-3 分钟，请耐心等待...")

        try:
            # # 步骤 1: 换源 (针对 Debian 12/13 的新路径 debian.sources)
            # self.stdout.write("1. [Config] 替换为阿里云源...")
            # # 注意：Debian 13 使用 debian.sources 而不是 sources.list
            # cmd_sed = [
            #     "docker", "exec", container_name,
            #     "sh", "-c",
            #     "sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources"
            # ]
            # # 为了兼容性，如果命令失败(比如是旧版Debian)，我们尝试旧路径，但不报错退出
            # try:
            #     subprocess.run(cmd_sed, check=True)
            # except subprocess.CalledProcessError:
            #     self.stdout.write("   (新路径替换失败，尝试旧路径 sources.list...)")
            #     cmd_sed_old = [
            #         "docker", "exec", container_name,
            #         "sh", "-c",
            #         "sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list"
            #     ]
            #     subprocess.run(cmd_sed_old, check=False)

            # 步骤 2: 更新 apt
            self.stdout.write("2. [Update] 更新软件列表 (apt-get update)...")
            cmd_update = ["docker", "exec", container_name, "apt-get", "update"]
            subprocess.run(cmd_update, check=True)

            # 步骤 3: 安装配置列表中的所有包
            self.stdout.write(f"3. [Install] 正在安装: {packages_str} ...")

            cmd_install = [
                              "docker", "exec",
                              "-e", "DEBIAN_FRONTEND=noninteractive",
                              container_name,
                              "apt-get", "install", "-y"
                          ] + self.TARGET_PACKAGES

            subprocess.run(cmd_install, check=True)

            # 步骤 4: 清理缓存
            self.stdout.write("4. [Clean] 清理缓存...")
            cmd_clean = ["docker", "exec", container_name, "rm", "-rf", "/var/lib/apt/lists/*"]
            subprocess.run(cmd_clean, check=True)

            self.stdout.write(self.style.SUCCESS("\n🎉🎉🎉 环境自动初始化完成！"))
            self.stdout.write(self.style.SUCCESS(f"已安装环境: {packages_str}"))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ 环境安装失败: {e}"))
            self.stdout.write(
                self.style.WARNING("请尝试运行 `python manage.py start_gojudge --force` 重试，或检查服务器网络。"))