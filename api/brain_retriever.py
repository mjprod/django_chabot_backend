import os
import time
import gc
import logging

from typing import List

from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

class MultiRetriever:
    def __init__(self, vectorstores: List[Chroma]):
        self.vectorstores = vectorstores

    def get_relevant_documents(self, query: str):
        all_results = []
        try:
            for store in self.vectorstores:
                logger.info(f"Retrieving from collection: {store._collection}")
                retriever = store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
)
                results = retriever.invoke(query)
                all_results.extend(results)
                
            return all_results[:3]
        finally:
            gc.collect()

    def invoke(self, query: str):
        return self.get_relevant_documents(query)