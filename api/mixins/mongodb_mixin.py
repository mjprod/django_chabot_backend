import logging
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)


class MongoDBMixin:
    """
    Mixin to handle MongoDB database connections.
    """

    def get_db(self):
        """
        Establish and return a connection to the MongoDB database.
        """
        try:
            if not hasattr(self, "_db"):  # Singleton approach
                client = MongoClient(settings.MONGODB_URI)
                self._db = client[settings.MONGODB_DATABASE]
                logger.info("MongoDB connection established successfully.")
            return self._db
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}", exc_info=True)
            raise

    def close_db(self):
        """
        Close the MongoDB database connection to release resources.
        """
        try:
            if hasattr(self, "_db"):
                self._db.client.close()
                logger.info("MongoDB connection closed.")
                del self._db  # Remove reference to free resources
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
