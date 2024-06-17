# 建立 python3.9 环境
FROM python:3.9
    
# 镜像作者
MAINTAINER CHENXW
    
# 设置 python 环境变量
ENV PYTHONUNBUFFERED 1
    
# 设置pip源为国内源
COPY pip.conf ~/.pip/pip.conf

# 拷贝字体文件
COPY simfang.ttf /usr/share/fonts/chinese/simfang.ttf
    
# 在容器内创建zxdservice文件夹
RUN mkdir -p /var/www/html/myservice
    
# 设置容器内工作目录
WORKDIR /var/www/html/myservice
    
# 将当前目录文件加入到容器工作目录中（. 表示当前宿主机目录）
ADD . /var/www/html/myservice
    
# pip安装依赖
#RUN pip install -r requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host mirrors.aliyun.com --default-timeout=60 --no-cache-dir -r requirements.txt


