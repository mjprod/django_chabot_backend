from .base import *  # noqa: F403


DEBUG = True
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "api-staging.mjproapps.com",
    "staging.mjproapps.com",
    "13.236.102.255",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
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