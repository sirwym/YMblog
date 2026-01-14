# Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    gcc g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. 安装 AI 出题需要的库 (直接装在容器全局环境)
RUN pip3 install --no-cache-dir cyaron numpy

# 3. 准备 Go-Judge
WORKDIR /opt/go-judge
COPY mac_docker/go-judge_1.11.3_linux_arm64 /opt/go-judge/go-judge

RUN chmod +x go-judge

# 4. 准备静态资源 (Driver/Templates)

COPY assets /opt/assets

# 5. 准备挂载配置 (用于基础环境)
COPY mac_docker/mount.yaml /opt/go-judge/mount.yaml

EXPOSE 5050

# 6. 启动命令
CMD ["/opt/go-judge/go-judge", \
     "-http-addr", "0.0.0.0:5050", \
     "-mount-conf", "/opt/go-judge/mount.yaml", \
     "-tmp-fs-param", "size=128m,nr_inodes=4k", \
     "-release", \
     "-src-prefix", "/"]