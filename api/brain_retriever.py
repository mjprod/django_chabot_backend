import gc
import logging

from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

class MultiRetriever:
    def __init__(self, store: Chroma):
        self.store = store

    def get_relevant_documents(self, query: str):
        all_results = []
        try:

            logger.info(f"Retrieving from collection: {self.store._collection}")
            retriever = self.store.as_retriever(
                search_type="similarity", search_kwargs={"k": 5}
            )
            results = retriever.invoke(query)
            all_results.extend(results)

            return all_results[:3]
        finally:
            gc.collect()

    def invoke(self, query: str):
        return self.get_relevant_documents(query)
