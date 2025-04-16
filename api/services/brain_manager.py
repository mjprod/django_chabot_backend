import logging
import chromadb
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from .config import EMBEDDING_MODEL, CHROMA_DIR
from ..models import KnowledgeContent

from .config import (
    CHROMA_BRAIN_COLLECTION
)


load_dotenv()
logger = logging.getLogger(__name__)

class BrainManager:
    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BrainManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.chroma_dir = CHROMA_DIR
            self.embedding_model = EMBEDDING_MODEL
            self.initialized = True
            self.chromadb_client = chromadb.PersistentClient(path=self.chroma_dir)
            logger.info("Brain instance initialized.")


    def get_vector_store(self, collection_name):
        """Retrieve the vector store for a given collection."""
        return Chroma(
            collection_name=collection_name,
            embedding_function=HuggingFaceEmbeddings(model_name=self.embedding_model),
            persist_directory=self.chroma_dir,
        )
    
    def add_documents(self, collection_name, knowledge_contents):
        """Add documents to the vector store with progress tracking."""
        try:
            vector_store = self.get_vector_store(collection_name)
            
            with get_progress_bar() as progress:
                task = progress.add_task(f"Adding {len(knowledge_contents)}  documents", total=len(knowledge_contents))
                
                for kc in knowledge_contents:
                    id, document = self._parse_knowledge_content(kc)
                    vector_store.add_documents(documents=[document], ids=[id])
                    progress.update(task, advance=1)
            
            logger.info(f"Successfully added {len(knowledge_contents)} documents to {collection_name}.")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
    

    def delete_documents(self, collection_name, ids):
        """Delete a document from the vector store."""
        try:
            ids = [str(id) for id in ids]
            vector_store = self.get_vector_store(collection_name)
            vector_store.delete(ids)
            logger.info(f"Deleted document {len(ids)} from '{collection_name}'.")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")


    def query(self, collection_name, query: str, k: int = 3):
        """Query the vector store for similar documents."""
        try:
            vector_store = self.get_vector_store(collection_name)
            return vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Query error: {e}")
            return [] 


    def get_by_ids(self, collection_name, ids):
        try:
            vector_store = self.get_vector_store(collection_name)
            ids = [str(id) for id in ids]
            return vector_store.get_by_ids(ids)
        except Exception as e:
            logger.error(f"Listing document error: {e}")
            return [] 


    def delete_collection(self, collection_name):
        vector_store = self.get_vector_store(collection_name)
        vector_store.delete_collection()


    def _parse_knowledge_content(self, kc):
        """Parse knowledge content into vector store format."""

        id = str(kc.id)  # Extract the ID

        document = Document(
            page_content=f"Question: {kc.question}\nAnswer: {kc.answer}",
            metadata={
                "knowledge_uuid": str(kc.knowledge.knowledge_uuid),
                "category": kc.knowledge.category.name if kc.knowledge.category else "",
                "subCategory": kc.knowledge.subcategory.name if kc.knowledge.subcategory else "",
                "language": kc.get_language_display(),
                "date_created": kc.date_created.strftime("%Y-%m-%d"),
                "last_updated": kc.last_updated.strftime("%Y-%m-%d"),
                "type": kc.knowledge.get_type_display(),
            },
        )

        return id, document
    

    def _check_chroma_collection_count(self, collection_name):
        """Check the number of documents in a collection."""
        try:
            collection = self.chromadb_client.get_or_create_collection(name=collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"Error checking collection count: {e}")
            return 0
    

    def _fetch_knowledge_contents_from_db(self, collection_name):
        """Fetch knowledge content from the KnowledgeContent table."""
        if collection_name == CHROMA_BRAIN_COLLECTION:
            logger.info("Getting knowledge content")
            return KnowledgeContent.objects.filter(in_brain=True).all()  # Filtering by Brain model
        else:
            raise ValueError(f"Loading content for other chroma collection: '{collection_name}' is not supported.")