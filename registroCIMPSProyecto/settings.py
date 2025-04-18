"""
Django settings for registroCIMPSProyecto project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ACCOUNT_SIGNUP_REDIRECT_URL = '/completeProfile/'
LOGIN_REDIRECT_URL='/dashboard/'

MEDIA_URL='/mainApplication/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mainApplication', 'media')

# SECURE_SSL_REDIRECT = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS=['52.40.72.178','cimps.org','127.0.0.1','localhost']

CSRF_TRUSTED_ORIGINS = ['https://cimps.org','https://register.cimps.org']

# X_FRAME_OPTIONS = 'ALLOWALL'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$lh%1s$b*un7qv5ro=@ngct*#=w(9sdl%4pbz3afptrr=_+qa2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['cimps.org']

STATIC_URL = 'static/'
STATICFILES_DIRS= ['mainApplication/static']

AUTHENTICATION_BACKENDS = [
    
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
    
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'allauth',
    'mainApplication',
    'django_countries',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

SOCIALACCOUNT_PROVIDERS={
    'google': {
        'APP': {
            'client_id': '328935690203-gk0ru5mtqq98veg25d41u9h70374sdv3.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
        },
        'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    },
    'facebook': {
        'APP': {
            'client_id': '2058281721272413',
            'secret': 'fb80c3e5d5a0ef5d03d81b7db5822436',
            'key': ''
        }
    }
}

import os

SITE_ID = 1

ROOT_URLCONF = 'registroCIMPSProyecto.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'mainApplication', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'mainApplication.context_processors.user_context'
            ],
        },
    },
]

WSGI_APPLICATION = 'registroCIMPSProyecto.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'mainAppplication/static/'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#configuraciones adicionales de DJANGO ALLAUTH
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_USE_TLS = True
    EMAIL_PORT = 587
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = 'conferencecimps@cimat.mx'
    EMAIL_HOST_PASSWORD = 'HIPOCRATES@2022'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_USE_TLS = True
    EMAIL_PORT = 587
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = 'conferencecimps@cimat.mx'
    EMAIL_HOST_PASSWORD = 'HIPOCRATES@2022'


############MODELO PERSONALIZADO DE USUARIO################
AUTH_USER_MODEL = 'mainApplication.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'

############### PARA EMAILS DE CONFIRMACION DE CUENTA################
# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Gmail SMTP Server Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465  # Usualmente el puerto para SSL

# Credenciales de la cuenta de correo de Gmail
EMAIL_HOST_USER = 'conferencecimps@cimat.mx'  # Reemplaza con tu correo
EMAIL_HOST_PASSWORD = 'HIPOCRATES@2022'  # Reemplaza con tu contraseña

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Configuración para manejar errores y debug
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False  # Asegúrate de que TLS está desactivado si estás usando SSL

