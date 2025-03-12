import os
import json
import time
from typing import List
import logging

from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

from .ai_services import (
  CustomDocument,
  CustomTextSplitter,
 )

from api.constants.ai_constants import (
    COHERE_MODEL,
)

logger = logging.getLogger(__name__)

store = None

def get_store():
    return store

def load_and_process_json_file() -> List[dict]:
    base_dir = os.path.join(os.path.dirname(__file__), "../data")
    database_files = [
        "database_part_1.json",
        "database_part_2.json",
        "database_part_3.json",
        "database_part_4.json",
        "database_part_5.json",
        "database_part_6.json",
        "database_part_7.json",
        "database_part_8.json",
        "database_part_9.json",
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

documents = load_and_process_json_file()

# Create Document Objects
doc_objects = [
    CustomDocument(
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

# Process documents in batches
def create_vector_store():
    try:    
        global store  # Store the store in a global variable

        if store is not None:
          logger.info("Store already exists")
          return store
      
        embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="glaucomp")
        
        logger.info("Starting document splitting process")
        split_start = time.time()

        # Initialize Text Splitter inside the function
        text_splitter = CustomTextSplitter()

        # Split documents
        split_data = text_splitter.split_documents(doc_objects)
        logger.info(f"Document splitting completed in {time.time() - split_start:.2f}s")

        logger.info("Initializing Chroma vector store")
        store_start = time.time()

        # Create store specifically for the old JSON files
        store = Chroma.from_documents(
            ids=[doc.id for doc in doc_objects],
            documents=split_data,
            collection_name="RAG",
            embedding=embedding_model,
            persist_directory="./chroma_db",
            collection_metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:search_ef": 50,
            },
        )
        logger.info(
            f"Vector store creation completed in {time.time() - store_start:.2f}s"
        )

        all_docs = store.get()
        print("BRAIN docs IDs:", all_docs["ids"]) 

        return store
    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise
    finally:
        if 'split_data' in locals():
            del split_data