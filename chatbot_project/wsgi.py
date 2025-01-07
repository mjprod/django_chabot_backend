"""
WSGI config for chatbot_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

# import gc
# import os

from django.core.wsgi import get_wsgi_application

# Set environment variable before application loads
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_project.settings")


# Initialize WSGI application with memory management
def get_managed_application():
    application = get_wsgi_application()
    # gc.collect()  # Force garbage collection after initialization
    return application


application = get_managed_application()


# Add request cleanup middleware
"""
class MemoryCleanupMiddleware:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        try:
            return self.application(environ, start_response)
        finally:
            gc.collect()  # Clean up after each request

"""
# Wrap application with memory cleanup
# application = MemoryCleanupMiddleware(application)
