import os

from django.core.wsgi import get_wsgi_application

if os.getenv("ENVIRONMENT") == "PROD":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
