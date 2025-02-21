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

# Inicializa o modelo de embedding usando Cohere
embedding_model = CohereEmbeddings(model=COHERE_MODEL)

# Classe para representar documentos customizados
class CustomDocument:
    def __init__(self, page_content: str, metadata: dict, id: str = "0"):
        self.id = id
        self.page_content = page_content
        self.metadata = metadata

    def __str__(self):
        # Mostra o id e os primeiros 100 caracteres do conteúdo
        return f"CustomDocument(id={self.id}, page_content={self.page_content[:100]}..., metadata={self.metadata})"

# Classe para realizar o splitting de textos em pedaços para embedding
class CustomTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(
        self,
        chunk_size: int = EMBEDDING_CHUNK_SIZE,
        chunk_overlap: int = EMBEDDING_OVERLAP,
        length_function = len,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_documents(self, documents: List[CustomDocument]) -> List[CustomDocument]:
        if not documents:
            return []

        chunks = []
        for doc in documents:
            try:
                # Garante que metadata seja um dicionário e inclua o id
                metadata = {**(doc.metadata if isinstance(doc.metadata, dict) else {}), "id": getattr(doc, "id", "no_id")}
                text = doc.page_content
                id_doc = getattr(doc, "id", "no_id")

                # Se o texto for curto, não precisa dividir
                if self.length_function(text) <= self.chunk_size:
                    chunks.append(CustomDocument(id=id_doc, page_content=text, metadata=metadata))
                    continue

                # Divide o texto em sentenças
                sentences = [s.strip() + ". " for s in text.split(". ") if s.strip()]
                current_chunk = []
                current_length = 0

                for sentence in sentences:
                    sentence_length = self.length_function(sentence)
                    # Se a sentença for maior que o chunk_size, divida em palavras
                    if sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(CustomDocument(id=id_doc, page_content="".join(current_chunk), metadata=metadata))
                            current_chunk = []
                            current_length = 0
                        words = sentence.split()
                        current_words = []
                        current_word_length = 0
                        for word in words:
                            word_length = self.length_function(word + " ")
                            if current_word_length + word_length > self.chunk_size:
                                chunks.append(CustomDocument(id=id_doc, page_content=" ".join(current_words), metadata=metadata))
                                current_words = [word]
                                current_word_length = word_length
                            else:
                                current_words.append(word)
                                current_word_length += word_length
                        if current_words:
                            current_chunk = [" ".join(current_words)]
                            current_length = self.length_function(current_chunk[0])
                        continue

                    # Se adicionar a sentença ultrapassar o chunk_size, finalize o chunk atual
                    if current_length + sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(CustomDocument(id=id_doc, page_content="".join(current_chunk), metadata=metadata))
                            # Mantém uma sobreposição para contexto
                            overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                            current_chunk = current_chunk[overlap_start:]
                            current_length = sum(self.length_function(s) for s in current_chunk)
                    current_chunk.append(sentence)
                    current_length += sentence_length

                # Adiciona o último chunk, se houver
                if current_chunk:
                    chunks.append(CustomDocument(id=id_doc, page_content="".join(current_chunk), metadata=metadata))
            except Exception as e:
                logger.error(f"Error splitting document: {str(e)}")
                continue

        return chunks

# Função para criar o vector store com Chroma
def create_vector_store(documents: List[CustomDocument]) -> Chroma:
    try:
        if not documents:
            logger.error("No documents provided for vector store creation")
            return None

        # Define os caminhos (ajuste conforme sua estrutura)
        BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/chroma_db")
        OLD_PATH = os.path.join(BASE_DIR, "old")
        os.makedirs(OLD_PATH, exist_ok=True)
        logger.info(f"Ensuring old vector store directory exists: {OLD_PATH}")

        logger.info("Starting document splitting process")
        split_start = time.time()

        # Inicializa o text splitter e divide os documentos
        text_splitter = CustomTextSplitter()
        split_data = text_splitter.split_documents(documents)
        logger.info(f"Document splitting completed in {time.time() - split_start:.2f}s")

        logger.info("Initializing Chroma vector store for legacy data")
        store_start = time.time()

        store = Chroma.from_documents(
            documents=split_data,
            collection_name="legacy_RAG",  # Nome da coleção para distinguir
            embedding=embedding_model,
            persist_directory=OLD_PATH,
            collection_metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:search_ef": 50,
            },
        )
        logger.info(f"Legacy vector store creation completed in {time.time() - store_start:.2f}s")
        return store

    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise
    finally:
        # Libera memória, se necessário
        gc.collect()

# Função para carregar um vector store com base no idioma
def get_vector_store(language_code: str, VECTOR_STORE_PATHS: dict, LANGUAGE_DEFAULT: str = "en") -> Chroma:
    try:
        if language_code not in VECTOR_STORE_PATHS:
            logger.warning(f"Unsupported language code: {language_code}, falling back to English")
            language_code = LANGUAGE_DEFAULT

        store_path = VECTOR_STORE_PATHS.get(language_code)
        logger.info(f"Loading vector store for language: {language_code}")
        return Chroma(
            persist_directory=store_path,
            embedding_function=embedding_model,
            collection_name=f"docs_{language_code}",
        )
    except Exception as e:
        logger.error(f"Error loading vector store: {str(e)}")
        raise

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
                    search_type="mmr",
                    search_kwargs={
                        "k": MMR_SEARCH_K,
                        "fetch_k": MMR_FETCH_K,
                        "lambda_mult": MMR_LAMBDA_MULT,
                    },
                )
                results = retriever.invoke(query)
                all_results.extend(results)
                logger.info(f"Accumulated {len(all_results)} results so far.")
            return all_results[:3]
        finally:
            gc.collect()

    def invoke(self, query: str):
        return self.get_relevant_documents(query)