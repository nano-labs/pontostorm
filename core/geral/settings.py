# -*- encoding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

"""
Django settings for 'storm default' project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

SITE_URL = ""
EMAIL_FROM = 'Clockwork Storm <ponto@stormsec.com.br>'
DEFAULT_FROM_EMAIL = EMAIL_FROM
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
if EMAIL_USE_TLS:
    EMAIL_HOST_USER = 'ponto@stormsec.com.br'
    EMAIL_HOST_PASSWORD = 'senha_do_email'
    EMAIL_PORT = 587

GRAPPELLI_ADMIN_TITLE = u"Clockwork Storm"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROFILE_LOG_BASE = "/Users/nano/Projetos/pontostorm/core/teste"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'skjdflksjhfo8s7yfp2u3hr0986qt9o84duu1kq[0937845h0d872tqsk870g87b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',

    'geral',
    'utils',
    'ponto',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'geral.urls'

WSGI_APPLICATION = 'geral.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                   # Or path to database file if using sqlite3.
        'USER': '',                   # Not used with sqlite3.
        'PASSWORD': '',               # Not used with sqlite3.
        'HOST': '',                   # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                   # Set to empty string for default. Not used with sqlite3.
    },
    'mysql-inno-init': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                   # Or path to database file if using sqlite3.
        'USER': '',                   # Not used with sqlite3.
        'PASSWORD': '',               # Not used with sqlite3.
        'HOST': '',                   # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                   # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB',
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'pt_BR'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "geral.context_processors.context",
            ),
            'debug': True,
        },
    },
]
# TEMPLATE_CONTEXT_PROCESSORS = (
#     "django.contrib.auth.context_processors.auth",
#     "django.template.context_processors.debug",
#     "django.template.context_processors.i18n",
#     "django.template.context_processors.media",
#     "django.template.context_processors.static",
#     "django.template.context_processors.tz",
#     "django.contrib.messages.context_processors.messages",
#     "geral.context_processors.context",
# )

# EMAIL_FROM = 'Bolao SporTV <bolaosportv@globo.com>'
# EMAIL_HOST = '10.2.207.6'
# EMAIL_PORT = 25
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''

# CACHES = {
#     Usar Memcached caso exista um servidor memcached disponível
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#     },
#     Usar Local Memory Cache caso não haja MemCached disponível
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'OPTIONS': {
#             'MAX_ENTRIES': 1000
#         }
#     },
# }

try:
    from custom_settings import *
except ImportError:
    pass
