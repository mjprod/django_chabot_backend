import os
import datetime
import chromadb

from utils.logger import logger, get_progress_bar
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from .config import (
    # vector store constants
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    CHROMA_DIR,
    MESSAGE_KEY,
)

from ..app.mongo import MongoDB

from api.ai_services import (
    BrainDocument,
)

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
                ),# TODO: LangChainBetaWarning: The function `init_chat_model` is in beta. It is actively being worked on, so the API may change.
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

            try:
                db = MongoDB.get_db()

                # Retrieve all documents
                results = db.brain.find({})
                # for doc in results:
                    # print(doc)

                # Get the count of all documents
                count = db.brain.count_documents({})
                print("Total documents:", count)
            
                logger.info(f"Preprocessing {count} documents")
                processed_conversations = self._preprocessing_conversation(results)
                brain_count=len(processed_conversations)

                logger.info(f"{brain_count} documents loading to the brain")
                self._parse_conversations(processed_conversations, brain_count)


            except KeyboardInterrupt:
                logger.info(f"Process interrupted")
            finally:
                # MongoDB connection gets closed even if the program is interrupted
                # mongodb_client.close()  
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
                processed_conversation.append(conversation)
        except KeyError as e:
            logger.error(f"{e}")
            pass
        return processed_conversation

    def _parse_conversations(self, conversations, count):
        logger.info(f"Conversations received: {len(conversations)}")
        # Create Document Objects using list comprehension
        doc_objects = [
            BrainDocument(
                id=doc.get("id", "no_id"),
                page_content=(
                    f"Question: {doc['question']['text']}\n"
                    f"Answer: {doc['answer']['detailed']['en']}"
                ),
                metadata={
                    "id": doc.get("id", ""),
                    "category": ",".join(doc["metadata"].get("category", [])),
                    "subCategory": doc["metadata"].get("subCategory", ""),
                    "difficulty": doc["metadata"].get("difficulty", 0),
                    "confidence": doc["metadata"].get("confidence", 0.0),
                    "intent": doc["question"].get("intent", ""),
                    "variations": ", ".join(doc["question"].get("variations", [])),
                    "conditions": ", ".join(doc["answer"].get("conditions", [])),
                },
            )
            for doc in conversations
        ]
        # Get the IDs of the documents
        doc_ids = [doc.get("id", "no_id") for doc in conversations]

        # Add the documents to the vector store
        self.vector_store.add_documents(documents=doc_objects, ids=doc_ids)

        # Update the progress bar (if count is correct, this should advance by count)
        with get_progress_bar() as progress:
            task = progress.add_task("Processing conversations", total=count)
            progress.update(task, advance=count)

        logger.info(f"@@@@ Processed {len(doc_objects)} documents")
        return doc_objects
            
    def _check_collection_count(self):
        client = chromadb.PersistentClient(path=self.chroma_dir)
        collection = client.get_collection(name=self.collection_name)
        return collection.count()

    def query(self, query:str, k:int=3):
        return self.vector_store.similarity_search(query, k=k)
    