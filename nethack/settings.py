from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-change-me')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'web',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]
ROOT_URLCONF = 'nethack.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'web' / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]
WSGI_APPLICATION = 'nethack.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'nethack.sqlite3',
    }
}
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'web' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
SECURE_REFERRER_POLICY = 'same-origin'
