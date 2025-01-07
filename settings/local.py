from .base import *

DEBUG = True
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# Security
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_PRELOAD = True

# MongoDB settings
MONGODB_USERNAME = "jaredmjpro"
MONGODB_PASSWORD = "JS19931989JR$"
MONGODB_CLUSTER = "staging-cluster.ooyoj.mongodb.net"
MONGODB_DATABASE = "chatbotdb"


# Construct MongoDB URI
MONGODB_URI = (
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
    f"@{MONGODB_CLUSTER}/{MONGODB_DATABASE}?retryWrites=true&w=majority"
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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
