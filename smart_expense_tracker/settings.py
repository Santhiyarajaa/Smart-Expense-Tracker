"""
Django settings for smart_expense_tracker project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------

SECRET_KEY = 'django-insecure-change-this-secret-key-in-production-2026'

# False for public/Render deployment
DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '10.0.2.2',
    'smart-expense-tracker-2-hxj4.onrender.com',
]

# Allow Django POST/CSRF requests from the Render website
CSRF_TRUSTED_ORIGINS = [
    'https://smart-expense-tracker-2-hxj4.onrender.com',
]


# ----------------------------------------------------------------------
# Application definition
# ----------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    # Local apps
    'expenses',
]


# ----------------------------------------------------------------------
# Middleware
# ----------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ----------------------------------------------------------------------
# URL / WSGI configuration
# ----------------------------------------------------------------------

ROOT_URLCONF = 'smart_expense_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart_expense_tracker.wsgi.application'


# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ----------------------------------------------------------------------
# Password validation
# ----------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ----------------------------------------------------------------------
# Internationalization
# ----------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# ----------------------------------------------------------------------
# Static files
# ----------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ----------------------------------------------------------------------
# Default primary key
# ----------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ----------------------------------------------------------------------
# Authentication redirect settings
# ----------------------------------------------------------------------

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# ----------------------------------------------------------------------
# Currency
# ----------------------------------------------------------------------

CURRENCY_SYMBOL = '₹'


# ----------------------------------------------------------------------
# Django REST Framework
# ----------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# ----------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------

# Suitable for a college/demo project.
# For a production application, restrict this to specific origins.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
