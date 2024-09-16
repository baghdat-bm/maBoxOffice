from .settings import *


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-swk#%beks1&cu=zu6q)b0((6g*2@bcjfl$3jyr&^yw$8xia2j5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000",
                        "http://127.0.0.1:8000",
                        'https://kassa.muzaidyny.kz']

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite",
    }
}

CACHE_MIDDLEWARE_SECONDS = 1
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
