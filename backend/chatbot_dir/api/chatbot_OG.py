# import ENV
# import standards
import json
import os
from pathlib import Path
from pprint import pprint

# Embedding and LLM imports
import cohere
import jsonify
from dotenv import load_dotenv
from groq import Groq

# Langchain imports
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings

# langchain community imports
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma

# langchain core imports
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.runnables.base import RunnableLambda, RunnableMap, RunnableSequence
from langchain_groq import ChatGroq

# pydantic imports
from pydantic import BaseModel, Field

docs_to_use = []

prompt = ""



# load env
load_dotenv()

# load JSON file
file_path = os.path.abspath("../data/database.json")
data = json.loads(Path(file_path).read_text())

# CohereEmbeddings

embedding_model = CohereEmbeddings(model="embed-english-v3.0")

# document prep
documents = [
    {
        "question": item["Question"],
        "answer": item["Answer"],
        "metadata": item["Metadata"],
    }
    for item in data
]


# create documents class
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


doc_objects = [
    Document(
        page_content=f"Question: {doc["question"]}\nAnswer: {doc["answer"]}",
        metadata=doc["metadata"],
    )
    for doc in documents
]


# class for text splitter
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents):
        chunks = []
        for docs in documents:
            text = docs.page_content
            while len(text) > self.chunk_size:
                chunks = text[: self.chunk_size]
                chunks.append(Document(page_content=text, metadata=doc.metadata))
                text = text[self.chunk_size - self.chunk_overlap :]
            if text:
                chunks.append(Document(page_content=text, metadata=docs.metadata))
            return chunks


# text splitting
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
split_data = text_splitter.split_documents(doc_objects)


# Create vectorestore
vectorstore = Chroma.from_documents(
    documents=split_data,
    collection_name="RAG",
    embedding=embedding_model,
)

# create retriever

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},  # K for number of retrievals
)


# user prompt -- > for testing from backend without API
# prompt = input("How can I help today? ")
def generate_answer(user_prompt):
    global prompt, generation, response, docs_to_use
    prompt = user_prompt

    # Retrieve documents
    docs_retrieve = retriever.invoke(prompt)

    # Filter relevant documents
    
    for doc in docs_retrieve:
        res = retrieval_grader.invoke({"prompt": prompt, "document": doc.page_content})
        if res.binary_score == "yes":
            docs_to_use.append(doc)

    # Generate response
    generation = rag_chain.invoke({"documents": format_docs(docs_to_use), "prompt": prompt})

    # Check for hallucinations
    response = hallucination_grader.invoke(
        {"documents": format_docs(docs_to_use), "generation": generation}
    )

    return generation, response.binary_score

# create class for relevance LLM
class GradeDocuments(BaseModel):
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# LLM call function for GradeDocuments
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# Create LLMGrader
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# system message for LLM
system = """
you are a grader assessing relevance of a retrieved document to a user question. \n
if the document contains kerowrd(s) or semantic meaning related to the user question,
grade it as relevant. \n give a binary score 'yes' or 'no' score to indicate weather the
document is relevant to the question.
"""

# grade prompt call
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {prompt}"),
    ]
)

# runnable chain for document grader
retrieval_grader = grade_prompt | structured_llm_grader

#test print for debug
# print("Filtered docuemnts:", len(docs_to_use))


# Create chat LLM function
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.",
        ),
        ("human", "Context: {context}\nquestion: {prompt}"),
    ]
)

# load LLM for conversation
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# formatting our docs
def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)


# create runnable chain
rag_chain = (
    {"context": lambda x: format_docs(docs_to_use), "prompt": RunnablePassthrough()}
    | prompt_template
    | llm
    | StrOutputParser()
)

# generate response
generation = rag_chain.invoke({"docuemnts": format_docs(docs_to_use), "prompt": prompt})
# test print for debug
# print("Generation Result:", generation)


# create Hallucination class
class GradeHallucinations(BaseModel):
    binary_score: str = Field(description="Answer is grounded in facts, 'yes' or 'no'")


# call LLM for GradeHallucinations
llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0)
system = """
You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
    Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts
"""

# call structured_llm_grader and our hallucination prompt
structured_llm_grader = llm.with_structured_output(GradeHallucinations)
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "set of facts: \n\n <facts>{documents}</facts> \n\n LLM generation: <generation>(generation)</generation>",
        ),
    ]
)

# run the chain
hallucination_grader = hallucination_prompt | structured_llm_grader

# produce end response to the user
response = hallucination_grader.invoke(
    {"documents": format_docs(docs_to_use), "generation": generation}
)

# test print
# print("Hallucination Check Result:", response)


# User get feedback function to format to JSON
def get_user_feedback(prompt, response, correct, rating, comments=""):
    return {
        "prompt": prompt,
        "response": response,
        "correct": int(correct),
        "rating": int(rating),
        "comments": comments,
    }


# save JSON data to new Json file
def feedback_store(feedback_data):
    os.makedirs("../data", exist_ok=True)
    with open("../data/database_update.json", "a") as f:
        json.dump(feedback_data, f)
        f.write("\n")


# sumbit feedback function for API post
def submit_feedback():
    data = request.json

    # extract Data
    prompt = data.get("prompt")
    response = data.get("response")
    correct = data.get("correct")
    rating = data.get("rating")
    comments = data.get("comments", "")

    # feedback object
    feedback = get_user_feedback(prompt, response, correct, rating, comments)

    # store feedback
    feedback_store(feedback)

    return jsonify({"message": "Feedback stored successfully"}), 200


def generate_answer(user_prompt):
    global prompt, generation, response
    prompt = user_prompt
