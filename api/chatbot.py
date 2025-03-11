import gc
import json
import logging
import os
import time
import re

from typing import List

from django.conf import settings
from dotenv import load_dotenv

from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import Chroma

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from openai import OpenAI

# mongodb imports
from pymongo import MongoClient

# constants
from api.constants.ai_constants import (
    OPENAI_MODEL,
    COHERE_MODEL,
    MAX_TEMPERATURE,
)

from api.constants.ai_prompts import (
    FIRST_MESSAGE_PROMPT,
    FOLLOW_UP_PROMPT,
    DOCUMENT_RELEVANCE_PROMPT,
    CONFIDENCE_GRADER_PROMPT,
    RAG_PROMPT_TEMPLATE,
    PROMPT_TEMPLATE_MONGO_AND_OPENAI,
)

from api.views.brain_file_reader import (
    get_document_by_id,
    update_answer_detailed
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

embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="glaucomp")
vectorstores = []
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

# Process docs
try:
    logger.info("Starting vector store creation with filtered documents")
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

def update_local_confidence(generation, confidence_diff):
    try:
        logger.info(
            "Starting update of local confidence scores across all database files"
        )
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

        updated = False
        for database_file in database_files:
            file_path = os.path.join(base_dir, database_file)
            try:
                with open(file_path, "r+") as f:
                    data = json.load(f)
                    for item in data:
                        # Correctly access nested dictionary structure
                        if (
                            isinstance(item, dict)
                            and "answer" in item
                            and "detailed" in item["answer"]
                            and "en" in item["answer"]["detailed"]
                            and item["answer"]["detailed"]["en"] == generation
                        ):
                            current_confidence = item["metadata"]["confidence"]
                            item["metadata"]["confidence"] = min(
                                1.0, current_confidence + (confidence_diff * 0.1)
                            )
                            updated = True
                            logger.info(
                                f"Updated confidence in {database_file} "
                                f"from {current_confidence} to {item['metadata']['confidence']}"
                            )

                            # Write back to file
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            f.truncate()
                            logger.info(f"Successfully updated {database_file}")
                            break

            except FileNotFoundError:
                logger.error(f"Database file not found: {database_file}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in file: {database_file}")
            except Exception as e:
                logger.error(f"Error processing file {database_file}: {str(e)}")
        if not updated:
            logger.warning("No matching answer found in any database files")
    except Exception as e:
        logger.error(f"Error updating local confidence: {str(e)}")

def update_database_confidence(comparison_result, docs_to_use):
    try:
        logger.info("Starting database confidence update")
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

        for database_file in database_files:
            file_path = os.path.join(base_dir, database_file)
            try:
                with open(file_path, "r+") as f:
                    data = json.load(f)
                    for i, item in enumerate(data):
                        # Check if the answer matches using proper dictionary access
                        if (
                            isinstance(item, dict)
                            and "answer" in item
                            and "detailed" in item["answer"]
                            and "en" in item["answer"]["detailed"]
                            and item["answer"]["detailed"]["en"]
                            == comparison_result["best_feedback"]["correct_answer"]
                        ):

                            current_confidence = item["metadata"]["confidence"]
                            data[i]["metadata"]["confidence"] = min(
                                1.0, current_confidence + 0.1
                            )

                            logger.info(
                                f"Updated confidence in {database_file} "
                                f"from {current_confidence} to {data[i]['metadata']['confidence']}"
                            )

                            # Write back to file
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            f.truncate()
                            logger.info(f"Successfully updated {database_file}")
                            break

            except Exception as e:
                logger.error(f"Error processing file {database_file}: {str(e)}")

    except Exception as e:
        logger.error(f"Error updating database confidence: {str(e)}")

def check_answer_mongo_and_openai(user_question, matches):
    if not matches:
        return None

    prompt = f"User question: {user_question}\n\n"
    prompt += "Here are some possible answers found in the database:\n"

    for idx, match in enumerate(matches):
        question = match.get("user_input", "N/A")
        answer = match.get("correct_answer", "N/A")
        prompt += f"\nQ{idx + 1}: {question}\nA{idx + 1}: {answer}\n"

    prompt += PROMPT_TEMPLATE_MONGO_AND_OPENAI.format(user_question=user_question)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY environment variable.")
        return "false"

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant evaluating answers to user questions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    final_response = response.choices[0].message.content.strip()
    final_response = re.sub(r'^["\']|["\']$', "", final_response)

    if "no" in final_response.lower() and len(final_response) < 5:
        return None

    return final_response
    
def update_chroma_document(doc_id, new_data):
    """
    Update an existing document in the ChromaDB collection.
    :param store: The ChromaDB collection object
    :param doc_id: The unique ID of the document to update
    :param new_data: Dictionary containing updated data fields
    """
    try:

        if store:  # Only search if store was successfully created
            search_results = search_by_id(store, "0068")  # Replace "0001" with your ID
            print("Search Results:", search_results)
        else:
            print("Vector store creation failed, cannot perform search.")

        return True
        all_docs = store.get()

        for key, value in all_docs.items():
                print(f"{key}: {value}")

        existing_docs = store.get(ids=[doc_id], include=["documents", "metadatas"])
        
        if not existing_docs["documents"]:
            print(f"Document with ID {doc_id} not found.")
            return False

        # Retrieve the existing document
        existing_doc = json.loads(existing_docs["documents"][0])  # Convert back to dictionary if stored as JSON string

        # Merge the existing document with new data
        updated_doc = {**existing_doc, **new_data}

        # Remove the old document before re-adding
        store.delete(ids=[doc_id])

        # Reinsert the updated document
        store.add(
            documents=[json.dumps(updated_doc)],  # Store as JSON string
            ids=[doc_id],
            metadatas=[updated_doc.get("metadata", {})]
        )

        print(f"Document with ID {doc_id} updated successfully.")
        return True

    except Exception as e:
        print(f"Error updating document: {e}")
        return False
    
def search_by_id(store: Chroma, custom_id: str):
    results = store.get(
        where={"id": custom_id},
        include=["documents", "metadatas"]
    )
    return results

def update_document_by_custom_id(custom_id: str, answer_en: str, answer_ms: str, answer_cn: str):
    try:
        search_results = store.get(
            where={"id": custom_id},
            include=["metadatas","documents"]
        )

        if not search_results['ids']:
            print(f"Document ID '{custom_id}' not found.")
            return

        document_id = search_results['ids'][0]
        doc = get_document_by_id(document_id) 
        
        if doc:
            update_answer_detailed(doc, answer_en, answer_ms, answer_cn)

        existing_metadata = search_results['metadatas'][0]
        document = search_results['documents'][0]
        question_text = document.split("\n")[0].replace("Question: ", "").strip()

        new_document = CustomDocument(
            id=custom_id,
            page_content=(
                f"Question: {question_text}\n"
                f"Answer: {answer_en}"
            ),
            metadata={
                "category": ",".join(existing_metadata.get("category", [])),
                "subCategory": existing_metadata.get("subCategory", ""),
                "difficulty": existing_metadata.get("difficulty", 0),
                "confidence": existing_metadata.get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "variations": ", ".join(doc["question"].get("variations", [])),
                "conditions": ", ".join(doc["answer"].get("conditions", [])),
            },
        )

        store.add_documents(documents=[new_document])
        return (f"ID '{custom_id}' updated ")
    except Exception as e:
        print(f"Error to update document: {str(e)}")

        
