"""
Django settings for blog project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
import djcelery

from celery.schedules import crontab


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'r_+x!+6y%&dub)ez47j@85!4^_!j9%zozy+zy6izf5-z5r0i9c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'blog/render/templates')],
    'APP_DIRS': True,
    'OPTIONS': {
        'debug': True,
        'context_processors': [
            'django.contrib.auth.context_processors.auth'
        ]
    }
}]

ALLOWED_HOSTS = ['127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'blog.account',
    'blog.account.users',
    'blog.account.roles',
    'blog.account.groups',
    'blog.content.albums',
    'blog.content.articles',
    'blog.content.comments',
    'blog.content.marks',
    'blog.content.photos',
    'blog.content.sections',
    'blog.scheduler',
    'blog.wechat',
    'blog.render'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'blog.urls'

WSGI_APPLICATION = 'blog.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blog',
        'USER': 'eternalzzx',
        'PASSWORD': 'qwer4321',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'zh_hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'data').replace('\\', '/')
MEDIA_URL = '/media/'

APPEND_SLASH = False

# Token Key
HEADER_KEY = 'Auth-Token'
TOKEN_COOKIE_KEY = 'BLOG-TOKEN'
TOKEN_URL_KEY = 'ticket'
TOKEN_HEADER_KEY = 'HTTP_%s' % HEADER_KEY.replace('-', '_').upper()

# Redis
REDIS_HOSTS = '127.0.0.1'
REDIS_PASSWORD = 'qwer4321'

# Memcached
MEMCACHED_HOSTS = ['127.0.0.1:11211']

# Celery
djcelery.setup_loader()

REDIS_CONFIG_DB = '1'
REDIS_CONFIG_HOST = '127.0.0.1'
REDIS_CONFIG_PASSWORD = 'qwer4321'
REDIS_CONFIG_PORT = '6379'
REDIS_CONFIG_INFO = 'redis://:%s@%s:%s/%s'%(
    REDIS_CONFIG_PASSWORD,
    REDIS_CONFIG_HOST,
    REDIS_CONFIG_PORT,
    REDIS_CONFIG_DB
)
BROKER_URL = REDIS_CONFIG_INFO
CELERY_RESULT_BACKEND = REDIS_CONFIG_INFO

CELERY_IMPORTS = ('blog.scheduler.tasks', )

CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['application/json', 'json', 'msgpack']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERYBEAT_SCHEDULE = {
    'sync_redis': {
        "task": "sync_redis",
        "schedule": crontab(minute='*/1'),
        "args": (),
        "enabled": True
    },
    'wechat_access_token': {
        "task": "wechat_access_token",
        "schedule": crontab(minute='*/90'),
        "args": (),
        "enabled": True
    }
}

# WeChat
APP_TOKEN = 'myAppToken'
APP_ID = 'myAppId'
APP_SECRET = 'myAppSecret'
