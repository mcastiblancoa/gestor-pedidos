import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-secret-key')
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'

def _parse_allowed_hosts(val: str):
    return [h.strip() for h in val.split(',') if h.strip()]

ALLOWED_HOSTS = _parse_allowed_hosts(os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1'))

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'inventory_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

WSGI_APPLICATION = 'inventory_manager.wsgi.application'
ASGI_APPLICATION = 'inventory_manager.asgi.application'

# Django's DB not used for orders; keep minimal sqlite for framework needs
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = str(BASE_DIR / 'staticfiles')

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Gestor de Pedidos - API',
    'DESCRIPTION': 'API REST para gestionar pedidos de inventario.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# MongoDB settings via env
MONGO = {
    'HOST': os.environ.get('DB_HOST', 'localhost'),
    'PORT': int(os.environ.get('DB_PORT', '27017')),
    'USER': os.environ.get('DB_USER', ''),
    'PASS': os.environ.get('DB_PASS', ''),
    'NAME': os.environ.get('DB_NAME', 'inventory_db'),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
