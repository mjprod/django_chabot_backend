from .base import BASE_DIR,SECRET_KEY,ROOT_URLCONF,INSTALLED_APPS,MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["api-staging.mjproapps.com", "https://staging.mjproapps.com"]
CORS_ALLOWED_ORIGINS = [
    "https://api-staging.mjproapps.com",
    "https://staging.mjproapps.com",
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
MONGODB_USERNAME = "jaredmjpro"
MONGODB_PASSWORD = "JS19931989JR$"
MONGODB_CLUSTER = "staging-cluster.ooyoj.mongodb.net"
MONGODB_DATABASE = "chatbotdb"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY

ROOT_URLCONF=ROOT_URLCONF
INSTALLED_APPS=INSTALLED_APPS
MIDDLEWARE=MIDDLEWARE

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
