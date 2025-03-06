import shutil
import os
import logging
import datetime
from utils.logger import logger, get_progress_bar

from .config import (
    # vector store constants
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    CHROMA_DIR,
    DATE_THRESHOLD,
    MESSAGE_KEY
)

from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

import chromadb

from ..mongodb.mongodb_client import MongoDBClient

load_dotenv()

USER_AGENT = os.getenv("USER_AGENT","chatbot")
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY",None)
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY",None)
TOKENIZERS_PARALLELISM=os.getenv("TOKENIZERS_PARALLELISM", False)


class Brain:
    # store the singleton instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Brain, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, 
                 collection_name=COLLECTION_NAME, 
                 chroma_dir=CHROMA_DIR, 
                 embedding_model=EMBEDDING_MODEL):
        
        if not hasattr(self, 'initialised'):
            self.collection_name = collection_name
            self.chroma_dir = chroma_dir
            self.embedding_model = embedding_model
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=HuggingFaceEmbeddings(
                    model_name=embedding_model
                ),
                persist_directory=chroma_dir,
            )
            self.initialised = True
            self.load_conversations_to_store()

    def load_conversations_to_store(self):
        """
        Load the document store with a list of documents if the chroma store is empty
        """
        document_count = self._check_collection_count()

        if  document_count > 0:
            logger.info(f"The brain '{self.collection_name}' already has {document_count} documents, loading the brain")
        else:
            # create old conversation chromadb
            logger.info(f"Initialising MongoDB connection")

            try:
                mongodb_client = MongoDBClient()

                # query = {
                #     "updated_at": {
                #         "$gt": DATE_THRESHOLD.strftime("%Y-%m-%dT%H:%M:%SZ")  # Convert datetime to string format
                #     }
                # }

                logger.info(f"Fetching old conversations from Mongodb")
                results, count = mongodb_client.query(collection="old_conversation",query=None)
            
                logger.info(f"Preprocessing {count} documents")
                processed_conversations = self._preprocessing_conversation(results)
                qualified_count=len(processed_conversations)

                logger.info(f"{qualified_count} qualified documents found, loading to the brain")
                self._parse_conversations(processed_conversations, qualified_count)


            except KeyboardInterrupt:
                logger.info(f"Process interrupted")
            finally:
                # MongoDB connection gets closed even if the program is interrupted
                mongodb_client.close()  
                logger.info(f"Closing MongoDB connection")              
         
    def add_documents(self, document):
        """
        TODO: Add a new document to the document store
        """
        self.vector_store.add_documents(document)

    def delete_document(self, document):
        self.vector_store.delete(document)

    def update_document(self, document):
        self.vector_store.update_document(document)

    def _preprocessing_conversation(self, conversations):
        processed_conversation = []
        try: 
            for conversation in conversations:
                if len(conversation[MESSAGE_KEY]) > 2:
                    processed_conversation.append(conversation)
        except KeyError as e:
            logger.error(f"{e}")
            pass
        return processed_conversation

    def _parse_conversations(self, conversations, count):
        with get_progress_bar() as progress:
            task = progress.add_task("Processing conversations", total=count)
            for conversation in conversations:
                chroma_doc = Document(
                    id=str(conversation['_id']),
                    page_content=str(conversation[MESSAGE_KEY]),
                    metadata={ 
                        "id": str(conversation['_id']),
                        # "session_id": conversation.get('session_id'),
                        # "language": conversation.get('language',"None"),
                        # "category": conversation.get("category", "None"),
                        # "subcategory": conversation.get("subcategory", "None"),
                        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    }
                )
                id = str(conversation['_id'])
                self.vector_store.add_documents(documents=[chroma_doc], ids=[id])
                progress.update(task, advance=1)

        return chroma_doc
    
    def _check_collection_count(self):
        client = chromadb.PersistentClient(path=self.chroma_dir)
        collection = client.get_collection(name=self.collection_name)
        return collection.count()

    def query(self, query:str, k:int=3):
        return self.vector_store.similarity_search(query, k=k)