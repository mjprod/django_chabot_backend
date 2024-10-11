import json
import os
from datetime import datetime
from pathlib import Path

import cohere
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
from pydantic import BaseModel, Field

# Initialize global variables
docs_to_use = []
prompt = ""

# Load environment variables
load_dotenv()

# Load JSON data
file_path = os.path.join(os.path.dirname(__file__), "../data/database.json")
with open(file_path, "r") as f:
    data = json.load(f)

# Initialize Embedding Model
embedding_model = CohereEmbeddings(model="embed-english-v3.0")

# Prepare Documents
documents = [
    {
        "question": item["Question"],
        "answer": item["Answer"],
        "metadata": item["Metadata"],
    }
    for item in data
]


# Custom Document Class to Avoid Conflicts
class CustomDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


# Create Document Objects
doc_objects = [
    CustomDocument(
        page_content=f"Question: {doc['question']}\nAnswer: {doc['answer']}",
        metadata=doc["metadata"],
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

# Create Vector Store
vectorstore = Chroma.from_documents(
    documents=split_data,
    collection_name="RAG",
    embedding=embedding_model,
)

# Create Retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},  # Number of retrievals
)

doc_retrieve = retriever.invoke(prompt)
print("Documents retrieved:", len(doc_retrieve))


# Define GradeDocuments Model
class GradeDocuments(BaseModel):
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# Initialize LLM for Grading
llm_grader = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
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
llm_hallucination = ChatGroq(model="mixtral-8x7b-32768", temperature=0)
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
            "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.",
        ),
        ("human", "Context: {context}\nQuestion: {prompt}"),
    ]
)

# Initialize LLM for RAG Chain
rag_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


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


# Function to Generate Answer
def generate_answer(user_prompt):
    global prompt, generation, response, docs_to_use

    prompt = user_prompt

    # Retrieve documents
    docs_retrieve = retriever.invoke(prompt)

    # Filter relevant documents
    for doc in docs_retrieve:
        res = retrieval_grader.invoke({"prompt": prompt, "document": doc.page_content})
        if res.binary_score.lower() == "yes":
            docs_to_use.append(doc)

    # Generate response
    generation = rag_chain.invoke(
        {"context": format_docs(docs_to_use), "prompt": prompt}
    )

    # Check for hallucinations
    response = hallucination_grader.invoke(
        {"documents": format_docs(docs_to_use), "generation": generation}
    )

    return generation, response.binary_score
    print("Generation result:", generation)
    print("Filtered documents:", len(docs_to_use))


# Feedback Handling Functions
def get_user_feedback(prompt, response, correct, rating, comments=""):
    return {
        "prompt": prompt,
        "response": response,
        "correct": int(correct),
        "rating": int(rating),
        "comments": comments,
    }


def feedback_store(feedback_data):
    os.makedirs("../data", exist_ok=True)
    feedback_file = os.path.join(
        os.path.dirname(__file__), "../data/database_update.json"
    )
    with open(feedback_file, "a") as f:
        json.dump(feedback_data, f)
        f.write("\n")


# capture interaction fucntion


def capture_interaction(
    prompt, response, question_correct, correct_rating, correct_answer, metadata
):
    interaction = {
        "Date_time": datetime.now().isoformat(),
        "Question": prompt,
        "Answer": response,
        "Question_correct": question_correct,
        "Correct_rating": correct_rating,
        "Correct_Answer": correct_answer,
        "Metadata": metadata,
    }

    file_path = os.path.join(os.path.dirname(__file__), "../data/interactions.json")

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)

    with open(file_path, "r+") as f:
        interactions = json.load(f)
        interactions.append(interaction)
        f.seek(0)
        json.dump(interactions, f, indent=4)
        f.truncate()

    return {"message": "Interaction captured successfully"}


# Submit Feedback Function for API Post
def submit_feedback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt")
            response_txt = data.get("response")
            correct = data.get("correct")
            rating = data.get("rating")
            comments = data.get("comments", "")

            if not all([prompt, response_txt, correct, rating]):
                return JsonResponse({"error": "Missing required fields."}, status=400)

            feedback = get_user_feedback(
                prompt, response_txt, correct, rating, comments
            )
            feedback_store(feedback)

            return JsonResponse({"message": "Feedback stored successfully"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)