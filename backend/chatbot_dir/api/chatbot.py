import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

import cohere
import requests
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
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field

#
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
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# Initialize LLM for Grading
llm_grader = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm_grader.with_structured_output(GradeDocuments)

# System Message for Grader
system_message = """
You are a grader assessing the relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the user question,
grade it as relevant.
Give a binary score 'yes' or 'no' to indicate whether the
document is relevant to the question.
"""

# Create Grading Prompt
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {prompt}"),
    ]
)

# Runnable Chain for Document Grader
retrieval_grader = grade_prompt | structured_llm_grader


# Define GradeHallucinations Model
class GradeHallucinations(BaseModel):
    binary_score: str = Field(description="Answer is grounded in facts, 'yes' or 'no'")


# Initialize LLM for Hallucination Grading
llm_hallucination = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_hallucination_grader = llm_hallucination.with_structured_output(
    GradeHallucinations
)

# System Message for Hallucination Grader
hallucination_system_message = """
You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.
Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.
"""

# Create Hallucination Grading Prompt
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", hallucination_system_message),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

# Runnable Chain for Hallucination Grader
hallucination_grader = hallucination_prompt | structured_hallucination_grader

# Define Prompt Template for RAG Chain
rag_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a knowledgeable gaming/gambling platform assistant. Your primary task is to thoroughly analyze the provided context and deliver precise, accurate information.

CONTEXT ANALYSIS RULES:
- First, carefully examine all provided context
- Match user questions with relevant context information
- Only use information present in the context
- If information is missing from context, acknowledge the limitation

RESPONSE FORMAT:
- Begin with "Dear Player" or "Dear Boss"
- Use formal pronouns (您) for "you/your"
- Add "please" before first instruction
- Respond only in English
- End procedural answers with "If this hasn't resolved your issue, please contact Our Professional Customer Service team who can assist you further"

CONTENT GUIDELINES:
- Provide detailed, specific information from context
- Include exact numbers and timeframes when available
- Use "on the app" or "on the platform" instead of "our platform"
- Avoid time-specific greetings (use "Day" instead of "Morning/Afternoon")
- For 4D questions, strictly use draw times from context
- For technical issues, provide step-by-step solutions
- For account-related queries, give precise procedures

TONE AND STYLE:
- Clear and friendly semi-informal tone
- Professional yet approachable language
- Direct and confident answers
- No hedging or uncertainty
- No emotional management advice
- For losses, simply wish better luck

PROHIBITED:
- Information not in context
- Mentioning sources/databases
- Phrases like "based on" or "it appears"
- External knowledge or assumptions
- Casino edge mentions
- Suggesting customer service contact unless specifically asked

Example format:
User: "How long does it take for deposits to process?"
Assistant: "Dear Boss, Please allow 5-30 minutes for deposit processing. If funds are not received within 30 minutes, the Professional Customer Service team will assist immediately."
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


def generate_answer(user_prompt):
    global prompt, docs_to_use

    # added in translate and clean prompt
    cleaned_prompt = translate_and_clean(user_prompt)

    # updated prompt to take the output of the cleaned_prompt call
    prompt = cleaned_prompt
    docs_to_use = []

    # Retrieve documents
    docs_retrieve = retriever.get_relevant_documents(prompt)

    # Filter relevant documents
    for doc in docs_retrieve:
        res = retrieval_grader.invoke({"prompt": prompt, "document": doc.page_content})
        if res.binary_score.lower() == "yes":
            docs_to_use.append(doc)

    # Generate response
    generation = rag_chain.invoke(
        {"context": format_docs(docs_to_use), "prompt": prompt}
    )

    # Get Malay translation
    malay_translation = translate_en_to_ms(generation)

    # translate to Mandarin
    chinese_translation = translate_en_to_cn(generation)

    return {
        "generation": generation,
        "translations": [
            {"language": "en", "text": generation},
            {"language": "ms-MY", "text": malay_translation.get("text", "")},
            {"language": "cn", "text": chinese_translation.get("text", "")},
        ],
        "usage": {
            "prompt_tokens": malay_translation.get("prompt_tokens", 0),
            "total_tokens": malay_translation.get("total_tokens", 0),
        },
    }


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


def save_interaction(interaction_type, data):
    file_path = os.path.join(os.path.dirname(__file__), "../data/interactions.json")

    # Initialize empty interactions list
    interactions = []

    # Create the file with empty array if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)
    else:
        # Try to read existing interactions
        try:
            with open(file_path, "r") as f:
                content = f.read()
                if content:  # Only try to load if file is not empty
                    interactions = json.loads(content)
                # If file is empty, keep empty list
        except json.JSONDecodeError:
            # If file is corrupted, start fresh
            interactions = []

    # Create new interaction
    new_interaction = {
        "Date_time": datetime.now().isoformat(),
        "Type": interaction_type,
        "Data": data,
    }

    # Append new interaction
    interactions.append(new_interaction)

    # Write updated interactions back to file
    with open(file_path, "w") as f:
        json.dump(interactions, f, indent=4)

    return {"message": f"{interaction_type} interaction saved successfully"}


# added new function to save the interaction outcomes to a seperate json file here
def save_interaction_outcome(data):
    file_path = os.path.join(
        os.path.dirname(__file__), "../data/interaction_outcome.json"
    )
    outcomes = []

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Create or read existing file
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)
    else:
        try:
            with open(file_path, "r") as f:
                content = f.read()
                if content:
                    outcomes = json.loads(content)
        except json.JSONDecodeError:
            outcomes = []

    formatted_data = {
        "user_id": data.get("user_id", 0),
        "prompt": data.get("prompt"),
        "cleaned_prompt": data.get("cleaned_prompt"),
        "generation": data.get("generation"),
        "translations": data.get("translations", []),
        "correct_bool": data.get("correct_bool"),
        "correct_answer": data.get("correct_answer", ""),
        "chat_rating": data.get("chat_rating"),
    }

    # Append new outcome
    outcomes.append(formatted_data)

    # Write updated outcomes back to file
    with open(file_path, "w") as f:
        json.dump(outcomes, f, indent=4, ensure_ascii=False)

    return {"message": "Interaction outcome saved successfully"}


# Remove or comment out any unused functions
