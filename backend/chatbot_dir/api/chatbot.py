import cProfile
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

import requests
from bson import ObjectId
from django.conf import settings
from dotenv import load_dotenv
from langchain.schema import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field

# mongodb imports
from pymongo import MongoClient

# create out gloabl variables
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

    # create the docutments list
    all_documents = []

    for file_name in database_files:
        file_path = os.path.join(base_dir, file_name)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict):
                        document = {
                            "question": item["question"],
                            "answer": item["answer"],
                            "metadata": item.get("metadata", {}),
                        }
                        all_documents.append(document)
        except FileNotFoundError:
            print(f"Warning: {file_name} - not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {file_name}")
            continue
    return all_documents


class CustomDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")

vectorstores = []

documents = load_and_process_json_file()

# Create Document Objects
# Modify the document creation to flatten metadata
doc_objects = [
    CustomDocument(
        page_content=f"Question: {doc['question']}\nAnswer: {doc['answer']}",
        metadata={
            "category": ",".join(doc["metadata"].get("category", [])),
            "subCategory": doc["metadata"].get("subCategory", ""),
            "difficulty": doc["metadata"].get("difficulty", 0),
            "confidence": doc["metadata"].get("confidence", 0.0),
        },
    )
    for doc in documents
]


# Text Splitter Class
class CustomTextSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents):
        chunks = []
        for doc in documents:
            text = doc.page_content
            while len(text) > self.chunk_size:
                chunk = text[: self.chunk_size]
                chunks.append(CustomDocument(page_content=chunk, metadata=doc.metadata))
                text = text[self.chunk_size - self.chunk_overlap :]
            if text:
                chunks.append(CustomDocument(page_content=text, metadata=doc.metadata))
        return chunks


# Initialize Text Splitter and Split Data
text_splitter = CustomTextSplitter(chunk_size=500, chunk_overlap=100)
split_data = text_splitter.split_documents(doc_objects)

try:
    store = Chroma.from_documents(
        documents=split_data,
        collection_name="RAG",
        embedding=embedding_model,
        persist_directory=f"./chroma_db",
    )

    vectorstores.append(store)
except Exception as e:
    print(f"Error: {e}")


# Changed the retriever to retrieve across all 4 vector stores
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
            results = retriever.get_relevant_documents(query)
            all_results.extend(results)
        return all_results[:3]


retriever = MultiRetriever(vectorstores)


# created message class to keep track of messages that build a Conversation
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

    def add_message(self, role, content):
        message = Message(role, content)
        self.messages.append(message)

        # added in translation layer here
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

    # save the output to a dict for using in API
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
    # load env for api key
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    # generate response
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
   - Output: "Translated from [language] to English: [translated query]"

2. If the input is in English:
   - Remove filler words and informal language
   - Standardize terminology
   - Maintain the original question's intent
   - Output: "[optimized query]"

Do not:
- Add explanations or additional context
- Expand abbreviations unless unclear
- Change the meaning of the query
- Add steps or instructions

Example 1:
Input: "berapa minimum deposit ah?"
Output: "Translated from Malay to English: What is the minimum deposit amount?"

Example 2:
Input: "how do I participate in live casino tournaments?"
Output: "How do I participate in live casino tournaments?"

Example 3:
Input: "yo wassup how do i get my money back from da slots?"
Output: "How do I withdraw money from slot games?"
                """,
            },
            {"role": "user", "content": f"Process this text, {text}"},
        ],
    )
    return response.choices[0].message.content.strip()


# Define GradeDocuments Model
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
You are a document relevance assessor. Analyze the retrieved document's relevance to the user's question.
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
        description="Confidence score between 0.0 and 1.0 indicating how well the answer is grounded in source facts",
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
            """You are a knowledgeable gaming/gambling platform assistant. Your primary task is to thoroughly analyse the provided context and deliver precise, accurate information.
CONTEXT ANALYSIS RULES:  
- First, carefully examine all provided context  
- Match user questions with relevant context information  
- Only use information present in the context  
- If information is missing from context, acknowledge the limitationRESPONSE FORMAT:  
- Begin with "Dear Player" or "Dear Boss"  
- Use formal pronouns (您) for "you/your"  
- Add "please" before first instruction  
- Respond only in English  
- For questions specifically about **procedures** or **steps to resolve an issue**, after providing guidance or instructions include if the problem is still not resolved or you encounter any difficulty follow the instruction, you can reach out through our professional support team, and we’ll ensure you get the help you need.
-   For fixed answers like rules or the location of the feature, instead of asking contact our Professional Customer Service team to further assist you, ask users let me know if you have other questions.
- 
- CONTENT GUIDELINES:  
- Provide detailed, specific information from context  
- Avoid saying please note when answering
- Include exact numbers and timeframes when available  
- Instead of saying "navigate to", say "please go to"
- Use "on the app" or "on the platform" instead of "our platform"  
- Avoid time-specific greetings (use "Day" instead of "Morning/Afternoon")  
- For 4D questions, strictly use draw times from context  
- For technical issues, provide step-by-step solutions  
- For account-related queries, give precise proceduresTONE AND STYLE:  
- Clear and friendly semi-informal tone  
- Professional yet approachable language  
- Direct and confident answers  
- No hedging or uncertainty  
- No emotional management advice  
- For losses, simply wish better luck
- Do not mention casino edge
- PROHIBITED:  
- Information not in context  
- Mentioning sources/databases  
- Phrases like "based on" or "it appears"  
- do not use External knowledge or assumptions  (Only what is within the databases you have access to)
- Suggesting customer service contact unless specifically asked
- 
Example:Questions: 
What games offer the highest RTP (Return to Player) percentage?  
Answers: The winning rate of slot games is actually determined by the game's random mechanisms. Sometimes, you may feel that the chances of winning are decreasing, which is actually a normal fluctuation phenomenon; after all, each spin is an independent random event.

Questions: Is there any issue with the deposit system right now?  
Answers: Our deposit system is currently running normally. Usually, the deposit processing time is 5 to 30 minutes. If you encounter a delay, it may be because the processing time of the network system is slightly extended. If your deposit has not yet arrived after 30 minutes, you can reach out through our professional support team, and we’ll ensure you get the help you need.
""",
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


def translate_en_to_cn(input_text):
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional Chinese translator specializing in gaming platform communications. Follow these guidelines:
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


def translate_en_to_ms(input_text, to_lang="ms", model="small"):
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


# updated generate_answer function to include new classes for chat history
def generate_answer(
    user_prompt, session_id=None, admin_id=None, agent_id=None, user_id=None
):
    # Handle legacy user_input calls (where only user_prompt is provided)
    if session_id is None:
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

        # Generate translations
        malay_translation = translate_en_to_ms(generation)
        chinese_translation = translate_en_to_cn(generation)

        # Return legacy format with translations
        return {
            "generation": generation,
            "translations": [
                {"language": "en", "text": generation},
                {"language": "ms-MY", "text": malay_translation.get("text", "")},
                {"language": "cn", "text": chinese_translation.get("text", "")},
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    # Handle new conversation-based calls
    conversation = ConversationMetaData(
        session_id=session_id,
        admin_id=admin_id,
        agent_id=agent_id,
        user_id=user_id,
    )

    cleaned_prompt = translate_and_clean(user_prompt)
    conversation.add_message("user", user_prompt)

    docs_to_use = []
    docs_retrieve = retriever.get_relevant_documents(cleaned_prompt)

    for doc in docs_retrieve:
        relevance_score = retrieval_grader.invoke(
            {"prompt": cleaned_prompt, "document": doc.page_content}
        )
        if relevance_score.confidence_score >= 0.7:
            docs_to_use.append(doc)

    history = conversation.get_conversation_history()

    generation = rag_chain.invoke(
        {
            "context": format_docs(docs_to_use),
            "prompt": cleaned_prompt,
            "history": history,
        }
    )

    confidence_result = confidence_grader.invoke(
        {"documents": format_docs(docs_to_use), "generation": generation}
    )

    conversation.add_message("assistant", generation)
    save_conversation(conversation)

    return {
        "generation": generation,
        "conversation": conversation.to_dict(),
        "confidence_score": confidence_result.confidence_score,
        "translations": (
            conversation.translations[-1]["translations"]
            if conversation.translations
            else []
        ),
    }


def save_conversation(conversation):
    db = get_mongodb_client()
    conversations = db.conversations
    conversation_dict = conversation.to_dict()

    # Remove _id from the dictionary if it exists
    if "_id" in conversation_dict:
        del conversation_dict["_id"]

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


def save_interaction_outcome(data):
    db = get_mongodb_client()
    outcomes = db.interaction_outcomes

    formatted_data = {
        "user_id": data.get("user_id", 0),
        "prompt": data.get("prompt"),
        "cleaned_prompt": data.get("cleaned_prompt"),
        "generation": data.get("generation"),
        "translations": data.get("translations", []),
        "correct_bool": data.get("correct_bool"),
        "correct_answer": data.get("correct_answer", ""),
        "chat_rating": data.get("chat_rating"),
        "timestamp": datetime.now().isoformat(),
    }

    outcomes.insert_one(formatted_data)
    return {"message": "Interaction outcome saved successfully"}


def submit_feedback(request):
    if request.method == "POST":
        try:
            data = (
                json.loads(request.body)
                if isinstance(request.body, bytes)
                else request.data
            )
            correct_answer = data.get("correct_answer")

            if not correct_answer:
                return JsonResponse(
                    {"error": "Missing required field: correct_answer."}, status=400
                )

            return JsonResponse({"message": "Incorrect answer received"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)


def load_and_process_json_file() -> List[dict]:
    db = get_mongodb_client()
    documents = db.training_documents.find({})

    all_documents = []
    for doc in documents:
        if isinstance(doc, dict):
            document = {
                "question": doc["question"],
                "answer": doc["answer"],
                "metadata": doc.get("metadata", {}),
            }
            all_documents.append(document)

    return all_documents


def handle_mongodb_operation(operation):
    try:
        return operation()
    except Exception as e:
        print(f"MongoDB operation failed: {str(e)}")
        return None


# Remove or comment out any unused functions
