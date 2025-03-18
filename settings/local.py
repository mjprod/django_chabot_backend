from .base import *  # noqa: F403

DEBUG = False

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

# Construct MongoDB URI
MONGODB_URI = (
    f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
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
