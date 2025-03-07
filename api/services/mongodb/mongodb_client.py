import os
import logging
from pymongo import MongoClient
from threading import Lock

logger = logging.getLogger("brain")

from dotenv import load_dotenv

load_dotenv()

class MongoDBClient:
    _instance = None
    _lock = Lock() # prevents race conditions! 

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(MongoDBClient, cls).__new__(cls, *args, **kwargs)
                    cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE")]

    def query(self, collection: str, query: object = None):
        collection = self.db[collection]

        # Handle empty query cases
        if query is None or not bool(query):
            query = {} 
            logger.warning("Empty query received, fetching all documents.")

        results = collection.find(query)
        count = collection.count_documents(query)
        
        return results, count

    def close(self):
        if self.client:
            self.client.close()
            type(self)._instance = None