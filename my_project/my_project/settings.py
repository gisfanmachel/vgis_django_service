"""
Django settings for my_project project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
LOGGER_ROOT = os.path.join(BASE_DIR, 'logger')
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

APP_NAME = "my_app"
PROJECT_NAME = "my_project"
STATIC_NAME = "my_static"
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&8ue%+g+nyf8oy6ctogjia!q$o_qv@^sr44&px*63_k!=^$192'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_apscheduler',
    'django.contrib.gis',
    # 项目工程
    APP_NAME,
    # rest framework框架
    'rest_framework',
    'rest_framework_gis',
    # 过滤器
    'django_filters',
    # 身份认证
    'rest_framework.authtoken',
    # swagger文档
    'rest_framework_swagger',
    # 跨域
    'corsheaders',
    'channels'
    # 'sslserver',
    # 'werkzeug_debugger_runserver',
    # 'django_extensions'

]
# AUTH_USER_MODEL = "{}.SysUser".format(APP_NAME)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    '{}.middleware.DisableCSRF'.format(APP_NAME),
    '{}.middleware.CORSMiddleware'.format(APP_NAME),
    '{}.middleware.EncryptionMiddleware'.format(APP_NAME)

]

# # SECURITY安全设置 - 支持http时建议开启
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# # SECURE_SSL_REDIRECT = True # 将所有非SSL请求永久重定向到SSL
# SESSION_COOKIE_SECURE = True  # 仅通过https传输cookie
# CSRF_COOKIE_SECURE = True  # 仅通过https传输cookie
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # 严格要求使用https协议传输
# SECURE_HSTS_PRELOAD = True  # HSTS为
# SECURE_HSTS_SECONDS = 60
# SECURE_CONTENT_TYPE_NOSNIFF = True  # 防止浏览器猜测资产的内容类型

# 跨域增加忽略
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = (
#     '*'
# )

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)

CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',
)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    # 身份认证
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        '{}.token.ExpiringTokenAuthentication'.format(PROJECT_NAME)  # 自定义token认证，增加了token失效时间
        # 'rest_framework.authentication.TokenAuthentication',  # token认证
    ),
    # 权限认证
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # IsAuthenticated 仅通过认证的用户
        'rest_framework.permissions.AllowAny',  # AllowAny 允许所有用户
        'rest_framework.permissions.IsAdminUser',  # IsAdminUser 仅管理员用户
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # IsAuthenticatedOrReadOnly 认证的用户可以完全操作，否则只能get读取
    ),
    # 过滤器
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend', 'rest_framework.filters.OrderingFilter'),
    # 分页
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100000,  # 每页数目
    #  swagger文档
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema',

}

ROOT_URLCONF = '{}.urls'.format(PROJECT_NAME)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {  # Adding this section should work around the issue.
                'staticfiles': 'django.templatetags.static',
            },
        },
    },
]

WSGI_APPLICATION = '{}.wsgi.application'.format(PROJECT_NAME)
ASGI_APPLICATION = '{}.asgi.application'.format(PROJECT_NAME)
# 指定日志的目录所在，如果不存在则创建
LOG_ROOT = os.path.join(BASE_DIR, 'log')
if not os.path.exists(LOG_ROOT):
    os.mkdir(LOG_ROOT)

# 日志配置（基本跟原生的TimedRotatingFileHandler一样）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] '
                      '[%(levelname)s]- %(message)s'},
        'simple': {  # 简单格式
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'servers': {
            'class': '{}.log.InterceptTimedRotatingFileHandler'.format(PROJECT_NAME),  # 这个路径看你本地放在哪里(下面的log文件)
            # 路径可以设置在外部，并同步到宿主机
            'filename': os.path.join(LOG_ROOT, 'myapp.log'),
            # 每天自动归档写新的日志文件
            'when': "D",
            'interval': 1,
            'backupCount': 1,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'db': {
            'class': '{}.log.InterceptTimedRotatingFileHandler'.format(PROJECT_NAME),  # 这个路径看你本地放在哪里
            'filename': os.path.join(LOG_ROOT, 'myapp_db.log'),、
            # 每天自动归档写新的日志文件
            'when': "D",
            'interval': 1,
            'backupCount': 1,
            'formatter': 'standard',
            'encoding': 'utf-8',
            'logging_levels': ['info']  # 😒注意这里，这是自定义类多了一个参数，因为我只想让db日志有debug文件，所以我只看sql，这个可以自己设置
        }
    },
    'loggers': {
        # Django全局绑定
        'django': {
            'handlers': ['servers'],
            'propagate': True,
            'level': "INFO"
        },
        'celery': {
            'handlers': ['servers'],
            'propagate': False,
            'level': "INFO"
        },
        'django.db.backends': {
            'handlers': ['db'],
            'propagate': False,
            'level': "DEBUG"
        },
        'django.request': {
            'handlers': ['servers'],
            'propagate': False,
            'level': "DEBUG"
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("192.168.3.191", 6379)],
        },
    },
}

# Redis缓存库配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.3.191:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {"max_connections": 512},
            "IGNORE_EXCEPTIONS": True,
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,  # in seconds
        }
    }
}

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'postgres',
        'PASSWORD': '*******',
        'HOST': '192.168.3.191',
        'PORT': '5432',
        'NAME': 'DZ_AREA'
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

# 设置为中文
LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True
# 不用世界时
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


STATICFILES_DIRS = [os.path.join(BASE_DIR, '{}/{}'.format(APP_NAME, STATIC_NAME))]

# 根据项目名称修改url
STATIC_URL = '/{}/'.format(STATIC_NAME)

# STATIC_ROOT = os.path.join(BASE_DIR, '{}'.format(APP_NAME), '{}'.format(STATIC_NAME))

# 上传文件目录
UPLOAD_ROOT = os.path.join(BASE_DIR, '{}'.format(APP_NAME), '{}'.format(STATIC_NAME), 'upload')

# 是否使用模拟数据
IS_USE_MOCK_DATA = False

# token失效时间，单位秒，开发可自行配置
AUTH_TOKEN_AGE = 60 * 60 * 3

# 项目部署的IP、端口号、网络协议
PROJECT_WEB_PROTOCOL = 'http'
PROJECT_SERVICE_IP = '192.168.3.152'
PROJECT_SERVICE_PORT = '10841'

# 广西服务器
# PROJECT_SERVICE_IP = '117.141.148.176'
# PROJECT_SERVICE_PORT = '14001'

# 是否开启验证码
IS_USE_VERIFICATION_CODE = False

# 是否对请求响应做加解密
IS_ENCRYPTION = False

# 登录失败尝试次数
LOGIN_ERROR_ATTEMPTS = 4

# 账号锁定后的解锁时间，单位秒
LOGIN_LOCKED_TIME = 10 * 60

# Token的key
TOKEN_KEY = 'Authorization'

# 加密相关信息
ENCRPTION = {
    "key1": "uNl-LfGm6NKDQ1Uz9azZIEEzYnaLz68gz0UzaQvYFIY=",
    "key2": "Z0FBQUFBQmsyZWJGZl81NGRMVG9zTVdtQmhTalhfQkhvRVlaVElCMm1ubnZHTXFOb1otNG40ODFlX1JDNk5udmZQaWxrTTI4ODNsVjZyYVZNZDZUZ3NnbS0wMGpEVE1JZFVWS3pkU0pkWVpWcG1ZaTRoeHJDQTd1UXo1Mk5tZ19sdlZUUC1HZ0xiUkNKYWFhcVNuaTFMcTZSam96b3liZmNfMUtKYUxUdldkM3lyVngtYUZleE0zVEZ1cHlkTGdFRVlOQkhlR2dkT191VjJOWXFWSF9YamNuZkE1cURJTlpmWWpUZS1ON2lDZmlNX1MzSzk4eVFEQ2E1MHFTMUpCYjJVRVhrX2pDaEIwcnhVb3lvQ3hqRWF5aTJNVFYwamNtamxyYzFlMXFjaFpDVDBCZkhQdTFma1kwVV93dVNFamlpNUY1ejZIWG1VNEhfMGh0N1hrYXNfcnBobzZ5X1RtVXRiOUtWelZPTFpsNmVxc2xqUHdGYkswPQ==",
    "key3": "Z0FBQUFBQmsyZWJGOWxzeWtGZnVwa0tNdFBQSG1GSkxfRXZPS2lScmtMSHBZM0w4M3FJdXY1N0JHTlRwYjFILXY0akl0NjVvSFA0bkdWdENtTUx6czFab3AwQkpoQ1VNeXJ2QUFTMU9NZ200ZzlVMWZWdTU3eWt0WjhnaElZVzN3WUxZTzFZMkF6czhFN19JWk9zZmRsSDRBdzZuUUVQQW5VbFJpZ1oxVVdlVkVNWEJkSVdGX0VVNEZrRDUtQVFrQm9zalphRkxzLVBGanlnTEhUb0VPaE5YYnBaeDJaUm1laHRUOUxNamIycFMyMDlnYkJ0NTFpZVZxaElkZXlUcEQ5eUJBUTZBVkNkVHI5UktVeFJDMjlXNlhaVWNEZnNlZ09ZWE42Nk52eG9lWnNWOURVRVV4SVFGaGNVM2tuOVBiTHFyQzJOTzNFMUpMendYdWF4ZzBPWnBfc1RXWGxNMnJiNWxsRzQ0Uk12RF85NTR0U2I5SzdQSXc2c1c3N0w2T1cteTNPcWZhdHM0SHlYdXllbkc5ZG04V25TbHdrMC0xRHBXVktQTW1TT3pFMmZsZkNReDczanphYXlxNnpmaE5Db1k0ejBpNVo5N1owM0M4UVNJUWZNUmFSZVctQklaeG5LZE90amNTNHlCU1lzY1B6ZGlfRVczRk05T09udG14OWlSaXZWVnh0dmtwLXJvZUU1MFl4WjBRX0lIaUJhZF9RNTB2a2VYeUtaMmhmY2xTRWtJNFVBX0dHMnNKOGhYRF82bVJDa2Jfck5CeVhIU3BOQW82QmJwZjdXVUhZSEMxSGEwaUk3a0pwS3BoSDRoMDhkblNYVVlyQWV3QWVFSFdIZ1IydE5yeWRwd1ZtR1h6MXJsS28wWWZ6VWtUZzlWZG1nQjE3M1JOQUVvcjg4NThzczZmazg0Tmp6SjNzZXNCanpIek5YRnp0YXZhbFdhWDNYMV9NYXJFMExtZXdYLXhsZ3k2T3g5YlduV1hJRFEzbFVsTDhRYWZ0WFZNTEo3dlFyTHFKREV0ZWxJYnJKN3RRZmt3cE9Bc3F5TlZ3WVg4YTY4VW5MbnZuVkhudllTQ052S3ZwSWx5c2tuX1FuZ1F6ejAyTVZrUG5meTU2c2NSbWs2ZDlDUVA5QXdMLU9Sc3FqVVF6RXB0UG9YNkZSTnRreXZIR05qRW9JQkp4MmU2amw5YlhqZzl2RlFYS0lIck9HU3hHS185em1qLTY1UnV3eDl5SGFyT1lpV1REY3NsMzhEOEh1NFlHMHkwNlpWdWpuTGFVemtTSGFLZmZZWE02ZE1HcGxjRC1nR2NPb0Q3S0FjdXlpNEJjRWlER2h0X1VQR1VuZ0YwNEpzWVZvbmxDaXBSQ0dwSHBYTDBwZ1AycjFSd1pibndFRW41UjNtQzVIczVzYzgyQjdWZ2VlMm5kbnNVN1FqTlVHWHdoRGR2QUVXWGZnZFRRZVlNRk1xZHNGcVVCcEw3RmRsaVUtM29aZHZycV93cXByR291T0dxWnhBVF9VS0FaNjJJb29XOEhpbzBKa2JXbGJBY1Q3VFZGd1BqSGp3LVpaR0p5NGlwZUZfREV0dUNZSG90bnRQU3hPOUxweURyTlB4X3l6VHZRdDFGejREbVQ1QQ==",
    "key4": "b3sVBbMdxJ2pgK/XYPpKVEYdVNk8bUBt9bcpCMegEec3m/nfbvdvVgPlEm1Yd6aavB8jdUR1HF1vf13l/ADVddg6Cl1Yl+vXkDaKeKHa7bHoJpLAWt7i0mIVHSMhPJdQb2qRTbaPCu8MRZNsJWivgnnTSGEHy+vvGhvxCeWcmB0="
}

# 许可文件的路径
WINDOWS_LICENSE_PATH = "E:/license/django_license.lic"
LINUX_LICENSE_PATH = "/home/root/license/django_license.lic"

# 多线程数
MAX_THREAD_COUNT = 16
