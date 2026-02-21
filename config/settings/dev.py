from .base import *  # noqa: F401,F403

DEBUG = True

ENVIRONMENT = "DEV"

ALLOWED_HOSTS = [
    "dev.praxisapp.com.br",
    "localhost", 
    "127.0.0.1", 
    "10.0.0.71",
    "187.77.37.217"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
