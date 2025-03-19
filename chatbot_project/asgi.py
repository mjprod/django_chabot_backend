"""
ASGI config for chatbot_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

load_dotenv()

environment = os.getenv("DJANGO_ENV", "dev")

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"chatbot_project.settings.{environment}")

application = get_asgi_application()
