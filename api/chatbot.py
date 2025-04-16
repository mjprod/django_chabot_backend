import json
import logging
import os
import time

from typing import List

from django.conf import settings
from dotenv import load_dotenv

from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from openai import OpenAI

# mongodb imports
from pymongo import MongoClient

# constants
from ai_config.ai_constants import (
    OPENAI_MODEL,
    OPENAI_TIMEOUT,
    COHERE_MODEL,
    MAX_TEMPERATURE,
)

from ai_config.ai_prompts import (
    FIRST_MESSAGE_PROMPT,
    FOLLOW_UP_PROMPT,
    DOCUMENT_RELEVANCE_PROMPT,
    CONFIDENCE_GRADER_PROMPT,
    RAG_PROMPT_TEMPLATE,
)



from api.brain_retriever import (
  MultiRetriever,
)

from .ai_services import (
  CustomDocument,
  CustomTextSplitter,
  GradeDocuments,
  GradeConfidenceLevel,
 )


# create our gloabl variables
logger = logging.getLogger(__name__)
logger.info("Initializing vector database...")
docs_to_use = []
prompt = ""


logger = logging.getLogger()

# Load environment variables
load_dotenv()

# added function for loading and processing the json file
def load_and_process_json_file() -> List[dict]:
    base_dir = os.path.join(os.path.dirname(__file__), "../data")
    database_files = [
        "database_part_1.json",
        "database_part_2.json",
        "database_part_3.json",
        "database_part_4.json",
        "database_part_5.json",
        "database_part_6.json",
        "old_conv_04_08_25.json",
        "old_conv_04_09_25.json",
        "old_conv_04_10_25.json",
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
                            "id": item.get("id", "")
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

embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="mjpro")
vectorstores = []
documents = load_and_process_json_file()

collection_name="RAG",
embedding=embedding_model,
persist_directory="./chroma_db",

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
        vectorstores.append(store)

        all_docs = store.get()
        print("All docs IDs:", all_docs["ids"]) 

        return store
    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise
    finally:
        del split_data

def is_vector_store_created(collection_name="RAG", persist_directory="./chroma_db"):
    collection_path = os.path.join(persist_directory, f"chromadb/{collection_name}")
    return os.path.exists(collection_path)

# Process docs
try:
    logger.info("Starting vector store creation with filtered documents")
    if is_vector_store_created(collection_name="RAG", persist_directory="./chroma_db"):
        print("Database already exists, loading existing vector store")
        store = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embedding_model
        )
        store.add_documents(doc_objects)
        store.persist()
    else:
        store = create_vector_store(doc_objects)

    logger.info("Vector store creation completed successfully")
except Exception as e: 
    logger.error(f"Failed to create vector store: {str(e)}")


retriever = MultiRetriever(vectorstores)


def get_rag_prompt_template(is_first_message):

    system_content = FIRST_MESSAGE_PROMPT if is_first_message else FOLLOW_UP_PROMPT

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_content),
            ("human", "Context: {context}\nQuestion: {prompt}"),
        ]
    )


# Initialize LLM for Grading
llm_grader = ChatOpenAI(model=OPENAI_MODEL, temperature=MAX_TEMPERATURE)
structured_llm_grader = llm_grader.with_structured_output(GradeDocuments)

# System Message for Grader
document_system_message = DOCUMENT_RELEVANCE_PROMPT

# Create Grading Prompt
document_grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", document_system_message),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {prompt}"),
    ]
)

# Runnable Chain for Document Grader
retrieval_grader = document_grade_prompt | structured_llm_grader


# Initialize LLM for Hallucination Grading
llm_confidence = ChatOpenAI(model=OPENAI_MODEL, temperature=MAX_TEMPERATURE)
structured_confidence_grader = llm_confidence.with_structured_output(
    GradeConfidenceLevel
)

# System Message for confidence Grader
confidence_system_message = CONFIDENCE_GRADER_PROMPT
# Create Confidence Grading Prompt
confidence_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", confidence_system_message),
        ("human", "Source facts: \n\n {documents} \n\n AI response: {generation}"),
    ]
)

# Runnable Chain for Confidence Grader
confidence_grader = confidence_prompt | structured_confidence_grader

# Define Prompt Template for RAG Chain
rag_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            RAG_PROMPT_TEMPLATE,
        ),
        ("assistant", "I'll provide clear, friendly direct answers to help you."),
        ("human", "Context: {context}\nQuestion: {prompt}"),
    ]
)

# Initialize LLM for RAG Chain
rag_llm = ChatOpenAI(model=OPENAI_MODEL, temperature=MAX_TEMPERATURE)


# Define Formatting Function
def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)

# Create RAG Chain
rag_chain = (
    {
        "context": lambda x: format_docs(docs_to_use),
        "prompt": RunnablePassthrough(),
    }
    | rag_prompt_template
    | rag_llm
    | StrOutputParser()
)

mongo_client = None

# API functions
def get_mongodb_client():
    global mongo_client
    if mongo_client is None:
        mongo_client = MongoClient(settings.MONGODB_URI)
    return mongo_client[settings.MONGODB_DATABASE]

def get_store():
    return store

def handle_mongodb_operation(operation):
    try:
        return operation()
    except Exception as e:
        print(f"MongoDB operation failed: {str(e)}")
        return None


