from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = [
    "praxiscrm-bpczdufkc2f3afah.brazilsouth-01.azurewebsites.net",
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
