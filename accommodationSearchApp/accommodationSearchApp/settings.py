import os
from pathlib import Path

import cloudinary
import cloudinary.uploader
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000', 'http://0.0.0.0:8000', 'http://100.85.57.9:8000', 'https://8183-103-199-70-79.ngrok-free.app', 'https://8183-103-199-70-79.ngrok-free.app:8001']
DJANGO_ALLOW_ASYNC_UNSAFE = True
REST_USE_JWT = True
# Configuration
cloudinary.config(
    cloud_name="devtqlbho",
    api_key="654785974366212",
    api_secret="yBPftN_K0QlSh0mAUyCZ-ewTxUY",
    secure=True
)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-83fly(by7c4z()nq*&ris453kd*f3+1#o8n_e50=k=ei7u+7&&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'accommodationSearch.apps.AccommodationsearchConfig',
    'ckeditor',
    'ckeditor_uploader',
    'cloudinary',
    'rest_framework',
    'drf_yasg',
    'oauth2_provider',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'rest_framework.authtoken',
    'channels',
]

ASGI_APPLICATION = 'accommodationSearchApp.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
AUTOSLUG_SLUGIFY_FUNCTION = 'autoslug.utils.slugify'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10
}

CKEDITOR_UPLOAD_PATH = "ckeditors/images/"

AUTH_USER_MODEL = 'accommodationSearch.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'accommodationSearchApp.urls'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Site ID
SITE_ID = 1

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True

# Google OAuth2 settings
GOOGLE_CLIENT_ID = "284762867837-e5gja6b1cp8kdt5pnss5jj8ok87lbt2l.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

# Social Account settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}


SOCIALACCOUNT_LOGIN_IN_GET = True
# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/accounts/logout/'
LOGOUT_REDIRECT_URL = '/'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'accommodationSearchApp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'rentalmanagementdb',
        'USER': 'root',
        'PASSWORD': 'Admin@123',
        'HOST': ''
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

pymysql.install_as_MySQLdb()

OAUTH2_PROVIDER = {'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'}

ROOT_URLCONF = "accommodationSearchApp.urls"

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = '%s/accommodationSearch/static/' % BASE_DIR
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': True,
    'JSON_EDITOR': True,
    'SECURITY': [
        {
            'Bearer': []
        }
    ],
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# FindAccommodationApp
CLIENT_ID = "5ZSVyx7Z9CzRooRyodvOxyMnL5gVHt16UqBiwh7y"
CLIENT_SECRET = "vxFust8TqAfft0AOPzK5R9Igc2WVpysm18wKX6AWgJidk5o9Eii2cmdhEvaeglbOBeAStBrI0RCl1YhM3QstIrmYrCsh189IIr79B0595eA3PJYWMWUnNpmdDKmuuHUa"

# duy
CLIENT_ID = "oAphbHhnaltzHuQooLxJoP72djbSeFaJOooGQamK"
CLIENT_SECRET = "WPSFJMMPz6YjFBUhyyxzZHftjH3PH0XgmxPN8AaP7DUPSQFSA2X6GbbFDBb4OFyZMaimvHCZYSk9PB4qeQysLb3LLSO0KIsKhOhX9EGR0r1QqjfVlFovWrJ7iOOy6uk6"

# Base URL for the application
BASE_URL = 'https://8183-103-199-70-79.ngrok-free.app'  # URL ngrok cố định
# BASE_URL = 'http://100.85.57.9:8000'  # URL ngrok cố định

# VNPay settings
VNPAY_TMN_CODE = 'X381HOFV'  # Terminal ID / Mã Website
VNPAY_HASH_SECRET = 'PKRAT3EZUB2AXAW8A1V62R9FE837B0EY'  # Secret Key
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'  # URL thanh toán môi trường TEST
VNPAY_RETURN_URL = f'{BASE_URL}/vnpay/return/'  # URL nhận kết quả thanh toán

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://sandbox.vnpayment.vn",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://100.85.57.9:8000",
    "https://8183-103-199-70-79.ngrok-free.app",
    "https://8183-103-199-70-79.ngrok-free.app:8001",  # Thêm URL ngrok mới cho WebSocket
]


# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nhatduy096@gmail.com'
EMAIL_HOST_PASSWORD = 'duynhat8877941z.'  # Mật khẩu ứng dụng từ Google
DEFAULT_FROM_EMAIL = 'nhatduy096@gmail.com'

# SendGrid Email Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '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')
SENDER_EMAIL = 'nhatduy096@gmail.com'
SENDER_NAME = 'System Accommodation'
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_SANDBOX_MODE_IN_DEBUG = False  # Set to False in production

# Frontend URL
FRONTEND_URL = 'https://8ef6-14-224-156-58.ngrok-free.app/'  # Thay đổi trong production

# Autoslug settings
AUTOSLUG_SLUGIFY_FUNCTION = 'autoslug.utils.slugify'

# Cập nhật CSRF settings
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
    'http://100.85.57.9:8000',
    'https://8183-103-199-70-79.ngrok-free.app',
    'https://8183-103-199-70-79.ngrok-free.app:8001',  # Thêm URL ngrok mới cho WebSocket
]
