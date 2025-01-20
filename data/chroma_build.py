# this file is used to build the vector store
# and run a few test queries in the langauges needed
# and then print the results

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from langchain.schema import Document as LangchainDocument
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Language configuration
LANGUAGE_CONFIG = {
    "en": {
        "file": "database_en.json",
        "name": "English",
        "questions": [
            "What are the payment methods available?",
            "How do I reset my password?",
            "What is your refund policy?",
            "How do I contact customer support?",
            "What are the VIP membership benefits?",
        ],
    },
    "ms_MY": {
        "file": "database_ms_MY.json",
        "name": "Malaysian",
        "questions": [
            "Apakah kaedah pembayaran yang tersedia?",
            "Bagaimana cara menetapkan semula kata laluan saya?",
            "Apakah dasar bayaran balik anda?",
            "Bagaimana saya boleh menghubungi khidmat pelanggan?",
            "Apakah manfaat keahlian VIP?",
        ],
    },
    "zh_CN": {
        "file": "database_zh_CN.json",
        "name": "Simplified Chinese",
        "questions": [
            "进行真钱投注之前我可以在试玩模式下玩游戏吗？",
            "你们为玩家提供会员计划或 VIP 福利吗？",
            "退款政策是什么？",
            "如何联系客户服务？",
            "VIP会员有什么福利？",
        ],
    },
    "zh_TW": {
        "file": "database_zh_TW.json",
        "name": "Traditional Chinese",
        "questions": [
            "有哪些支付方式？",
            "如何重置密碼？",
            "退款政策是什麼？",
            "如何聯繫客戶服務？",
            "VIP會員有什麼福利？",
        ],
    },
}


def load_language_documents(lang_code: str) -> List[dict]:
    """Load documents for a specific language."""
    try:
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, LANGUAGE_CONFIG[lang_code]["file"])

        # Add debug logging
        logger.info(f"Looking for file: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # The data is already a list, no need to access data[0]
                documents = data if isinstance(data, list) else []
                logger.info(
                    f"Loaded {len(documents)} documents for {LANGUAGE_CONFIG[lang_code]['name']}"
                )
                return documents
        except FileNotFoundError:
            logger.warning(f"Database file not found: {file_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading {lang_code} documents: {str(e)}")
        raise


def build_language_vector_store(lang_code: str, documents: List[dict]) -> Chroma:
    """Build vector store for a specific language."""
    try:
        logger.info(
            f"Starting vector store build for {LANGUAGE_CONFIG[lang_code]['name']}"
        )
        chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db", lang_code)

        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            logger.info(f"Removed existing vector store for {lang_code}")

        # Initialize embedding model
        embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")

        # Create language-specific documents
        doc_objects = []
        for doc in documents:
            # Extract language-specific content
            question = doc["question"][
                "text"
            ]  # The question text is directly in 'text'
            answer = doc["answer"]["detailed"]  # The answer is directly in 'detailed'

            page_content = f"Question: {question}\nAnswer: {answer}"

            metadata = {
                "category": ",".join(doc["metadata"].get("category", [])),
                "subCategory": doc["metadata"].get("subCategory", ""),
                "difficulty": doc["metadata"].get("difficulty", 0),
                "confidence": doc["metadata"].get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "language": lang_code,
            }

            doc_objects.append(
                LangchainDocument(page_content=page_content, metadata=metadata)
            )

        # Create store
        store = Chroma.from_documents(
            documents=doc_objects,
            collection_name=f"RAG_{lang_code}",
            embedding=embedding_model,
            persist_directory=chroma_path,
            collection_metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:search_ef": 50,
                "language": lang_code,
            },
        )
        logger.info(f"Vector store built successfully for {lang_code}")
        return store
    except Exception as e:
        logger.error(f"Failed to build vector store for {lang_code}: {str(e)}")
        raise


def test_language_vector_store(lang_code: str, store: Chroma):
    """Test vector store for a specific language."""
    logger.info(f"\nTesting {LANGUAGE_CONFIG[lang_code]['name']} Vector Store:")

    for question in LANGUAGE_CONFIG[lang_code]["questions"]:
        logger.info(f"\nQuery: {question}")
        results = store.similarity_search_with_score(question, k=3)

        for i, (doc, score) in enumerate(results, 1):
            relevancy_percentage = (1 - score) * 100
            logger.info(f"\nResult {i} (Relevancy: {relevancy_percentage:.2f}%):")
            logger.info(f"Content: {doc.page_content[:300]}...")
            logger.info(f"Categories: {doc.metadata['category']}")
            logger.info(f"Intent: {doc.metadata['intent']}")
            logger.info("-" * 50)


def main():
    load_dotenv()

    # Ensure COHERE_API_KEY is set
    if not os.getenv("COHERE_API_KEY"):
        raise ValueError("COHERE_API_KEY environment variable is not set")

    # Create vector stores for each language
    stores = {}
    for lang_code in LANGUAGE_CONFIG.keys():
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing {LANGUAGE_CONFIG[lang_code]['name']}")
        logger.info(f"{'='*50}")

        # Load documents
        documents = load_language_documents(lang_code)
        if documents:
            # Build vector store
            store = build_language_vector_store(lang_code, documents)
            stores[lang_code] = store

            # Test vector store
            test_language_vector_store(lang_code, store)


if __name__ == "__main__":
    main()
