# 使用 Python 作为基础镜像
FROM python:3.9.19

# 指定维护者信息
LABEL maintainer='quill'

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
	PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
	PROJECT_PATH=/usr/local/share/helloBlog

# 设置工作目录
WORKDIR ${PROJECT_PATH}

# 更换 Debian APT 源为阿里云镜像
RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 安装基本工具和依赖，并清理缓存
RUN apt-get update -y && \
    #apt-get install -y --no-install-recommends gcc && \
    apt-get install -y --no-install-recommends nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 pipenv
#RUN pip install --no-cache-dir --default-timeout=100 -i https://mirrors.aliyun.com/pypi/simple/ pipenv
RUN pip install --no-cache-dir --default-timeout=100  pipenv

# 复制项目文件到容器
COPY . ${PROJECT_PATH}

# 复制配置文件
COPY backend/conf/uwsgi.ini.docker ${PROJECT_PATH}/backend/conf/uwsgi.ini
COPY backend/conf/supervisor/supervisord.conf /etc/
COPY backend/conf/supervisor/supervisord.d/myapp.ini /etc/supervisord.d/myapp.ini

# 根据 Pipfile 和 Pipfile.lock，安装虚拟环境依赖
RUN cd ${PROJECT_PATH}/backend && \
	pipenv --rm || true && \
	# `pipenv` 命令指定国内镜像源
	#pipenv install --deploy --ignore-pipfile --verbose --pypi-mirror https://mirrors.aliyun.com/pypi/simple/ && \
	pipenv install --deploy --ignore-pipfile --verbose --pypi-mirror ${PIP_INDEX_URL} && \
	#VENV_PATH=$(pipenv --venv) && \
	#echo "pythonhome=${VENV_PATH}" >> ${PROJECT_PATH}/backend/conf/uwsgi.ini && \
	# 创建必要的日志目录
	mkdir -p /var/log/supervisor && \
	mkdir -p ${PROJECT_PATH}/backend/logs/uwsgi

# 暴露 uWSGI 默认端口
EXPOSE 8000

# 复制 init.sh 到容器并设置可执行权限
COPY init.sh ${PROJECT_PATH}/init.sh
RUN chmod +x ${PROJECT_PATH}/init.sh

# 在容器启动时执行初始化操作
CMD ["sh", "-c", "${PROJECT_PATH}/init.sh"]
