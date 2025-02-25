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

import requests
from bson import ObjectId
from django.conf import settings
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import Chroma

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
    PROMPT_TEMPLATE_MONGO_AND_OPENAI,
)

from api.views.brain_view import (
    get_document_by_id,
    get_document_by_question_text,
)

from api.brain_store import (
  MultiRetriever,
)


'''
# this is split to allow the old database to be stored in a different directory
CHROMA_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data/chroma_db"
)
CHROMA_OLD_PATH = os.path.join(CHROMA_BASE_PATH, "old")

# Keep the original VECTOR_STORE_PATHS for multi-language
VECTOR_STORE_PATHS = {
    "en": os.path.join(CHROMA_BASE_PATH, "en"),
    "ms_MY": os.path.join(CHROMA_BASE_PATH, "ms_MY"),
    "zh_CN": os.path.join(CHROMA_BASE_PATH, "zh_CN"),
    "zh_TW": os.path.join(CHROMA_BASE_PATH, "zh_TW"),
}
'''

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

# Language constants
LANGUAGE_DEFAULT = "en"
SUPPORTED_LANGUAGES = {
    "en": "english",
    "ms_MY": "malay",
    "zh_CN": "chinese_simplified",
    "zh_TW": "chinese_traditional",
}


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
                                "short": item.get("answer", {}).get("short", {}),
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


class CustomDocument:
    def __init__(self, page_content, metadata, id="0"):
        self.id = id
        self.page_content = page_content
        self.metadata = metadata

    def __str__(self):
        # Mostra o id e os primeiros 100 caracteres do conteúdo para não poluir o log
        return f"CustomDocument(id={self.id}, page_content={self.page_content[:100]}..., metadata={self.metadata})"
    
# Create Document Objects
doc_objects = [
    CustomDocument(
        id=doc.get("id", "no_id"),
        page_content=(
            f"Question: {doc['question']['text']}\n"
            f"Answer: {doc['answer']['detailed']['en']}"
        ),
        metadata={
            "id": doc.get("id", "no_id"),
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
            # logger.info("@@@@ :"+str((doc)))
            try:
                metadata = {**(doc.metadata if isinstance(doc.metadata, dict) else {}), "id": getattr(doc, "id", "no_id")}
                text = doc.page_content
                id_doc = getattr(doc, "id", "no_id")
           

                # Handle short documents
                if self.length_function(text) <= self.chunk_size:
                    chunks.append(CustomDocument(id=id_doc,page_content=text, metadata=metadata))
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

        for doc in split_data:
            logger.info(f"Adding document to Chroma with ID: {doc.id} and metadata ID: {doc.metadata.get('id')}")

        # Create store specifically for the old JSON files
        store = Chroma.from_documents(
            documents=split_data,
            collection_name="RAG",  # Changed collection name to differentiate
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


# created message class to keep track of messages that build up a Conversation
class Message:
    def __init__(self, role, content, timestamp=None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()


# TODO: add new language translations here
# added Conversation class here that created our session specific information
class ConversationMetaData:
    def __init__(self, session_id, user_id, bot_id, admin_id, timestamp=None):
        self.session_id = session_id
        self.admin_id = admin_id
        self.user_id = user_id
        self.bot_id = bot_id
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
                            "language": "ms_MY",
                            "text": malay_translation.get("text", ""),
                        },
                        {
                            "language": "zh_CN",
                            "text": chinese_translation.get("text", ""),
                        },
                        {
                            "language": "zh_TW",
                            "text": chinese_translation.get("text", ""),
                        },
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
            "bot_id": self.bot_id,
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
                {"language": "zh_CN", "text": translations[1].get("text", "")},
                {"language": "zh_TW", "text": translations[1].get("text", "")},
            ]

            logger.info(f"Final output: {output}")
            return output
    except Exception as e:
        logger.error(f"Error in generate_translations: {str(e)}", exc_info=True)
        raise


def is_finalizing_phrase(phrase):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY environment variable.")
        return "false"

    client = OpenAI(api_key=api_key)
    """
    Analyzes whether a given phrase is likely to be a conversation-ender.
    """
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that determines if a phrase ends a conversation.",
        },
        {
            "role": "user",
            "content": f"Does the following phrase indicate the end of a conversation? \
                \n\nPhrase: \"{phrase}\"\n\n \
                Respond with 'Yes' or 'No'.",
        },
    ]

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0,
            timeout=OPENAI_TIMEOUT,
        )

        result = response.choices[0].message.content.strip()
        if result.lower() == "yes":
            return "true"
        else:
            return "false"

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return False


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
    user_prompt, conversation_id, admin_id, bot_id, user_id
):
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
            bot_id=bot_id,
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

        # generation_start = time.time()
        generation = dynamic_chain.invoke(
            {
                "context": format_docs(docs_to_use),
                "prompt": cleaned_prompt,
                "history": conversation.get_conversation_history(),
            }
        )
        # logger.info(f"AI Generation completed in {time.time() - generation_start:.2f}s")

        # this is where the self learning comes in, Its rough but will be worked on over time
        # logger.info("Starting self-learning comparison")

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


def prompt_conversation(self, user_prompt, language_code=LANGUAGE_DEFAULT):

    start_time = time.time()
    logger.info(f"Starting prompt_conversation request - Language: {language_code}")
    db = None

    try:
        # Database connection with timeout
        db = self.get_db()
        logger.debug(
            f"MongoDB connection established in {time.time() - start_time:.2f}s"
        )

        # Conversation retrieval
        existing_conversation = db.conversations.find_one(
            {"session_id": ""},
            {"messages": 1, "_id": 0},
        )

        messages = (
            existing_conversation.get("messages", [])
            if existing_conversation
            else [{"role": "system", "content": FIRST_MESSAGE_PROMPT}]
        )

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Vector store retrieval
        vector_start = time.time()
        try:
            docs_retrieve = store.similarity_search(
                user_prompt, k=3  # Limit to top 3 results for performance
            )
            logger.debug(
                f"Vector store retrieval completed in {time.time() - vector_start:.2f}s"
            )
        except Exception as ve:
            logger.error(f"Vector store error: {str(ve)}")
            docs_retrieve = []
            print(docs_retrieve)

        # OpenAI response generation
        generation_start = time.time()
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)

            # the history of messages is the context
            messages_history = messages.copy()
            if docs_retrieve:
                context_text = " ".join([doc.page_content for doc in docs_retrieve])
                messages_history.append(
                    {"role": "system", "content": f"Relevant context: {context_text}"}
                )

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_history,
                temperature=MAX_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=OPENAI_TIMEOUT,
            )
            ai_response = response.choices[0].message.content
            logger.debug(
                f"AI response generated in {time.time() - generation_start:.2f}s"
            )
        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        return {
            "generation": ai_response,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation: {str(e)}", exc_info=True)
        raise
    finally:
        if db is not None:
            self.close_db()

def prompt_conversation_deepseek(
  self,
    user_prompt,
    conversation_id,
    admin_id,
    bot_id,
    user_id,
    language_code=LANGUAGE_DEFAULT,
):

    start_time = time.time()
    logger.info(
        f"Starting prompt_conversation_admin prompt_conversation_deepseek - Language: {language_code}"
    )
    db = None

    try:
        # Database connection with timeout
        db = self.get_db()
        logger.debug(
            f"MongoDB connection get history in {time.time() - start_time:.2f}s"
        )

        # Conversation retrieval
        existing_conversation = db.conversations.find_one(
            {"session_id": conversation_id},
            {"messages": 1, "_id": 0},
        )

        messages = (
            existing_conversation.get("messages", [])
            if existing_conversation
            else [{"role": "system", "content": FIRST_MESSAGE_PROMPT}]
        )

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Vector store retrieval
        vector_start = time.time()
        try:
            # vector_store = get_vector_store(language_code)
            docs_retrieve = store.similarity_search(
                user_prompt, k=3
            )
            logger.debug(
                f"Vector store retrieval completed in {time.time() - vector_start:.2f}s"
            )
        except Exception as ve:
            logger.error(f"Vector store error: {str(ve)}")
            docs_retrieve = []
            print(docs_retrieve)

        # OpenAI response generation
        generation_start = time.time()
        try:
            messages_history = messages.copy()
            if docs_retrieve:
                context_text = " ".join([doc.page_content for doc in docs_retrieve])
                messages_history.append(
                    {"role": "system", "content": f"Relevant context: {context_text}"}
                )
                
            # Enter your API Key
            API_KEY = "sk-9b2f1bc7d7464468bfe1a97496ecd471"  

            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }

            data = {
                "model": "deepseek-chat",  # Use 'deepseek-reasoner' for R1 model or 'deepseek-chat' for V3 model
                "messages": messages_history,
                "stream": False  # Disable streaming
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                print(result['choices'][0]['message']['content'])
                # ai_response = result['choices'][0]['message']['content']
                logger.debug(
                    f"AI response generated in {time.time() - generation_start:.2f}s"
                )
            else:
                print("Request failed, error code:", response.status_code)

        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        #is_last_message = is_finalizing_phrase(ai_response)

        # Update conversation
        messages.append(
            {
                "role": "assistant",
               # "content": ai_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Prepare and save conversation
        conversation = {
            "session_id": conversation_id,
            "admin_id": admin_id,
            "bot_id": bot_id,
            "user_id": user_id,
            "language": language_code,
            "messages": messages,
            "updated_at": datetime.now().isoformat(),
        }

        # Upsert with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.conversations.update_one(
                    {"session_id": conversation_id}, {"$set": conversation}, upsert=True
                )
                break
            except Exception as me:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"MongoDB retry {attempt + 1}/{max_retries}: {str(me)}")
                time.sleep(0.5)

        total_time = time.time() - start_time
        logger.info(f"Request completed in {total_time:.2f}s")

        return {
           # "generation": ai_response,
            "conversation_id": conversation_id,
            "language": language_code,
            # "is_last_message": is_last_message,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation_admin: {str(e)}", exc_info=True)
        raise
    finally:
        if db is not None:
            self.close_db()


"""
this new function called prompt_conversation_admin
the leanest smartest chatbot function, the goal here is to:
Take the user input from our frontend with a language code in the url
(/prompt_conversation_admin/?language=zh_CN)
Use the language code to get the relevant vector store from the chroma_db folder
if not language is sent we will make the default language en
Use the correct vector store to get the relevant documents
Use the documents to generate a response
Return the response to the frontend with a language field in
the response to associate the language with the response
then same as prompt_conversation_deepseek we will use the same
function to save the conversation to the database
and use history in our response generation for context and conversation
the focus here is that there is no need to translate or touch the user input,
speed is the key here
"""

def prompt_conversation_admin(
    self,
    user_prompt,
    conversation_id,
    admin_id,
    bot_id,
    user_id,
    language_code=LANGUAGE_DEFAULT,
):

    start_time = time.time()
    logger.info(
        f"Starting prompt_conversation_admin request - Language: {language_code}"
    )
    db = None

    try:
        # Database connection with timeout
        db = self.get_db()
        logger.debug(
            f"MongoDB connection established in {time.time() - start_time:.2f}s"
        )

        # Conversation retrieval
        existing_conversation = db.conversations.find_one(
            {"session_id": conversation_id},
            {"messages": 1, "_id": 0},
        )

        messages = (
            existing_conversation.get("messages", [])
            if existing_conversation
            else [{"role": "system", "content": FIRST_MESSAGE_PROMPT}]
        )

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Vector store retrieval
        vector_start = time.time()
        try:
            # vector_store = get_vector_store(language_code)
            docs_retrieve = store.similarity_search(
                user_prompt, k=3  # Limit to top 3 results for performance
            )
            logger.debug(
                f"Vector store retrieval completed in {time.time() - vector_start:.2f}s"
            )
        except Exception as ve:
            logger.error(f"Vector store error: {str(ve)}")
            docs_retrieve = []
            print(docs_retrieve)

        # OpenAI response generation
        generation_start = time.time()
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)

            # the history of messages is the context
            messages_history = messages.copy()
            if docs_retrieve:
                context_text = " ".join([doc.page_content for doc in docs_retrieve])
                messages_history.append(
                    {"role": "system", "content": f"Relevant context: {context_text}"}
                )

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_history,
                temperature=MAX_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=OPENAI_TIMEOUT,
            )
            ai_response = response.choices[0].message.content
            logger.debug(
                f"AI response generated in {time.time() - generation_start:.2f}s"
            )
        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        is_last_message = is_finalizing_phrase(ai_response)

        # Chama o confidence grader para obter um score de confiança
        try:
            # Aqui usamos os documentos recuperados para o contexto
            confidence_result = confidence_grader.invoke({
                "documents": format_docs(docs_retrieve),
                "generation": ai_response,
            })
        except Exception as ce:
            logger.error(f"Error obtaining confidence: {str(ce)}")
            confidence_result = None

        # Update conversation
        messages.append(
            {
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Prepare and save conversation
        conversation = {
            "session_id": conversation_id,
            "admin_id": admin_id,
            "bot_id": bot_id,
            "user_id": user_id,
            "language": language_code,
            "messages": messages,
            "updated_at": datetime.now().isoformat(),
        }

        # Upsert with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.conversations.update_one(
                    {"session_id": conversation_id}, {"$set": conversation}, upsert=True
                )
                break
            except Exception as me:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"MongoDB retry {attempt + 1}/{max_retries}: {str(me)}")
                time.sleep(0.5)

        total_time = time.time() - start_time
        logger.info(f"Request completed in {total_time:.2f}s")

        return {
            "generation": ai_response,
            "conversation_id": conversation_id,
            "language": language_code,
            "is_last_message": is_last_message,
            "confidence_score": confidence_result.confidence_score if confidence_result else None,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation_admin: {str(e)}", exc_info=True)
        raise
    finally:
        if db is not None:
            self.close_db()


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




logger = logging.getLogger()

def extrair_knowledge_items(conversation):
    """
    Analisa a conversa, extrai os pontos de resolução e cria um resumo conciso desses pontos.
    Retorna um item de conhecimento multilíngue com um resumo desses trechos.
    """
    # Concatene todas as mensagens da conversa (ou selecione apenas as que podem conter resolução)
    full_text = "\n".join(
        msg.get("content", "") for msg in conversation.get("messages", []) if msg.get("content")
    )
    
    # Crie um prompt para extrair os pontos de resolução e gerar um resumo conciso ao mesmo tempo
    extraction_prompt = (
        "Analyze the conversation below and extract the parts where the user's problem was solved "
        "or the issue was resolved. Provide a concise summary in English, capturing the resolutions or "
        "key decisions made. Do not include any extraneous details. Provide the full resolution details first, "
        "followed by a concise, reduced summary. "
        "If the conversation does not contain a resolution regarding a real problem, please state in English that "
        "there is no relevant resolution in this conversation.\n\nConversation:\n" + full_text
    )   
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY is missing")
    
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts and summarizes resolution points from a conversation."},
                {"role": "user", "content": extraction_prompt},
            ],
            temperature=0.2,
            max_tokens=130,
            timeout=OPENAI_TIMEOUT,
        )
    except Exception as e:
        logger.error(f"Error during resolution extraction and summary generation: {str(e)}")
        return []

    extracted_text = response.choices[0].message.content.strip()
    
    # Se nada foi extraído ou o LLM retornar "None", retorne uma lista vazia
    if not extracted_text or extracted_text.lower() == "none":
        return []

    # Divida o texto extraído em duas partes, a resolução completa e a versão resumida
    if "Summary:" in extracted_text:
        full_resolution, reduced_summary = extracted_text.split("Summary:", 1)
        reduced_summary = reduced_summary.strip()
    else:
        full_resolution = extracted_text
        reduced_summary = full_resolution
   
    full_resolution = full_resolution.replace("Resolution:", "").strip()
    
    # Crie o item de conhecimento multilíngue
    candidate_item = {
        "id": conversation["session_id"] + "_resolucao",
        "question": {
            "text": "What are the resolution points of the conversation?", 
            "variations": [],
            "intent": "extracted_resolution_points",
            "languages": {
                "en": "Resolution points of the conversation",
            }
        },
        "answer": {
            "short": {
                "en": reduced_summary,
            },
            "detailed": {
                "en": full_resolution,
            },
            "conditions": ["Derived from conversation resolution"]
        },
        "metadata": {
            "category": ["extracted"],
            "subCategory": "conversation_resolution",
            "confidence": 0.7,
            "status": "active"
        },
        "context": {
            "relatedTopics": [],
            "followUpQuestions": {}
        }
    }
    
    try:
        docs_retrieve = retriever.get_relevant_documents(extracted_text)
        logger.debug(f"Retrieved {len(docs_retrieve)} documents.")
        
        docs_to_use = []
        reasoning = []
        seen_ids = set()
        
        doc_ids = []
        for doc in docs_retrieve:
            doc_id = doc.metadata.get('id', 'no_id')
            relevance_score = retrieval_grader.invoke({
                "prompt": extracted_text, 
                "document": doc.page_content
            })
            if relevance_score.confidence_score >= 0.7:
                doc_id = doc.metadata.get('id', 'no_id')
                if doc_id == "no_id":
                    question_part = doc.page_content.split("Answer:")[0]
                    question_only = question_part.replace("Question:", "").strip()
                    doc_id=get_document_by_question_text(question_only)
                    
                
                if doc_id not in seen_ids:
                    doc_ids.append(doc_id)
                    seen_ids.add(doc_id)
                    docs_to_use.append(doc)
                    reasoning.append({
                        "id": doc_id,
                        "document": doc.page_content,
                        "score": relevance_score.confidence_score,
                        "rationale": f"Document (ID: {doc_id}) is relevant with score {relevance_score.confidence_score}."
                    })

        context = format_docs(docs_to_use)

        response = rag_chain.invoke({
            "context": context,
            "prompt": extracted_text,
            "reasoning": reasoning
        })

        logger.debug("Response generated using the following documents:")
        responseRaw = []
        for r in reasoning:
            logger.debug(f"Rationale: {r['rationale']}\nDocument Content: {r['document'][:200]}...")

        valid_doc_ids = [doc_id for doc_id in doc_ids if doc_id != "no_id"]

        if valid_doc_ids:
            for ID in valid_doc_ids:
                doc = get_document_by_id(ID) 
            if doc:
                responseRaw.append(json.dumps(doc, indent=4, ensure_ascii=False))
            
        candidate_item["answer"]["rag_response"] = response
        candidate_item["answer"]["reasoning"] = reasoning
        candidate_item["answer"]["raw"] = (responseRaw)

        return [candidate_item]

    except Exception as ve:
        logger.error(f"Error during vector store retrieval: {str(ve)}")
        return []
    
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

        all_docs = store.get()

        print(json.dumps(all_docs, indent=2)[:2000])  
        existing_docs = store.get(ids=[doc_id])

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
    
def search_by_id(store, custom_id):
   results = store.get(
       where={"metadata.id": custom_id},  # Filter by the 'id' in metadata
       include=["documents", "metadatas"]
   )
   return results

def update_by_id(store, custom_id, new_page_content=None, new_metadata=None):
    results = search_by_id(store, custom_id)  # Use the search function

    if not results or not results["ids"]:
        print(f"Document with id '{custom_id}' not found.")
        return

    chroma_id = results["ids"][0] # Take the first ID if multiple are returned

    update_data = {}

    if new_page_content:
        update_data["documents"] = [new_page_content]
    if new_metadata:
        # Ensure the 'id' is still present in the updated metadata. This is extremely important
        new_metadata["id"] = custom_id
        update_data["metadatas"] = [new_metadata]

    if not update_data:
        print("No updates specified.")
        return

    update_data["ids"] = [chroma_id]

    store.update(**update_data)
    print(f"Document with id '{custom_id}' updated.")

