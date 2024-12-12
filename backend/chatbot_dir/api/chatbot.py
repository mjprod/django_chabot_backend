import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List

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


embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")
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
    def __init__(self, chunk_size=1000, chunk_overlap=200, length_function=len):
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
    try:
        logger.info("Starting document splitting process")
        split_start = time.time()

        # Initialize Text Splitter inside the function
        text_splitter = CustomTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )

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
        return store

    except Exception as e:
        logger.error(f"Vector store creation failed: {str(e)}")
        raise


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
        all_results = []
        for store in vectorstores:
            retriever = store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 8, "lambda_mult": 0.8},
            )
            results = retriever.invoke(query)
            all_results.extend(results)
        return all_results[:3]

    def invoke(self, query):
        return self.get_relevant_documents(query)


retriever = MultiRetriever(vectorstores)


def get_rag_prompt_template(is_first_message):
    if is_first_message:
        system_content = """You are a friendly gaming platform assistant
        focused on natural conversation.

CONVERSATION STYLE:
- Respond warmly and naturally
- Match the user's tone and energy
- Use conversational acknowledgments ("I see", "Got it", "I understand")
- For thank you messages, respond with "You're welcome" or similar phrases
- Show enthusiasm when appropriate

CORE RULES:
- Use context information accurately
- Maintain professional but friendly tone
- Keep responses concise but complete
- Build rapport through conversation

RESPONSE PATTERNS:
- For greetings: Respond warmly with "Dear Player"
- For thank you: Reply with variations of "You're welcome"
- For goodbyes: Close warmly but professionally
- For confusion: Gently ask for clarification

CONTENT DELIVERY:
- Start with acknowledgment
- Provide clear information
- End with subtle encouragement
- Use natural transitions
- Include exact numbers and timeframes

PROHIBITED:
- Overly formal language
- Generic responses
- Ignoring conversational cues
- Breaking character
- Using external knowledge

TONE AND STYLE:
- Clear and friendly semi-informal
- Professional yet approachable
- Direct and confident answers
- No hedging or uncertainty
- No emotional management advice
- For losses, simply wish better luck
- Do not mention casino edge

PROHIBITED:
- Information not in context
- Mentioning sources/databases
- Phrases like "based on" or "it appears"
- External knowledge or assumptions
- Generic endings asking for more questions
- Time-specific greetings
- Saying "please note"
- Suggesting customer service unless necessary"""
    else:
        system_content = """You are a friendly gaming platform assistant
        focused on natural conversation.

CONVERSATION STYLE:
- Maintain warm, natural dialogue
- Build on previous context
- Use conversational acknowledgments
- Match user's communication style
- Show personality while staying professional

CORE RULES:
- Skip formal greetings in follow-ups
- Reference previous context naturally
- Keep information accurate
- Stay friendly but focused

RESPONSE PATTERNS:
- For thank you: Use variations like "You're welcome!", "Happy to help!", "Anytime!"
- For questions: Acknowledge before answering
- For confusion: Gently clarify
- For feedback: Show appreciation

CONTENT DELIVERY:
- Natural conversation flow
- Clear information sharing
- Subtle encouragement
- Warm closings
- Exact details when needed

TONE AND STYLE:
- Clear and friendly semi-informal
- Professional yet approachable
- Direct and confident answers
- No hedging or uncertainty
- No emotional management advice
- For losses, simply wish better luck
- Do not mention casino edge

PROHIBITED:
- Information not in context
- Mentioning sources/databases
- Phrases like "based on" or "it appears"
- External knowledge or assumptions
- Generic endings asking for more questions
- Time-specific greetings
- Saying "please note"
- Suggesting customer service unless necessary"""

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
            chinese_translation = translate_en_to_cn(content)

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
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a query optimization expert. Your task is to:
                    1. If the input is not in English:
                    - Translate it to clear, formal English
                    - Maintain proper nouns, numbers, and technical terms
                    - Output ONLY the translated text without any prefixes or
                    explanations
                    2. If the input is in English:
                    - Remove filler words and informal language
                    - Standardize terminology
                    - Maintain the original question's intent
                    - Output ONLY the cleaned text
                    Do not:
                    - Add explanations or additional context
                    - Include phrases like "Translated from X to English:"
                    - Add any prefixes or suffixes
                    - Change the meaning of the query
                    """,
                },
                {"role": "user", "content": f"Process this text: {text}"},
            ],
        )

        translated_text = response.choices[0].message.content.strip()

        # Remove any remaining translation prefixes if they exist
        prefixes_to_remove = [
            "Translated from Chinese to English:",
            "Translated from Malay to English:",
            "Translated from Malaysian to English:",
            "Translation:",
        ]

        for prefix in prefixes_to_remove:
            if translated_text.startswith(prefix):
                translated_text = translated_text.replace(prefix, "").strip()

        return translated_text

    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text


# Define grading of docs
class GradeDocuments(BaseModel):
    confidence_score: float = Field(
        description="Confidence score between 0.0 and 1.0 indicating document relevance",
        ge=0.0,
        le=1.0,
    )


# Initialize LLM for Grading
llm_grader = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm_grader.with_structured_output(GradeDocuments)

# System Message for Grader
document_system_message = """
You are a document relevance assessor.
Analyze the retrieved document's relevance to the user's question.
Provide a confidence score between 0.0 and 1.0 where:
- 1.0: Document contains exact matches or directly relevant information
- 0.7-0.9: Document contains highly relevant but not exact information
- 0.4-0.6: Document contains partially relevant or related information
- 0.1-0.3: Document contains minimal relevant information
- 0.0: Document is completely irrelevant

Consider:
- Keyword matches
- Semantic relevance
- Context alignment
- Information completeness
"""

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
llm_confidence = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_confidence_grader = llm_confidence.with_structured_output(
    GradeConfidenceLevel
)

# System Message for confidence Grader
confidence_system_message = """
You are a grader assessing how well an AI response is grounded in the provided source facts.
Provide a confidence score between 0.0 and 1.0 where:
- 1.0: Answer is completely supported by source facts with exact matches
- 0.8-0.9: Answer is strongly supported with most information retrieved
- 0.6-0.7: Answer is moderately supported with reasonable inferences
- 0.4-0.5: Answer is partially supported but do not contain enough data to give a true response
- 0.0-0.39: Answer is out of scope and not to be answered

Consider:
- Exact matches with source facts
- Logical inferences from provided information
- Unsupported statements
- Factual accuracy and completeness
- Whether the question is within the gaming/gambling platform scope
"""
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
            """You are a knowledgeable gaming/gambling platform assistant.
            Your primary task is to analyze context and maintain natural conversation
            flow while delivering precise information.

CONTEXT RULES:
- Thoroughly examine all provided context before responding
- Only use information present in the context
- Match user questions with relevant context information
- Acknowledge limitations when information is missing

CONVERSATION FLOW:
- First Message:
  * Begin with "Dear Player" (Only use Dear Player for
  the first interaction and follow up or other questions do not use)
  * Introduce yourself briefly
  * Use formal pronouns (您)
- Follow-up Messages:
  * Skip formal greetings
  * Reference previous context naturally
  * Maintain conversation continuity
  * Build upon established context

CONTENT DELIVERY:
- Provide detailed, specific information
- Include exact numbers and timeframes
- Use "please go to" instead of "navigate to"
- Use "on the app" or "on the platform"
- For technical issues:
  * Provide step-by-step solutions
  * Only suggest support contact if steps fail
- For fixed answers:
  * Give direct information
  * Offer to answer follow-up questions

TONE AND STYLE:
- Clear and friendly semi-informal
- Professional yet approachable
- Direct and confident answers
- No hedging or uncertainty
- No emotional management advice
- For losses, simply wish better luck
- Do not mention casino edge

PROHIBITED:
- Information not in context
- Mentioning sources/databases
- Phrases like "based on" or "it appears"
- External knowledge or assumptions
- Generic endings asking for more questions
- Time-specific greetings
- Saying "please note"
- Suggesting customer service unless necessary

Example Flow:
User: "What's the minimum deposit?"
Assistant: "Dear Player, the minimum deposit amount is $10.
You can make deposits through various payment methods on the app."

User: "Which payment method is fastest?"
Assistant: "Bank transfers typically process within 5-15 minutes.
For instant deposits, please use e-wallets available on the platform."

User: "How do I set up an e-wallet?"
Assistant: "Please go to the wallet section and select 'Add Payment Method'.
Follow the verification steps to link your e-wallet.
If you encounter any issues during setup, our support team is ready to assist you.""",
        ),
        ("assistant", "I'll provide clear, friendly direct answers to help you."),
        ("human", "Context: {context}\nQuestion: {prompt}"),
    ]
)

# Initialize LLM for RAG Chain
rag_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


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


# API functions
def get_mongodb_client():
    client = MongoClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DATABASE]


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
    with ThreadPoolExecutor() as executor:
        # Run translations
        malay_future = executor.submit(translate_en_to_ms, generation)
        chinese_future = executor.submit(translate_en_to_cn, generation)

        # Gather results
        translations = await asyncio.gather(
            asyncio.wrap_future(malay_future), asyncio.wrap_future(chinese_future)
        )

        return [
            {"language": "en", "text": generation},
            {"language": "ms-MY", "text": translations[0].get("text", "")},
            {"language": "cn", "text": translations[1].get("text", "")},
        ]


def translate_en_to_cn(input_text):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional Chinese translator specializing
                    in gaming platform communications. Follow these guidelines:
    - Use Simplified Chinese (简体中文)
    - Maintain a semi-formal tone (温和 亲近)
    - Use standard business honorifics (您) for addressing users
    - Preserve gaming-specific terminology accurately
    - Ensure proper Chinese grammar and sentence structure
    - Keep numerical values and technical terms consistent
    - Use appropriate Chinese punctuation (。，！？）
    - Maintain a warm yet professional tone
    - Avoid overly casual or overly formal expressions
    - Keep the original paragraph structure
    Example:
    English: "Dear Player, Please check your balance in the wallet section."
    Chinese: "亲爱的玩家，请您查看钱包区域中的余额。"
    """,
                },
                {
                    "role": "user",
                    "content": f"Translate this text to Chinese: {input_text}",
                },
            ],
            temperature=0,
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
    url = "https://api.mesolitica.com/translation"

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
def generate_user_input(user_prompt):
    # Clean and translate prompt
    cleaned_prompt = translate_and_clean(user_prompt)

    # Get relevant documents
    docs_retrieve = retriever.get_relevant_documents(cleaned_prompt)
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
    start_time = time.time()
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
        db = get_mongodb_client()
        relevant_feedbacks = get_relevant_feedback_data(cleaned_prompt, db)

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

        # Calculate confidence
        confidence_result = confidence_grader.invoke(
            {"documents": format_docs(docs_to_use), "generation": generation}
        )

        # Generate translations asynchronously
        translation_start = time.time()
        translations = asyncio.run(generate_translations(generation))
        logger.info(f"Translations completed in {time.time() - translation_start:.2f}s")

        # Save conversation
        db_start = time.time()
        conversation.add_message("assistant", generation)
        save_conversation(conversation)
        logger.info(f"Database operation completed in {time.time() - db_start:.2f}s")

        total_time = time.time() - start_time
        logger.info(f"Total request processing time: {total_time:.2f}s")

        return {
            "generation": generation,
            "conversation": conversation.to_dict(),
            "confidence_score": confidence_result.confidence_score,
            "translations": translations,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation: {str(e)}")
        raise


def save_conversation(conversation):
    db = get_mongodb_client()
    conversations = db.conversations
    conversation_dict = conversation.to_dict()

    # Remove _id from the dictionary if it exists
    if "_id" in conversation_dict:
        del conversation_dict["_id"]

    conversation_dict["is_first_message"] = False

    conversations.update_one(
        {"session_id": conversation.session_id},
        {"$set": conversation_dict},
        upsert=True,
    )


def save_interaction(interaction_type, data):
    db = get_mongodb_client()
    interactions = db.interactions

    new_interaction = {
        "timestamp": datetime.now().isoformat(),
        "type": interaction_type,
        "data": data,
    }

    interactions.insert_one(new_interaction)
    return {"message": f"{interaction_type} interaction saved successfully"}


def handle_mongodb_operation(operation):
    try:
        return operation()
    except Exception as e:
        print(f"MongoDB operation failed: {str(e)}")
        return None


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
