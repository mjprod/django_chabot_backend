import os
import json
import time
import logging
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import Chroma

from dotenv import load_dotenv

load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Constants
COHERE_MODEL = "embed-english-v3.0"  # os.environ.get("COHERE_MODEL")
EMBEDDING_CHUNK_SIZE = 500  # int(os.environ.get("EMBEDDING_CHUNK_SIZE", "500"))
EMBEDDING_OVERLAP = 50  # int(os.environ.get("EMBEDDING_OVERLAP", "50"))
CHROMA_PATH = "./chroma_db"  # os.environ.get("CHROMA_PATH", "./chroma_db")

class CustomDocument:
    def __init__(self, page_content, metadata, id="0"):
        self.id = id
        self.page_content = page_content
        self.metadata = metadata

    def __str__(self):
        # Mostra o id e os primeiros 100 caracteres do conteúdo para não poluir o log
        return f"CustomDocument(id={self.id}, page_content={self.page_content[:100]}..., metadata={self.metadata})"

# Text Splitter Class
class CustomTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(
        self,
        chunk_size=EMBEDDING_CHUNK_SIZE,
        chunk_overlap=EMBEDDING_OVERLAP,
        length_function=len,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_documents(self, documents):
        if not documents:
            return []

        chunks = []

        for doc in documents:
            try:
                metadata = {**(doc.metadata if isinstance(doc.metadata, dict) else {}), "id": getattr(doc, "id", "no_id")}
                text = doc.page_content
                id_doc = getattr(doc, "id", "no_id")

                # Handle short documents
                if self.length_function(text) <= self.chunk_size:
                    chunks.append(CustomDocument(id=id_doc, page_content=text, metadata=metadata))
                    continue

                # Split into sentences
                sentences = [s.strip() + ". " for s in text.split(". ") if s.strip()]
                current_chunk = []
                current_length = 0

                for sentence in sentences:
                    sentence_length = self.length_function(sentence)

                    # Handle sentences longer than chunk_size
                    if sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(
                                CustomDocument(
                                    id=id_doc,
                                    page_content="".join(current_chunk),
                                    metadata=metadata,
                                )
                            )
                            current_chunk = []
                            current_length = 0

                        # Split long sentence
                        words = sentence.split()
                        current_words = []
                        current_word_length = 0

                        for word in words:
                            word_length = self.length_function(word + " ")
                            if current_word_length + word_length > self.chunk_size:
                                chunks.append(
                                    CustomDocument(
                                        id=id_doc,
                                        page_content=" ".join(current_words),
                                        metadata=metadata,
                                    )
                                )
                                current_words = [word]
                                current_word_length = word_length
                            else:
                                current_words.append(word)
                                current_word_length += word_length

                        if current_words:
                            current_chunk = [" ".join(current_words)]
                            current_length = self.length_function(current_chunk[0])
                        continue

                    # Normal sentence processing
                    if current_length + sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(
                                CustomDocument(
                                    id=id_doc,
                                    page_content="".join(current_chunk),
                                    metadata=metadata,
                                )
                            )

                            # Handle overlap
                            overlap_start = max(
                                0, len(current_chunk) - self.chunk_overlap
                            )
                            current_chunk = current_chunk[overlap_start:]
                            current_length = sum(
                                self.length_function(s) for s in current_chunk
                            )

                    current_chunk.append(sentence)
                    current_length += sentence_length

                # Add remaining text
                if current_chunk:
                    chunks.append(
                        CustomDocument(
                            id=id_doc,
                            page_content="".join(current_chunk),
                            metadata=metadata
                        )
                    )

            except Exception as e:
                logger.error(f"Error splitting document: {str(e)}")
                continue

        return chunks

# added function for loading and processing the json file
def load_and_process_json_file() -> List[dict]:
    base_dir = os.path.join(os.path.dirname(__file__), "../../data")
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
                                "conditions": item.get("conditions", []
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

# Process docs
embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="glaucomp")
documents = load_and_process_json_file()

# Create Document Objects
doc_objects = [
    CustomDocument(
        id=str(doc.get("id", "no_id")),
        page_content=str(doc['answer']['detailed']['en']),
        metadata={
            "id": str(doc.get("id", "no_id")),
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

def search_by_id(store: Chroma, custom_id: str):
    results = store.get(
        where={"id": custom_id},
        include=["documents", "metadatas"]
    )
    return results


# Process documents in batches
def create_vector_store(documents, batch_size=500):
    try:
        logger.info("Starting document splitting process")
        split_start = time.time()

        # Initialize Text Splitter inside the function
        text_splitter = CustomTextSplitter()

        # Split documents
        split_data = text_splitter.split_documents(documents)
        logger.info(f"Document splitting completed in {time.time() - split_start:.2f}s")

        logger.info("Initializing Chroma vector store")
        store_start = time.time()

        # Create store specifically for the old JSON files
        store = Chroma.from_documents(
            ids=[doc.id for doc in doc_objects],
            documents=split_data,
            embedding=embedding_model,
            collection_name="RAG",  # Changed collection name to differentiate
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
        return store

    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise

try:
    logger.info("Starting vector store creation with filtered documents")
    store = create_vector_store(doc_objects)
    logger.info("Vector store creation completed successfully")
except Exception as e:
    logger.error(f"Failed to create vector store: {str(e)}")
    store = None  # Ensure store is None if creation fails

# Example Usage:
if store:  # Only search if store was successfully created
    search_results = search_by_id(store, "0068")  # Replace "0001" with your ID
    print("Search Results:", search_results)
else:
    print("Vector store creation failed, cannot perform search.")
