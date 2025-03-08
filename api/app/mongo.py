import logging
import threading
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """
    Singleton class to manage MongoDB connections efficiently.
    """
    _client = None
    _db = None
    _lock = threading.Lock()  # add lock

    @classmethod
    def get_db(cls):
        """Get a single instance of the MongoDB connection."""
        if cls._client is None:
            with cls._lock:  
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
        with cls._lock:
            if cls._client:
                cls._client.close()
                logger.info("MongoDB connection closed.")
                cls._client = None
                cls._db = None

    @classmethod
    def query_collection(cls, collection_name, query=None, projection=None, limit=0):
        db = cls.get_db()
        collection = db[collection_name]

        try:
            results = collection.find(query or {}, projection).limit(limit)
            return list(results)
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {str(e)}", exc_info=True)
            return []
    
    @classmethod 
    def aggregate_collection(cls, collection_name, aggregation):
        db = cls.get_db()
        collection = db[collection_name]
        try:
            return collection.aggregate(aggregation)
        except Exception as e:
            logger.error(f"Error aggregating collection '{collection_name}': {str(e)}", exc_info=True)
