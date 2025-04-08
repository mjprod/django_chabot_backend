import gc
import json
import logging
import os
import time
import tracemalloc
import re

from typing import List

from django.conf import settings
from dotenv import load_dotenv

# from langchain.embeddings import CohereEmbeddings
from langchain_cohere import CohereEmbeddings
# from langchain.vectorstores import Chroma
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
    PROMPT_TEMPLATE_MONGO_AND_OPENAI,
)

from api.views.brain_file_reader import (
    get_document_by_id,
    get_document_by_question_text,
    update_answer_detailed,
    insert_new_document,
    get_next_id_from_json
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
        "database_part_4.json",
        "database_part_5.json",
        "database_part_6.json",
        "database_part_7.json",
        "database_part_8.json",
        "database_part_9.json",
        "database_part_10.json",
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
        print("✅ Banco já existe!")
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
        "database_part_10.json",
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
        "database_part_10.json",
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
    
    if not extracted_text or extracted_text.lower() == "none":
        return []

    if "Summary:" in extracted_text:
        full_resolution, reduced_summary = extracted_text.split("Summary:", 1)
        reduced_summary = reduced_summary.strip()
    else:
        full_resolution = extracted_text
        reduced_summary = full_resolution
   
    full_resolution = full_resolution.replace("Resolution:", "").strip()
    
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
           # "short": {
            #    "en": reduced_summary,
            # },
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
                "id": doc.get("id", ""),
                "category": ",".join(existing_metadata.get("category", [])),
                "subCategory": existing_metadata.get("subCategory", ""),
                "difficulty": existing_metadata.get("difficulty", 0),
                "confidence": existing_metadata.get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "variations": ", ".join(doc["question"].get("variations", [])),
                "conditions": ", ".join(doc["answer"].get("conditions", [])),
            },
        )

        store.add(documents=[new_document])
        return (f"ID '{custom_id}' updated ")
    except Exception as e:
        print(f"Error to update document: {str(e)}")

def reload_vector_store(collection_name="RAG", persist_directory="./chroma_db", embedding_model=None):
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
         
def insert_document(question_text, answer_en: str, answer_ms: str, answer_cn: str):
    try:
        
        new_id = get_next_id_from_json()
        if not new_id:
            return "Error obtaining the next ID."
    
        new_document = {
            "id": new_id,
            "question": {
            "text": question_text,
            "variations": [],
            "intent": "general_inquiry",
            "languages": {
                "en": "",
                "ms": "",
                "cn": ""
            }
        },
        "answer": {
            "detailed": {
                "en": answer_en,
                "ms": answer_ms,
                "cn": answer_cn
            },
            "conditions": []
        },
        "metadata": {
            "category": ["general"],
            "subCategory": "general_inquiry",
            "difficulty": 0,
            "confidence": 0.5,
            "dateCreated": "",
            "lastUpdated": "",
            "version": "1.0",
            "source": "",
            "status": "active"
        },
        "context": {
            "relatedTopics": [],
            "prerequisites": [],
            "followUpQuestions": {
                "en": [],
                "ms": [],
                "cn": []
            }
        },
        "usage": {
            "searchFrequency": 0,
            "successRate": 0,
            "lastQueried": None
        },
        "review_status": []
        }

        insert_new_document(new_document)

        new_document = CustomDocument(
            id=new_id,
            page_content=(
                f"Question: {question_text}\n"
                f"Answer: {answer_en}"
            ),
            metadata={
                "id": new_id,
                "category": ",".join(["general"]),
                "subCategory": "general_inquiry",
                "difficulty":  0,
                "confidence": 0.5,
                "intent": "general_inquiry",
                "variations": ",".join(["general"]),
                "conditions": ",".join(["general"])
            },
        )

        store.add_documents(documents=[new_document])
        store.persist()
        return (f"ID '{new_id}' updated ")
    

        #store.add(documents=[new_document])
        #store.add_documents(documents=[new_document])
       # 

        #collection_name="RAG",
        #embedding=embedding_model,
        #persist_directory="./chroma_db",
        
        #store = Chroma(
         #   collection_name=collection_name,
          #  persist_directory=persist_directory,
           # embedding_function=embedding
        #)

        #return (f"ID '{new_id}' updated ")
    except Exception as e:
        print(f"Error to update document: {str(e)}")

        
