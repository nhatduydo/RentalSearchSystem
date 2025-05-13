import os
from pathlib import Path

import cloudinary
import cloudinary.uploader
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    'accommodationSearch.apps.AccommodationsearchConfig',
    'ckeditor',
    'ckeditor_uploader',
    'cloudinary',
    'rest_framework',
    'drf_yasg',
    'oauth2_provider',
    'corsheaders',
    'authentication',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'alluth.socialaccount.providers.google',
    # 'accommodationSearch',

]

# AUTH_USER_MODEL = 'authentication.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.contrib.rest_framework.OAuth2Authentication',),
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

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
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

# Django allauth config
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'


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
STATIC_URL = 'static/'

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
BASE_URL = 'https://donhatduy.pythonanywhere.com'  # Update this when ngrok URL changes

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
    BASE_URL,  # Add your ngrok URL to allowed origins
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
# SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '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')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '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')
SENDER_EMAIL = 'nhatduy096@gmail.com'
SENDER_NAME = 'System Accommodation'
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_SANDBOX_MODE_IN_DEBUG = False  # Set to False in production

# Frontend URL
FRONTEND_URL = 'https://8ef6-14-224-156-58.ngrok-free.app/'  # Thay đổi trong production
