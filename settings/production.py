from .base import *  # noqa: F403
import os

DEBUG = False
ALLOWED_HOSTS = ["api.mjproapps.com", "www.mjproapps.com", "13.238.144.45"]

# CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "https://api.mjproapps.com",
    "https://mjproapps.com",
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
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("POSTGRE_DATABASE_NAME"),
        'USER': os.getenv("POSTGRE_DATABASE_USER"),
        'PASSWORD': os.getenv("POSTGRE_DATABASE_PASSWORD"),
        'HOST': os.getenv("POSTGRE_DATABASE_HOST"), 
        'PORT': os.getenv("POSTGRE_DATABASE_PORT"),
    }
}