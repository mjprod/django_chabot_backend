import logging
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """
    Singleton class to manage MongoDB connections efficiently.
    """

    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        """Get a single instance of the MongoDB connection."""
        if cls._client is None:
            try:
                cls._client = MongoClient(settings.MONGODB_URI)
                cls._db = cls._client[settings.MONGODB_DATABASE]
                logger.info("MongoDB connection established successfully.")
            except Exception as e:
                logger.error(f"MongoDB connection error: {str(e)}", exc_info=True)
                raise
        return cls._db

    @classmethod
    def close_connection(cls):
        """Close the MongoDB connection properly."""
        if cls._client:
            cls._client.close()
            logger.info("MongoDB connection closed.")
            cls._client = None
            cls._db = None
