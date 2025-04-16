import os

from dotenv import load_dotenv

load_dotenv()

STREAMING_COLLECTION="ck_old_conversations"

# vector store constants
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
COLLECTION_NAME="RAG"
CHROMA_BRAIN_COLLECTION="brain"
CHROMA_CONVERSATION_COLLECTION="conversation"
CHROMA_DIR="./chroma_db"

# chat model constants
CHAT_MODEL="gpt-4o-mini"
CHAT_MODEL_PROVIDER="openai"

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENAI_TIMEOUT=30
MAX_TEMPERATURE=0.2
MAX_TOKENS=500

CHATBOT_PROMPT="""
You are a helpful assistant that answers user questions strictly based on the provided retrieved knowledge. 
If the retrieved knowledge is not directly relevant to the question, kindly let the user know that you’re not sure about the answer and explain that you can only help with questions related to this game platform.
"""


CONVERSATION_STREAMING_PROMPT = """

Task: Analyze a list of admin replies according to the provided categorization and language detection rules.

    Rule 1: Categorization:Assign each reply to the appropriate category number based on the following categories:

        - 3rd Party = '1'
        - 4D Lotto = '2'
        - Account = '3'
        - Feedback = '4'
        - Finance = '5'
        - Points Shop = '6'
        - Referral = '7'
        - Security = '8'
        - Technical = '9'
        - Customer Support = '10'
        - Game Inquiry = '11'
        - Policy Explanation = '12'
        - Encouragement = '13'
        - Sports Betting = '14'

    Rule 2: Language Detection: Determine the language of each reply and assign a number string based on the following languages:

        - English = '1'
        - Malaysian = '2'
        - Chinese = '3'

    Core Rules:

        - Do not modify the original admin reply.
        - The output format must strictly follow the structure below for each reply:

        {{
            "answer": "<Admin's reply>",
            "category": "<Category Number>",
            "language": "<Language Number>"
        }}

        - Organize all JSON objects into a list.
        - Ensure the response strictly follows raw JSON structure. Do not use any markdown formatting.
"""