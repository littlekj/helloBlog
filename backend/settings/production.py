"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 4.2.14.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-!txzg@7*-((*x+8@k@#z#++@*i19k-_$5@v&g^z%4t9cg_ub!b'

import os
from .common import *
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取配置
SECRET_KEY = os.getenv('SECRET_KEY')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')

if not SECRET_KEY or not DB_USER or not DB_PASS:
    raise ValueError('Missing one or more required environment variables.')

# HSTS 确保浏览器只通过 HTTPS 连接到项目网站
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL 重定向，自动将所有 HTTP 请求重定向到 HTTPS
SECURE_SSL_REDIRECT = True

# 防止浏览器对相应内容类型嗅探
SECURE_CONTENT_TYPE_NOSNIFF = True

# 启用浏览器 XXS 过滤器
SECURE_BROWSER_XSS_FILTER = True

# 启用安全 Cookie 确保仅通过 HTTPS 传输
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 点击劫持保护
X_FRAME_OPTIONS = 'DENY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
    'comment',
    'haystack',
]

# Haystack 配置
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        # 'ENGINE': 'blog.search_backends.CustomElasticsearch7SearchEngine',
        'URL': 'http://101.34.211.137:9200/',  # Elasticsearch 地址
        # 'INDEX_NAME': 'haystack',  # Elasticsearch 索引名称
        'INDEX_NAME': 'blog_index',
        'KWARGS': {
            'http_auth': ('elastic', 'elastic'),  # Elasticsearch 实际设置的用户名和密码
            # 'timeout': 30,  # 将超时时间设置为 30 秒
            # 'use_ssl': True,
            # 'verify_certs': False,
            # 'ca_certs': '/path/to/ca.crt',
        },
        'INCLUDE_SPELLING': True,  # 是否开启拼写检查
        'DEFAULT_OPERATOR': 'AND',  # 默认的查询操作符，用于处理多个关键词的搜索
    },
}

# 可选的配置项
# 设置实时信号处理器，以便在模型保存时自动更新索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# 指定自定义高亮显示器，用于搜索结果中的高亮显示
HAYSTACK_CUSTOM_HIGHLIGHTER = 'blog.utils.CustomHighlighter'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blog.middleware.StoreLastURLMiddleware',  # 自定义中间件
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'database', 'db.sqlite3'),
    # }

    'default': {
        # 数据库引擎配置
        'ENGINE': 'django.db.backends.mysql',
        # 数据库的名称
        'NAME': 'blog',
        # 数据库服务器的 IP 地址(如果是本机，可以配置成 localhost 或 127.0.0.1)
        'HOST': '101.34.211.137',
        # 启动 MySQL 服务的端口号
        'PORT': 3306,
        # 数据库用户名和口令
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 数据库使用的字符集
        'CHARSET': 'utf8mb4',
        # 数据库时间日期的时区设定
        'TIME_ZONE': 'Asia/Chongqing',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# LANGUAGE_CODE = 'en-us'
#
# TIME_ZONE = 'UTC'

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Chongqing'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
# 指定在生产环境中收集所有静态文件的目录。
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

