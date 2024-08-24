#!/bin/bash

# 设置项目路径
PROJECT_PATH=/usr/local/share/helloBlog/backend

# 切换到项目目录
cd ${PROJECT_PATH}

# 数据库迁移
pipenv run python manage.py migrate

# 收集静态文件 
pipenv run python manage.py collectstatic --noinput

# 启动 Supervisor 服务
pipenv run supervisord -c /etc/supervisord.conf

# 容器保持运行状态
tail -f /dev/null
