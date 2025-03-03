import json
import logging
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain.schema import Document as LangchainDocument
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def rebuild_vector_store(documents):
    try:
        logger.info("Starting vector store rebuild")
        chroma_path = "./chroma_db"
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            logger.info("Removed existing vector store")

        # Initialize embedding model with API key
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is not set")

        embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")

        # Convert to LangchainDocument objects
        doc_objects = []
        for doc in documents:
            page_content = (
                f"Question: {doc['question']['text']}\n"
                f"Answer: {doc['answer']['detailed']['en']}"
            )
            metadata = {
                "category": ",".join(doc["metadata"].get("category", [])),
                "subCategory": doc["metadata"].get("subCategory", ""),
                "difficulty": doc["metadata"].get("difficulty", 0),
                "confidence": doc["metadata"].get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "variations": ", ".join(doc["question"].get("variations", [])),
                "conditions": ", ".join(doc["answer"].get("conditions", [])),
            }
            doc_objects.append(
                LangchainDocument(id='KAKO_ID',page_content=page_content, metadata=metadata)
            )

        # Create store
        store = Chroma.from_documents(
            documents=doc_objects,
            collection_name="RAG",
            embedding=embedding_model,
            persist_directory=chroma_path,
            collection_metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:search_ef": 50,
            },
        )
        logger.info("Vector store rebuilt successfully")
        return store
    except Exception as e:
        logger.error(f"Failed to rebuild vector store: {str(e)}")
        raise


def reset_all_confidence_scores(target_score=0.5):
    try:
        logger.info(f"Starting bulk confidence score update to {target_score}")
        base_dir = os.path.join(Path(__file__).parent.parent, "data")
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

        total_updates = 0
        all_documents = []

        for database_file in database_files:
            file_path = os.path.join(base_dir, database_file)
            try:
                with open(file_path, "r+") as f:
                    data = json.load(f)
                    updates_made = 0

                    if data and isinstance(data[0], list):
                        inner_array = data[0]

                        for item in inner_array:
                            if isinstance(item, dict) and "metadata" in item:
                                item["metadata"]["confidence"] = target_score
                                updates_made += 1
                                all_documents.append(item)

                        data[0] = inner_array

                    if updates_made > 0:
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()

                    total_updates += updates_made
                    logger.info(
                        f"Updated {updates_made} confidence scores in {database_file}"
                    )

            except FileNotFoundError:
                logger.error(f"Database file not found: {database_file}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in file: {database_file}")
            except Exception as e:
                logger.error(f"Error processing file {database_file}: {str(e)}")

        logger.info(f"Completed confidence score reset. Total updates: {total_updates}")

        # Rebuild vector store with all documents
        if total_updates > 0:
            rebuild_vector_store(all_documents)

    except Exception as e:
        logger.error(f"Error in bulk confidence update: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    reset_all_confidence_scores(0.5)
