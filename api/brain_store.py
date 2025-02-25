import os
import time
import gc
import logging

from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

# Importar constantes necessários (ajuste o caminho conforme seu projeto)
from ai_config.ai_constants import (
    COHERE_MODEL,
    EMBEDDING_CHUNK_SIZE,
    EMBEDDING_OVERLAP,
    MMR_SEARCH_K,
    MMR_FETCH_K,
    MMR_LAMBDA_MULT,
)

logger = logging.getLogger(__name__)

# Classe para recuperar documentos de múltiplos vector stores
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
                
                # logger.info(f"Collection: {store._collection} → Retrieved {len(results)} results")
                # logger.info(f"Results: {[r.metadata.get('id', 'unknown') for r in results]}")
            return all_results[:3]
        finally:
            gc.collect()

    def invoke(self, query: str):
        return self.get_relevant_documents(query)