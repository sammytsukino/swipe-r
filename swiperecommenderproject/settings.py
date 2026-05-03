import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-change-this-key-before-production",
)
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INSTALLED_APPS = [
    "swiperecommenderapp.apps.SwiperecommenderappConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "swiperecommenderproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "swiperecommenderapp.context_processors.app_shell",
            ],
        },
    },
]

WSGI_APPLICATION = "swiperecommenderproject.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es-es"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": env("CACHE_LOCATION", default="swiperecommender-cache"),
    }
}

API_TIMEOUT_SECONDS = env.int("API_TIMEOUT_SECONDS", default=10)
API_RETRY_ATTEMPTS = env.int("API_RETRY_ATTEMPTS", default=2)
API_RETRY_BACKOFF_SECONDS = env.float("API_RETRY_BACKOFF_SECONDS", default=0.4)
API_RATE_LIMIT_SLEEP_SECONDS = env.float("API_RATE_LIMIT_SLEEP_SECONDS", default=1.0)
API_CACHE_TTL_SECONDS = env.int("API_CACHE_TTL_SECONDS", default=600)

TMDB_API_KEY = env("TMDB_API_KEY", default="")
TMDB_READ_ACCESS_TOKEN = env("TMDB_READ_ACCESS_TOKEN", default="")
TMDB_BASE_URL = env("TMDB_BASE_URL", default="https://api.themoviedb.org/3")

TVDB_API_KEY = env("TVDB_API_KEY", default="")
TVDB_PIN = env("TVDB_PIN", default="")
TVDB_BASE_URL = env("TVDB_BASE_URL", default="https://api4.thetvdb.com/v4")

RPDB_API_KEY = env("RPDB_API_KEY", default="")
RPDB_BASE_URL = env("RPDB_BASE_URL", default="https://api.ratingposterdb.com")
