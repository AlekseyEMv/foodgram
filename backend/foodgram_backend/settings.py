import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', get_random_secret_key())

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Константа, определяет адреса разрешённых доменов поумолчанию.
DEFAULT_ALLOWED_HOSTS = 'localhost;127.0.0.1'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(';')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'django_filters',
    'api.apps.ApiConfig',
    'recipes.apps.RecipesConfig',
    'users.apps.UsersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram_backend.urls'

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

WSGI_APPLICATION = 'foodgram_backend.wsgi.application'

# IS_POSTGRESQL_ENGINE = os.getenv('IS_POSTGRESQL', 'False').lower() == 'false'
IS_POSTGRESQL_ENGINE = os.getenv('IS_POSTGRESQL', 'True').lower() == 'true'

if not IS_POSTGRESQL_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'django'),
            'USER': os.getenv('POSTGRES_USER', 'django'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

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

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# Константы, определяют количество отображаемых рецептов на странице.
PAGINATION_SIZE = 6
MAX_PAGINATION_SIZE = 100


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': PAGINATION_SIZE,
    'PAGINATE_BY_PARAM': 'limit',
    'MAX_PAGE_SIZE': MAX_PAGINATION_SIZE,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '10000/day',
        'anon': '1000/day',
        'burst': '10/minute',
    }
}

DJOSER = {
    'HIDE_USERS': False,
    'LOGIN_FIELD': 'email',
    'PERMISSIONS': {
        'user': ['rest_framework.permissions.IsAuthenticated'],
        'user_list': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
        'user_create': ['rest_framework.permissions.AllowAny'],
        'set_password': ['djoser.permissions.CurrentUserOrAdmin'],
    },
    'SERIALIZERS': {
        'user_create': 'users.serializers.CustomUserCreateSerializer',
        'user': 'users.serializers.CustomUserSerializer',
    },
}

# Строка для пустых ячеек админ-панели
ADMIN_EMPTY_VALUE = 'Не задано'

# Максимальная длина строки в админ-панеле.
ADMIN_MAX_LENGTH = 32

# Максимальная длина email-адреса.
EMAIL_MAX_LENGTH = 254

# Максимальная длина названия ингридиента.
INGREDIENT_MAX_LENGTH = 128

# Максимальная длина названия единицы измерения ингридиента.
UNIT_MAX_LENGTH = 64

# Минимальное количество ингридиентов в рецепте.
INGRIGIENTS_MIN_VALUE = 1

# Минимальное время приготовления (в минутах)
MIN_COOKING_TIME = 1

# Максимальная длина названия тега.
TAG_MAX_LENGTH = 32

# Крайние размеры названия рецепта.
RECIPE_MIN_LENGTH = 2
RECIPE_MAX_LENGTH = 256

# Максимальная длина ника пользователя.
USERNAME_MAX_LENGTH = 150

# Шаблон ника пользователя.
USERNAME_REGEX = r'^[\w.@+-]+$'

# Список запрещенных ников пользователей.
FORBIDDEN_USERNAMES = ['me',]

# Минимальная длина пароля.
MIN_PASSWORD_LEN = 8

# Максимальная размер аватара.
AVATAR_MAX_LENGTH = 1024 ** 2

# Дефолтное значение для полей моделей.
DEFAULT_VALUE = 'Не указано'
