import os
from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["api.mjproapps.com", "www.mjproapps.com"]
CORS_ALLOWED_ORIGINS = [
    "https://api.mjproapps.com",
    "https://www.mjproapps.com",
]

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# MongoDB settings
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_CLUSTER = os.getenv("MONGODB_CLUSTER")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ChatbotDB")


# Construct MongoDB URI
MONGODB_URI = (
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
    f"@{MONGODB_CLUSTER}/{MONGODB_DATABASE}?retryWrites=true&w=majority"
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3", # noqa: F405
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "timeout": 20,
        },
    },
    "mongodb": {
        "ENGINE": "djongo",
        "NAME": MONGODB_DATABASE,
        "CLIENT": {
            "host": MONGODB_URI,
            "maxPoolSize": 50,
            "minPoolSize": 10,
            "maxIdleTimeMS": 45000,
        },
    },
}
