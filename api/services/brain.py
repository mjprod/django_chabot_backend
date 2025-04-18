import os
import logging
import chromadb
import json
import re
import tiktoken
import warnings

from typing import List
from dotenv import load_dotenv
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
from api.ai_services import BrainDocument

warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

from .config import EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_DIR
from ai_config.ai_constants import COHERE_MODEL

logger = logging.getLogger(__name__)
load_dotenv()


class Brain:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Brain, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, collection_name=COLLECTION_NAME, chroma_dir=CHROMA_DIR):
        if hasattr(self, 'initialized'):
            return

        self.collection_name = collection_name
        self.chroma_dir = chroma_dir
        self.embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="mjpro")
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.chroma_dir,
        )
        self.initialized = True
        self.ensure_documents_loaded()

    def ensure_documents_loaded(self):
        if self._check_collection_count() == 0:
            documents = self.load_and_process_json_file()
            rules_chunks = self._load_and_chunk_rules()
            all_docs = self.prepare_brain_documents(documents + rules_chunks)
            self.vector_store.add_documents(all_docs)
            logger.info(f"{len(all_docs)} documents loaded to ChromaDB.")
        else:
            logger.info("ChromaDB already initialized with documents.")

    def load_and_process_json_file(self) -> List[dict]:
        base_dir = os.path.join(os.path.dirname(__file__), "../../data")
        database_files = ["database_part_1.json", "database_part_2.json", "database_part_3.json"]
        all_documents = []

        for file_name in database_files:
            file_path = os.path.join(base_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        detailed_answer = item.get("answer", {}).get("detailed", {}).get("en", "")
                        if item.get("question", {}).get("text") and detailed_answer:
                            all_documents.append({
                                "id": item.get("id", "no_id"),
                                "content": f"Question: {item['question']['text']}\nAnswer: {detailed_answer}",
                                "metadata": {
                                    "category": ",".join(item.get("metadata", {}).get("category", [])),
                                    "subCategory": item.get("metadata", {}).get("subCategory", ""),
                                },
                            })
            except Exception as e:
                logger.error(f"Error loading {file_name}: {e}")
        return all_documents

    def _load_and_chunk_rules(self, file_name="4DJokerRulesDocument.markdown", max_tokens=400):
        base_dir = os.path.join(os.path.dirname(__file__), "../../data")
        file_path = os.path.join(base_dir, file_name)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                rules_content = f.read()

            sections = re.split(r'(## .+)', rules_content)
            encoding = tiktoken.encoding_for_model("gpt-4")
            chunks, current_chunk, current_tokens = [], "", 0

            for section in sections:
                if not section.strip():
                    continue
                section_tokens = len(encoding.encode(section))
                if current_tokens + section_tokens > max_tokens:
                    chunks.append(current_chunk.strip())
                    current_chunk, current_tokens = section, section_tokens
                else:
                    current_chunk += "\n" + section
                    current_tokens += section_tokens

            if current_chunk:
                chunks.append(current_chunk.strip())

            return [{
                "id": f"joker_rules_en_{i}",
                "content": chunk,
                "metadata": {"category": "static_rules"}
            } for i, chunk in enumerate(chunks)]

        except Exception as e:
            logger.error(f"Error chunking rules file: {e}")
        return []

    def prepare_brain_documents(self, raw_docs):
        return [
            BrainDocument(id=doc["id"], page_content=doc["content"], metadata=doc["metadata"])
            for doc in raw_docs
        ]

    def _check_collection_count(self):
        client = chromadb.PersistentClient(path=self.chroma_dir)
        collection = client.get_or_create_collection(name=self.collection_name)
        return collection.count()

    def query(self, query: str, k: int = 6):
        return self.vector_store.similarity_search(query, k=k)









'''

import os
import logging
import chromadb
import json
from typing import List, Optional
import re
import tiktoken
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

from dotenv import load_dotenv

from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from .config import (
    # vector store constants
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    CHROMA_DIR,
)

from ..app.mongo import MongoDB

from api.ai_services import (
    BrainDocument,
)

# constants
from ai_config.ai_constants import (
    COHERE_MODEL,
)

logger = logging.getLogger(__name__)

load_dotenv()


OPENAI_API_KEY= os.getenv("OPENAI_API_KEY",None)

embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="mjpro")

# added function for loading and processing the json file
def load_and_process_json_file() -> List[dict]:
    base_dir = os.path.join(os.path.dirname(__file__),  "../../data")
    database_files = [
        "database_part_1.json",
        "database_part_2.json",
        "database_part_3.json",
       
    ]

    all_documents = []

    for file_name in database_files:
        file_path = os.path.join(base_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict):
                        # Extract detailed answer in English
                        detailed_answer = (
                            item.get("answer", {}).get("detailed", {}).get("en", "")
                        )

                        # Process metadata with proper error handling
                        metadata = item.get("metadata", {})
                        processed_metadata = {
                            "id": item.get("id", ""),
                            "category": ",".join(metadata.get("category", [])),
                            "subCategory": metadata.get("subCategory", ""),
                            "difficulty": metadata.get("difficulty", 0),
                            "confidence": metadata.get("confidence", 0.0),
                            "dateCreated": metadata.get("dateCreated", ""),
                            "lastUpdated": metadata.get("lastUpdated", ""),
                            "version": metadata.get("version", "1.0"),
                            "status": metadata.get("status", "active"),
                        }

                        # Create structured document
                        document = {
                            "question": {
                                "text": item.get("question", {}).get("text", ""),
                                "variations": item.get("question", {}).get(
                                    "variations", []
                                ),
                                "intent": item.get("question", {}).get("intent", ""),
                                "languages": item.get("question", {}).get(
                                    "languages", {}
                                ),
                            },
                            "answer": {
                                # "short": item.get("answer", {}).get("short", {}),
                                "detailed": item.get("answer", {}).get("detailed", {}),
                                "conditions": item.get("answer", {}).get(
                                    "conditions", []
                                ),
                            },
                            "id": item.get("id", ""),
                            "metadata": processed_metadata,
                            "context": item.get("context", {}),
                        }

                        # Validate document key/values
                        if document["question"]["text"] and detailed_answer:
                            all_documents.append(document)

        except FileNotFoundError:
            logger.error(f"Database file not found: {file_name}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {file_name}")
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")

    if not all_documents:
        logger.warning("No documents were loaded from the database files")

    return all_documents



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
            # self.load_conversations_to_store()
            self.get_vector_store()


    def _load_and_chunk_rules(self, file_name="4DJokerRulesDocument.markdown", max_tokens=400) -> List[BrainDocument]:
        base_dir = os.path.join(os.path.dirname(__file__), "../../data")
        file_path = os.path.join(base_dir, file_name)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                rules_content = f.read()

            # Split by markdown H2 headers
            sections = re.split(r'(## .+)', rules_content)
            encoding = tiktoken.encoding_for_model("gpt-4")
            chunks = []

            current_chunk = ""
            current_tokens = 0

            for section in sections:
                if not section.strip():
                    continue
                section_tokens = len(encoding.encode(section))
                if current_tokens + section_tokens > max_tokens:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = section
                    current_tokens = section_tokens
                else:
                    current_chunk += "\n" + section
                    current_tokens += section_tokens

            if current_chunk:
                chunks.append(current_chunk.strip())

            doc_chunks = [
                BrainDocument(
                    id=f"joker_rules_en_{i}",
                    page_content=chunk,
                    metadata={
                        "id": f"joker_rules_en_{i}",
                        "category": "static_rules",
                        "language": "en",
                        "type": "reference",
                        "chunk": i,
                        "source": file_name
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            return doc_chunks

        except FileNotFoundError:
            logger.error(f"Rules file not found: {file_name}")
        except Exception as e:
            logger.error(f"Error loading and chunking rules file: {str(e)}")
        return []

    def get_vector_store(self):
        """Retrieve the vector store for a given collection."""
        documents = load_and_process_json_file()
        
        # Create Document Objects
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
            for doc in documents
        ]

        rules_chunks = self._load_and_chunk_rules("4DJokerRulesDocument.markdown")
        if rules_chunks:
            doc_objects.extend(rules_chunks)

        self.vector_store.add_documents(doc_objects)
       
        all_docs = self.vector_store.get()
        print("All docs IDs:", all_docs["ids"]) 

        processed_conversations = self._preprocessing_conversation(documents)
        brain_count=len(processed_conversations)

        logger.info(f"{brain_count} documents loading to the brain")
        self._parse_conversations(processed_conversations, brain_count)

        for idx, doc_id in enumerate(all_docs["ids"]):
            if "joker_rules" in doc_id:
                print(f"📘 Found Rules Doc: {doc_id}")
                print("🔍 Preview:", all_docs["documents"][idx][:100], "...") 

        return self.vector_store
    

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

    
        logger.info(f"@@@@ Processed {len(doc_objects)} documents")
        return doc_objects
            
    def _check_collection_count(self):
        client = chromadb.PersistentClient(path=self.chroma_dir)
        collection = client.get_collection(name=self.collection_name)
        return collection.count()

    def query(self, query:str, k:int=6):
        return self.vector_store.similarity_search(query, k=k)
        '''
