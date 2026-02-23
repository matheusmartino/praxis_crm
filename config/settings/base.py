import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-production",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # apps locais
    "apps.core",
    "apps.accounts",
    "apps.crm",
    "apps.sales",
    "apps.gestao",
    "apps.prospeccao",
    "apps.carteira_ativa",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Praxis — injeta perfil no request e valida isolamento de acesso
    'apps.core.middleware.tenant_isolation.TenantIsolationMiddleware',
    # Praxis — captura exceções não tratadas com contexto completo
    'apps.core.middleware.global_exception.GlobalExceptionMiddleware',
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.prospeccao.context_processors.followups_pendentes",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# LOGGING — Configuração profissional em arquivo
# =============================================================================

# Garante que o diretório de logs exista na inicialização
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    # --- Formatters -----------------------------------------------------------
    "formatters": {
        # Formato detalhado para arquivos de log
        "verbose": {
            "format": (
                "[{asctime}] {levelname} {name} {module} "
                "({pathname}:{lineno}) — {message}"
            ),
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        # Formato compacto para console de desenvolvimento
        "simple": {
            "format": "[{asctime}] {levelname} {name} — {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
        # ---------------------------------------------------------------
        # FUTURO: JSON logging estruturado para integração com ELK/Datadog
        # Ativar quando necessário substituindo o formatter dos handlers.
        # ---------------------------------------------------------------
        # "json": {
        #     "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        #     "format": "%(asctime)s %(levelname)s %(name)s %(module)s "
        #               "%(pathname)s %(lineno)d %(message)s",
        # },
    },

    # --- Filters --------------------------------------------------------------
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        # ---------------------------------------------------------------
        # FUTURO: Filter para injetar request_id em cada registro de log.
        # Ativar junto com RequestIDMiddleware para correlação ponta-a-ponta.
        # ---------------------------------------------------------------
        # "request_id": {
        #     "()": "apps.core.middleware.request_id.RequestIdFilter",
        # },
    },

    # --- Handlers -------------------------------------------------------------
    "handlers": {
        # Console: apenas em desenvolvimento (DEBUG=True)
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # Arquivo de erros: ERROR e CRITICAL com rotação automática
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "errors.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # Arquivo de aplicação: INFO e WARNING com rotação automática
        "app_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # ---------------------------------------------------------------
        # FUTURO: Handler para Sentry (quando configurado)
        # ---------------------------------------------------------------
        # "sentry": {
        #     "level": "ERROR",
        #     "class": "sentry_sdk.integrations.logging.EventHandler",
        # },
    },

    # --- Loggers --------------------------------------------------------------
    "loggers": {
        # Logger raiz do Django
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Requisições Django (4xx/5xx)
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        # Logger do projeto Praxis — usado por todos os apps
        "praxis": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Logger específico para auditoria
        "praxis.auditoria": {
            "handlers": ["app_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Logger específico para segurança (acessos negados, tentativas)
        "praxis.seguranca": {
            "handlers": ["app_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"  # Redireciona para dashboard após login
LOGOUT_REDIRECT_URL = "/"  # Redireciona para landing após logout

# Configurações de E-mail
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",  # Console para dev
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Praxis CRM <administrativo@metamixequipamentos.com.br>")
