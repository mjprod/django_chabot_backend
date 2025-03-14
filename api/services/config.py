import datetime
import os
import json

from dotenv import load_dotenv

load_dotenv()


# vector store constants
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
CHROMA_BRAIN_COLLECTION="brain"
CHROMA_CONVERSATION_COLLECTION="conversation"
CHROMA_DIR="./chroma"

# chat model constants
CHAT_MODEL="gpt-3.5-turbo"
CHAT_MODEL_PROVIDER="openai"

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENAI_TIMEOUT=30
MAX_TEMPERATURE=0.2
MAX_TOKENS=500

# date threshold
DATE_THRESHOLD=datetime.datetime(2025, 3, 1)

CHATBOT_PROMPT="""
You are a helpful assistant that answers user questions strictly based on the provided retrieved knowledge. 
If the retrieved knowledge is not directly relevant to the question, kindly let the user know that you’re not sure about the answer and explain that you can only help with questions related to this game platform.
"""


# Step 1: Load the JSON files
with open('api/fixtures/categories_fixture.json', 'r') as file:
    category = json.load(file)

with open('api/fixtures/subcategories_fixture.json', 'r') as file:
    subcategory = json.load(file)

# Step 2: Prepare the conversation streaming prompt
CONVERSATION_STREAMING_PROMPT = f"""
Task:

Given a conversation between a user and an agent in JSON format

Analyze the entire conversation transcript to identify user messages and corresponding agent responses. Follow these rules:

***Instruction Rules***

CORE RULES:

- Identify Agent Messages: Messages where IsService == true indicate they are from the agent.
- Use Corrected Responses: If an agent's message has AdminAction == 1 or AdminAction == 2, retrieve the corrected response only from the AdminReply.
- Extract User Questions: Summarize possible user questions based on AdminReply and user messages in the whole conversation context.
- Structure in Q&A Format: Present the extracted user questions and their matched agent responses in a clear Q&A format, ensuring each user message is accurately paired with the correct agent response.
- Maintain Accuracy: The agent's response must remain unchanged in the final output, and do not change the original language it is using
- Assign each Q&A a category id based on \n{json.dumps(category, indent=2)}\n, and a subcategory id based on \n{json.dumps(subcategory, indent=2)}\n. 
- Make sure the subcategory must belong to the assigned category. Category and subcategory should only be assigned with a number! You need to find a number, it is compulsory!
- Assign each Q&A a language id: 1=English, 2=Malaysian, 3=Chinese. You MUST assign an id to the language field.

Return a list of question-answer pairs in the exact following format. Do not use markdown formatting (` ```json `). Just return the raw JSON object.:

[
    {{
        "question": "<User's message>",
        "answer": "<Agent's response>",
        "category": "<Category's ID>",
        "subcategory": "<Subcategory's ID>",
        "language": "<language's ID>"
    }}
]
"""