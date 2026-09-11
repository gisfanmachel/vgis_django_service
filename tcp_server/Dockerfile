# 建立 python3.10 环境
FROM python:3.10

# 镜像作者
MAINTAINER CHENXW

# 设置 python 环境变量
ENV PYTHONUNBUFFERED 1

# 设置pip源为国内源
COPY pip.conf ~/.pip/pip.conf

# 在容器内创建服务目录
RUN mkdir -p /var/backend/tcp_server

# 设置容器内工作目录
WORKDIR /var/backend/tcp_server

# 将当前目录文件加入到容器工作目录中
ADD . /var/backend/tcp_server

# pip安装依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host mirrors.aliyun.com --default-timeout=60 --no-cache-dir -r requirements.txt

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 启动（配置通过环境变量注入：TCP_SERVER_PORT / DB_HOST / DB_PASSWORD / WEB_API_ENABLED ...）
CMD python3 main.py
