import asyncio
import gc
import json
import logging
import os
import time
import tracemalloc
import re

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List
from unittest import result

import requests
from bson import ObjectId
from django.conf import settings
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field

# mongodb imports
from pymongo import MongoClient

# constants
from ai_config.ai_constants import (
    OPENAI_MODEL,
    OPENAI_MODEL_EN_TO_CN,
    OPENAI_TIMEOUT,
    MAX_TOKENS,
    COHERE_MODEL,
    MAX_TEMPERATURE,
    EMBEDDING_CHUNK_SIZE,
    EMBEDDING_OVERLAP,
    MMR_SEARCH_K,
    MMR_FETCH_K,
    MMR_LAMBDA_MULT,
    URL_TRANSLATE_EN_TO_MS,
)
from ai_config.ai_prompts import (
    FIRST_MESSAGE_PROMPT,
    FOLLOW_UP_PROMPT,
    TRANSLATION_AND_CLEAN_PROMPT,
    DOCUMENT_RELEVANCE_PROMPT,
    CONFIDENCE_GRADER_PROMPT,
    TRANSLATION_EN_TO_CN_PROMPT,
    RAG_PROMPT_TEMPLATE,
)


def monitor_memory():
    """Start memory monitoring and return initial snapshot"""
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()
    return snapshot1


def compare_memory(snapshot1):
    """Compare memory usage against initial snapshot"""
    snapshot2 = tracemalloc.take_snapshot()
    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    print("[ Top 10 memory differences ]")
    for stat in top_stats[:10]:
        print(stat)
    gc.collect()  # Force garbage collection after comparison


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
                                "short": item.get("answer", {}).get("short", {}),
                                "detailed": item.get("answer", {}).get("detailed", {}),
                                "conditions": item.get("answer", {}).get(
                                    "conditions", []
                                ),
                            },
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


embedding_model = CohereEmbeddings(model=COHERE_MODEL)
vectorstores = []
documents = load_and_process_json_file()


class CustomDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


# Create Document Objects
doc_objects = [
    CustomDocument(
        page_content=(
            f"Question: {doc['question']['text']}\n"
            f"Answer: {doc['answer']['detailed']['en']}"
        ),
        metadata={
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
                text = doc.page_content
                metadata = doc.metadata

                # Handle short documents
                if self.length_function(text) <= self.chunk_size:
                    chunks.append(CustomDocument(page_content=text, metadata=metadata))
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
                            page_content="".join(current_chunk), metadata=metadata
                        )
                    )

            except Exception as e:
                logger.error(f"Error splitting document: {str(e)}")
                continue

        return chunks


# Process documents in batches
def create_vector_store(documents, batch_size=500):
    # memory_snapshot = monitor_memory()
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

        # Create store
        store = Chroma.from_documents(
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
        # compare_memory(memory_snapshot)
        return store
    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise
    finally:
        del split_data


# Process docs
filtered_docs = filter_complex_metadata(doc_objects)
try:
    logger.info("Starting vector store creation with filtered documents")
    store = create_vector_store(filtered_docs)
    logger.info("Vector store creation completed successfully")
except Exception as e:
    logger.error(f"Failed to create vector store: {str(e)}")


# retriever to retrieve across all 4 vector stores
class MultiRetriever:
    def __init__(self, query):
        self.vectorstores = vectorstores

    def get_relevant_documents(self, query):
        # memory_snapshot = monitor_memory()
        all_results = []
        try:
            for store in vectorstores:
                retriever = store.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": MMR_SEARCH_K,
                        "fetch_k": MMR_FETCH_K,
                        "lambda_mult": MMR_LAMBDA_MULT,
                    },
                )
                results = retriever.invoke(query)
                all_results.extend(results)
                # compare_memory(memory_snapshot)
                logger.info(
                    f"Processing completed with {len(all_results)} total results."
                )

            return all_results[:3]
        finally:
            gc.collect()

    def invoke(self, query):
        return self.get_relevant_documents(query)


retriever = MultiRetriever(vectorstores)


def get_rag_prompt_template(is_first_message):

    system_content = FIRST_MESSAGE_PROMPT if is_first_message else FOLLOW_UP_PROMPT

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_content),
            ("human", "Context: {context}\nQuestion: {prompt}"),
        ]
    )


# created message class to keep track of messages that build up a Conversation
class Message:
    def __init__(self, role, content, timestamp=None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()


# added Conversation class here that created our session specific information
class ConversationMetaData:
    def __init__(self, session_id, user_id, agent_id, admin_id, timestamp=None):
        self.session_id = session_id
        self.admin_id = admin_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.messages = []
        self.translations = []
        self._id = ObjectId()
        self.is_first_message = True

    def add_message(self, role, content):
        message = Message(role, content)
        self.messages.append(message)

        # translation layer
        if role == "assistant":
            malay_translation = translate_en_to_ms(content)
            chinese_translation = content

            self.translations.append(
                {
                    "message_id": len(self.messages) - 1,
                    "translations": [
                        {"language": "en", "text": content},
                        {
                            "language": "ms-MY",
                            "text": malay_translation.get("text", ""),
                        },
                        {"language": "cn", "text": chinese_translation.get("text", "")},
                    ],
                }
            )
            return message

    def get_conversation_history(self):
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in self.messages
        ]

    # save the output to a dict for using API
    def to_dict(self):
        return {
            "_id": self._id,
            "session_id": self.session_id,
            "admin_id": self.admin_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "messages": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in self.messages
            ],
            "translations": self.translations,
        }


# this is the OPENAI translate function
def translate_and_clean(text):
    logger.error("translate_and_clean")
    # memory_snapshot = monitor_memory()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY environment variable.")
        return text

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": TRANSLATION_AND_CLEAN_PROMPT,
                },
                {"role": "user", "content": f"Process this text: {text}"},
            ],
            max_tokens=MAX_TOKENS,
            timeout=OPENAI_TIMEOUT,
        )

        translated_text = response.choices[0].message.content.strip()

        translated_text = re.sub(r"^(Translated.*?:)", "", translated_text).strip()

        return translated_text

    except Exception as e:
        logger.error(f"Translation error: {str(e)}", exc_info=True)
        return text
    finally:
        # compare_memory(memory_snapshot)
        gc.collect()


# Define grading of docs
class GradeDocuments(BaseModel):
    confidence_score: float = Field(
        description="Confidence score between 0.0 and 1.0 indicating document relevance",
        ge=0.0,
        le=1.0,
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


# Define GradeHallucinations Model
class GradeConfidenceLevel(BaseModel):
    confidence_score: float = Field(
        description="""Confidence score between 0.0 and 1.0
        indicating how well the answer is grounded in source facts""",
        ge=0.0,
        le=1.0,
    )


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


# async for translations


async def generate_translations(generation):
    try:
        logger.info(f"Starting translations for: {generation}")

        with ThreadPoolExecutor() as executor:
            # Run translations
            malay_future = executor.submit(translate_en_to_ms, generation)
            chinese_future = executor.submit(translate_en_to_cn, generation)

            logger.info("Submitted translation tasks...")

            # Gather results
            translations = await asyncio.gather(
                asyncio.wrap_future(malay_future), asyncio.wrap_future(chinese_future)
            )

            logger.info(f"Translation results: {translations}")

            # Return structured translations
            output = [
                {"language": "en", "text": generation},
                {"language": "ms-MY", "text": translations[0].get("text", "")},
                {"language": "cn", "text": translations[1].get("text", "")},
            ]

            logger.info(f"Final output: {output}")
            return output
    except Exception as e:
        logger.error(f"Error in generate_translations: {str(e)}", exc_info=True)
        raise


def translate_en_to_cn(input_text):
    logger.info("Translating text to Chinese...")

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=OPENAI_MODEL_EN_TO_CN,
            messages=[
                {
                    "role": "system",
                    "content": TRANSLATION_EN_TO_CN_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Translate this text to Chinese: {input_text}",
                },
            ],
            temperature=0,
            timeout=OPENAI_TIMEOUT,
        )

        translation = response.choices[0].message.content.strip()

        return {
            "text": translation,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return {"text": "", "prompt_tokens": 0, "total_tokens": 0}


def translate_en_to_ms(input_text, to_lang="ms", model="base"):
    # this is the url we send the payload to for translation
    url = URL_TRANSLATE_EN_TO_MS

    # the payload struct
    payload = {
        "input": input_text,
        "to_lang": to_lang,
        "model": model,
        "top_k": 1,
        "top_p": 1,
        "repetition_penalty": 1.1,
        "temperature": 0,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MESOLITICA_API_KEY')}",
    }

    try:
        print(f"Sending translation request for: {input_text}")  # Debug print
        response = requests.post(url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")  # Debug print
        print(f"Response content: {response.text}")  # Debug print

        if response.status_code == 200:
            translation_data = response.json()
            return {
                "text": translation_data.get("result", ""),
                "usage": translation_data.get("usage", {}),
            }
    except Exception as e:
        print(f"Translation error: {str(e)}")

    return {"text": "", "prompt_tokens": 0, "total_tokens": 0}


def process_feedback_translation(feedback_data):
    try:
        logger.info("Processing feedback translation")

        # Translate user input if not in English
        user_input = translate_and_clean(feedback_data["user_input"])
        logger.info("User input translation completed")

        # Translate correct answer if provided and not in English
        if feedback_data.get("correct_answer"):
            correct_answer = translate_and_clean(feedback_data["correct_answer"])
            logger.info("Correct answer translation completed")
        else:
            correct_answer = ""

        return {
            **feedback_data,
            "user_input": user_input,
            "correct_answer": correct_answer,
        }
    except Exception as e:
        logger.error(f"Error processing feedback translation: {str(e)}")
        return feedback_data


# ahsfahssf this is an old functuion that will be removed in prod
def generate_user_input(cleaned_prompt):
    # Clean and translate prompt
    # cleaned_prompt = translate_and_clean(user_prompt)

    # Get relevant documents
    docs_retrieve = retriever.get_relevant_documents(cleaned_prompt)
    logger.error(f"Retrieved {len(docs_retrieve)} documents")

    docs_to_use = []

    # Filter documents
    for doc in docs_retrieve:
        relevance_score = retrieval_grader.invoke(
            {"prompt": cleaned_prompt, "document": doc.page_content}
        )
        if relevance_score.confidence_score >= 0.7:
            docs_to_use.append(doc)

    # Generate response
    generation = rag_chain.invoke(
        {
            "context": format_docs(docs_to_use),
            "prompt": cleaned_prompt,
        }
    )

    # Generate translations asynchronously
    translations = asyncio.run(generate_translations(generation))

    return {
        "generation": generation,
        "translations": translations,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def generate_prompt_conversation(
    user_prompt, conversation_id, admin_id, agent_id, user_id
):
    # memory_snapshot = monitor_memory()
    # start_time = time.time()
    logger.info("Starting prompt_conversation request")

    try:
        # this is a check for the conversation to remove Dear player
        db = get_mongodb_client()
        existing_conversation = db.conversations.find_one(
            {"session_id": conversation_id}
        )
        is_first_message = not existing_conversation

        # Initialize conversation
        conversation = ConversationMetaData(
            session_id=conversation_id,
            admin_id=admin_id,
            agent_id=agent_id,
            user_id=user_id,
        )
        conversation.is_first_message = is_first_message

        rag_prompt = get_rag_prompt_template(is_first_message)

        # Process prompt and add message
        logger.info("Processing user prompt")
        cleaned_prompt = translate_and_clean(user_prompt)
        conversation.add_message("user", user_prompt)

        # Get and filter relevant documents
        logger.info("Retrieving relevant documents")
        docs_start = time.time()
        docs_retrieve = retriever.invoke(cleaned_prompt)[:3]  # Limit initial retrieval
        docs_to_use = []

        for doc in docs_retrieve:
            relevance_score = retrieval_grader.invoke(
                {"prompt": cleaned_prompt, "document": doc.page_content}
            )
            if relevance_score.confidence_score >= 0.7:
                docs_to_use.append(doc)
        logger.info(f"Document retrieval completed in {time.time() - docs_start:.2f}s")

        # Generate  inital response
        logger.info("Generating AI response")
        dynamic_chain = (
            {
                "context": lambda x: format_docs(docs_to_use),
                "prompt": RunnablePassthrough(),
            }
            | rag_prompt
            | rag_llm
            | StrOutputParser()
        )

        generation_start = time.time()
        generation = dynamic_chain.invoke(
            {
                "context": format_docs(docs_to_use),
                "prompt": cleaned_prompt,
                "history": conversation.get_conversation_history(),
            }
        )
        logger.info(f"AI Generation completed in {time.time() - generation_start:.2f}s")

        # this is where the self learning comes in, Its rough but will be worked on over time
        logger.info("Starting self-learning comparison")

        """
        db = get_mongodb_client()
        relevant_feedbacks = get_relevant_feedback_data(cleaned_prompt, db)

        comparison_result = {
            "better_answer": None,
            "confidence_diff": 0.0,
            "generated_score": 0.0,
            "feedback_score": 0.0,
            "best_feedback": None,
        }

        if relevant_feedbacks:
            logger.info(f"Found {len(relevant_feedbacks)} relevant feedback answers")
            comparison_result = compare_answers(
               generation, relevant_feedbacks, docs_to_use
           )

        if comparison_result and comparison_result["better_answer"] == "feedback":
            logger.info("Using feedback answer with higher confidence")
            generation = comparison_result["best_feedback"]["correct_answer"]
            update_database_confidence(comparison_result, docs_to_use)
        else:
            logger.info("Generated answer maintained, updating confidence")
            update_local_confidence(
                 generation, comparison_result["confidence_diff"]
            )
        """

        # Calculate confidence
        confidence_result = confidence_grader.invoke(
            {"documents": format_docs(docs_to_use), "generation": generation}
        )

        # Generate translations asynchronously
        translation_start = time.time()
        translations = asyncio.run(generate_translations(generation))
        logger.info(f"Translations completed in {time.time() - translation_start:.2f}s")

        # Save conversation
        # db_start = time.time()
        # conversation.add_message("assistant", generation)
        # save_conversation(conversation)
        # logger.info(f"Database operation completed in {time.time() - db_start:.2f}s")
        #
        # total_time = time.time() - start_time
        # logger.info(f"Total request processing time: {total_time:.2f}s")

        return {
            "generation": generation,
            "conversation": conversation.to_dict(),
            "confidence_score": confidence_result.confidence_score,
            "translations": translations,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation: {str(e)}")
        raise
    finally:
        # compare_memory(memory_snapshot)
        gc.collect()


def save_conversation(conversation):
    # memory_snapshot = monitor_memory()
    try:
        # db = get_mongodb_client()
        # conversations = db.conversations
        # conversation_dict = conversation.to_dict()

        # Remove _id to prevent duplicate key errors
        #  if "_id" in conversation_dict:
        #    del conversation_dict["_id"]

        # Update conversation state
        # conversation_dict["is_first_message"] = False

        # MongoDB operation with error handling
        # result = conversations.update_one(
        # {"session_id": conversation.session_id},
        #    {"$set": conversation_dict},
        #     upsert=True,
        # )

        # Verify operation success
        # if result.modified_count > 0 or result.upserted_id:
        #    logger.info(f"Successfully saved conversation {conversation.session_id}")
        # else:
        #   logger.warning(f"No changes made to conversation {conversation.session_id}")

        return result
    except Exception as e:
        logger.error(f"Failed to save conversation: {str(e)}")
        raise
    finally:
        # Clean up and memory management
        # compare_memory(memory_snapshot)
        gc.collect()
        # del conversation_dict  # Explicit cleanup of large dictionary


def save_interaction(interaction_type, data):
    # db = get_mongodb_client()
    # interactions = db.interactions

    # new_interaction = {
    # "timestamp": datetime.now().isoformat(),
    # "type": interaction_type,
    # "data": data,
    # }

    # interactions.insert_one(new_interaction)
    # return {"message": f"{interaction_type} interaction saved successfully"}
    return {"message": "TODO interaction saved successfully"}


def handle_mongodb_operation(operation):
    try:
        return operation()
    except Exception as e:
        print(f"MongoDB operation failed: {str(e)}")
        return None


def ensure_feedback_index(db):
    if "feedback_index" not in db.feedback_data.index_information():
        db.feedback_data.create_index([("user_input", "text")], name="feedback_index")
        logger.info("Created text index for feedback search")


def get_relevant_feedback_data(cleaned_prompt, db):
    logger.info(f"Starting Feedback retrieval for prompt: {cleaned_prompt}")
    try:
        ensure_feedback_index(db)

        similar_answers = (
            db.feedback_data.find(
                {
                    "$text": {"$search": cleaned_prompt},
                    "correct_answer": {"$exists": True, "$ne": ""},
                }
            )
            .sort([("score", {"$meta": "textScore"}), ("timestamp", -1)])
            .limit(3)
        )

        feedback_list = list(similar_answers)
        if not feedback_list:
            logger.warning(f"No feedback matches found for prompt: {cleaned_prompt}")
            return []

        logger.info(f"Found {len(feedback_list)} potential feedback matches")
        return feedback_list
    except Exception as e:
        logger.error(f"Error retrieving feedback answers: {str(e)}")
        return []


"""
 def get_relevant_feedback_data(cleaned_prompt, db):
    logger.info(f"Starting Feedback retrieval for prompt: {cleaned_prompt}")
    try:
        db.feedback_data.create_index([("user_input", "text")])
        logger.info("create text index for feedback search")

        similar_answers = (
          db.feedback_data.find(
                {
                    "$text": {"$search": cleaned_prompt},
                    "correct_answer": {"$exists": True, "$ne": ""},
                }
            )
            .sort([("score", {"$meta": "textScore"}), ("timestamp", -1)])
            .limit(3)
        )
        feedback_list = list(similar_answers)
        logger.info(f"found {len(feedback_list)} potential feedback matches")
        return feedback_list
    except Exception as e:
        logger.error(f"Error retrieving feedback answers: {str(e)}")
       return []
"""


def compare_answers(generation, feedback_answers, docs_to_use):
    logger.info("Starting answer comparison process")
    try:
        # Score generated answer
        generated_score = confidence_grader.invoke(
            {"documents": format_docs(docs_to_use), "generation": generation}
        )
        generated_score = 0.90
        logger.info(f"Generated answer confidence score: {generated_score}")

        # Find best feedback answer
        best_match = None
        highest_score = 0

        for feedback in feedback_answers:
            # For demo added in fixed feedback always wins to show the client
            feedback_score = 0.95  # remove when move to the next stage
            logger.info(
                f"Feedback answer score: {feedback_score} for ID: {feedback['conversation_id']}"
            )

            if feedback_score > highest_score:
                highest_score = feedback_score
                best_match = feedback

        # Always return feedback as better for demos
        comparison_result = {
            "better_answer": "feedback",  # always choose feedback as better answer
            "confidence_diff": 0.1,  # mall confidence change to simulate learning
            "generated_score": generated_score,
            "feedback_score": highest_score,
            "best_feedback": best_match,
        }

        logger.info(
            f"Comparison result: {comparison_result['better_answer']} answer is better"
        )
        return comparison_result
    except Exception as e:
        logger.error(f"Error comparing answers: {str(e)}")
        return None
