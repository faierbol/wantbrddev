"""
Django settings for wantbrd project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import dj_database_url
from decouple import config
from django.contrib.messages import constants as message_constants
MESSAGE_LEVEL = message_constants.DEBUG

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#path to templates direcory
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
#path to static folder
STATIC_DIR = os.path.join(BASE_DIR, 'static')
#path to media/dynamic folder
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3i22t4vm=tnjqp%w@ye^n=zo=z$12=f=)bi_sw0ij9a2mup(o-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '.herokuapp.com', '0.0.0.0', 'localhost', '.wantbrd.com']
CORS_ORIGIN_ALLOW_ALL=True

# Application definition

INSTALLED_APPS = [
    'fluent_comments',  # must be before django_comments
    'crispy_forms',
    'django_comments',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'user',
    'board',
    'phonenumber_field',
    'widget_tweaks',
    'taggit',
    'rest_framework',
    'sorl.thumbnail',
    'storages',
    'threadedcomments',
    'corsheaders',
    'pwa',
    'anymail',
]

# pwa
PWA_APP_NAME = 'Wantbrd'
PWA_APP_DESCRIPTION = "Wantbrd - Taking the guessing out of giving"
PWA_APP_THEME_COLOR = '#F97D1F'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
# PWA_APP_ICONS = [
#     {
#         'src': '/static/images/my_app_icon.png',
#         'sizes': '160x160'
#     }
# ]
# PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

### COMMENTS STUFF

COMMENTS_APP = 'fluent_comments'
FLUENT_COMMENTS_EXCLUDE_FIELDS = ('name', 'email', 'url', 'title')
FLUENT_COMMENTS_USE_EMAIL_NOTIFICATION = True
CRISPY_TEMPLATE_PACK = 'bootstrap3'

### COMMENTS STUFF END

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware'
]

ROOT_URLCONF = 'wantbrd.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR, ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'wantbrd.context_processors.include_login_form',
                'wantbrd.context_processors.unread_notifications',
            ],
        },
    },
]


WSGI_APPLICATION = 'wantbrd.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'wantbrd',
        'USER': 'admin',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = ('wantbrd.backends.CaseInsensitiveModelBackend', )


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# our static files array
STATICFILES_DIRS = [STATIC_DIR, ]

# url definition for static files

# ----------- ENABLE BELOW FOR LOCAL -----------
STATIC_URL = '/static/'
# ----------- ENABLE ABOVE FOR LOCAL -----------

STATIC_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'staticfiles'))

# Media Files definition
MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'wantbrd-assets'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

AWS_LOCATION = 'static'

# ----------- DISABLE BELOW FOR LOCAL -----------
#STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
#SECURE_SSL_REDIRECT = True
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# ----------- DISABLE ABOVE FOR LOCAL-----------

DEFAULT_FILE_STORAGE = 'wantbrd.storage_backends.MediaStorage'  # <-- here is where we reference it


# the login url, needed so django knows where to redirect un-authenicated attempts to @login_required views
LOGIN_URL = 'login'
# where to redirect after login
LOGIN_REDIRECT_URL = '/checkstatus/'
# where to redirect after logout
LOGOUT_REDIRECT_URL = 'home'

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = "hello@wantbrd.com"
SERVER_EMAIL = "hello@wantbrd.com"

ANYMAIL = {
    "MAILGUN_API_KEY": config('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": "mg.wantbrd.com",
}

EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 5871
EMAIL_HOST_USER = 'mailsend@mg.wantbrd.com'
EMAIL_HOST_PASSWORD = config('MAILGUN_SMTP_PASSWORD')
EMAIL_USE_TLS = True

THUMBNAIL_ALIASES = {
    '': {
        'avatar': {'size': (50, 50), 'crop': True},
    },
}

try:
    from .local_settings import *
except ImportError:
    pass