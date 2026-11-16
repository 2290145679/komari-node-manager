FROM python:3.11-slim

LABEL maintainer="Komari Team"
LABEL description="Komari Monitor & Node Manager - Master Service"

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

WORKDIR /opt/komari-pro

# 安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    wget \
    gzip \
    tar \
    procps \
    net-tools \
    iptables \
    ca-certificates \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录结构
RUN mkdir -p /opt/komari-pro/data \
    /opt/komari-pro/node-mgr \
    /opt/komari-pro/admin-spa \
    /opt/komari-pro/user-portal \
    /opt/komari-pro/conf \
    /opt/komari-pro/backups

# 复制项目代码与资源
COPY node-mgr/ /opt/komari-pro/node-mgr/
COPY admin-spa/ /opt/komari-pro/admin-spa/
COPY user-portal/ /opt/komari-pro/user-portal/
COPY conf/ /opt/komari-pro/conf/

# 初始化数据库结构
RUN chmod +x /opt/komari-pro/node-mgr/server.py

EXPOSE 25775

VOLUME ["/opt/komari-pro/data"]

CMD ["python3", "/opt/komari-pro/node-mgr/server.py"]
