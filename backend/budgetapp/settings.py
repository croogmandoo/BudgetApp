"""Django settings for BudgetApp.

IMPORTANT: Any change in this file that touches auth, session cookies, CSP,
password hashing, TLS, or attachment handling MUST be cross-checked against
SPEC.md §7 (Security) before it lands. Security is a pillar, not an afterthought.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import dj_database_url
import environ

# ---------------------------------------------------------------------------
# Paths / environment
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# Load a local .env if present. In containers, env vars come from Compose.
environ.Env.read_env(BASE_DIR / ".env")

DEBUG: bool = env.bool("DJANGO_DEBUG", default=False)

# SECRET_KEY must be provided in production. In DEBUG, we generate a random
# ephemeral key so tests and local runs work without requiring env setup;
# sessions will not survive process restarts, which is fine for dev.
SECRET_KEY: str = env.str("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        import secrets as _secrets

        SECRET_KEY = _secrets.token_urlsafe(50)
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY is required when DJANGO_DEBUG is False. "
            "Generate one with `python -c 'import secrets; print(secrets.token_urlsafe(64))'`."
        )

ALLOWED_HOSTS: list[str] = [
    h.strip() for h in env.str("ALLOWED_HOSTS", default="").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS: list[str] = [
    o.strip() for o in env.str("CSRF_TRUSTED_ORIGINS", default="").split(",") if o.strip()
]

FRONTEND_URL: str = env.str("FRONTEND_URL", default="http://localhost:5173")

# Envelope-encryption master key. See SPEC §7.2. Required outside DEBUG.
APP_MASTER_KEY: str = env.str("APP_MASTER_KEY", default="")
if not APP_MASTER_KEY and not DEBUG:
    raise RuntimeError(
        "APP_MASTER_KEY is required outside DEBUG. It wraps per-row / per-file "
        "DEKs used for sensitive columns and attachments (SPEC §7.2)."
    )

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.finances",
    "apps.budgets",
    "apps.bills",
    "apps.projects",
    "apps.maintenance",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
# Order matters. Security first, then sessions/auth, then OTP gate, then CORS.
# CSP: we intend to emit a strict Content-Security-Policy header via a
# dedicated middleware (TBD: django-csp or an in-house shim). The policy must:
#   - default-src 'self'
#   - script-src 'self'       (no 'unsafe-inline' / 'unsafe-eval')
#   - style-src  'self'
#   - frame-ancestors 'none'
#   - object-src 'none'
# That middleware is not wired in yet; see SPEC §7.4.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # TODO: add CSP middleware once django-csp (or equivalent) is vetted.
]

ROOT_URLCONF = "budgetapp.urls"

TEMPLATES: list[dict[str, Any]] = [
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
            ],
        },
    },
]

WSGI_APPLICATION = "budgetapp.wsgi.application"
ASGI_APPLICATION = "budgetapp.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL: str = env.str("DATABASE_URL", default="")
if not DATABASE_URL:
    if DEBUG:
        # SQLite fallback is acceptable for the bootstrap phase only.
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
    else:
        raise RuntimeError("DATABASE_URL is required outside DEBUG.")
else:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        ),
    }

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

# Argon2 first. We deliberately do NOT include PBKDF2 as a fallback for new
# installs: SPEC §7.1 mandates Argon2id, and carrying a weaker hasher in the
# list only helps if we migrate an existing password database. See
# https://docs.djangoproject.com/en/5.1/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/api/v1/auth/login/"

# ---------------------------------------------------------------------------
# DRF + OpenAPI
# ---------------------------------------------------------------------------

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        # TODO: add a custom scoped-PAT authentication class once
        # apps.accounts.APIToken lands.
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "600/min",
    },
}

SPECTACULAR_SETTINGS: dict[str, Any] = {
    "TITLE": "BudgetApp API",
    "DESCRIPTION": (
        "Self-hostable household finance + home-management API. "
        "See SPEC.md for the product contract and security posture."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {"url": "/", "description": "Current host"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS: list[str] = [FRONTEND_URL] if FRONTEND_URL else []
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Session / cookie security (SPEC §7.1)
# ---------------------------------------------------------------------------

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days absolute
# Idle timeout is enforced by middleware (TBD) — Django has no built-in idle expiry.

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-ca"
TIME_ZONE = env.str("DJANGO_TIMEZONE", default="America/Toronto")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Attachments land in MEDIA_ROOT but are envelope-encrypted at rest before
# they get there (SPEC §7.2). Never serve MEDIA_ROOT directly.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Celery (SPEC §9: background jobs via Celery + Redis)
# ---------------------------------------------------------------------------

REDIS_URL: str = env.str("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TIME_LIMIT = 60 * 10
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 9
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Plain formatter in DEBUG, JSON in production so we can ship to Loki/ELK
# without re-parsing the line.

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
        "json": {
            "()": "logging.Formatter",
            "format": (
                '{"ts":"%(asctime)s","level":"%(levelname)s",'
                '"logger":"%(name)s","msg":"%(message)s"}'
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain" if DEBUG else "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Attachments (SPEC §7.4)
# ---------------------------------------------------------------------------
# Hard cap to blunt upload-based DoS; tune via env once the UI is real.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MiB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
ATTACHMENT_MAX_BYTES = env.int("ATTACHMENT_MAX_BYTES", default=25 * 1024 * 1024)
