import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        try:
            from .views import create_feedback_indexes

            create_feedback_indexes()
            logger.info("MongoDB indexes created successfully on startup")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes on startup: {str(e)}")
