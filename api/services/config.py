import datetime

# vector store constants
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
COLLECTION_NAME="knowledge_base"
CHROMA_DIR="./chroma_brain_db"
MESSAGE_KEY="historyMsgs"
MONOGODB_COLLECTION="brain"

# chat model constants
CHAT_MODEL="gpt-4o"
CHAT_MODEL_PROVIDER="openai"

# date threshold
DATE_THRESHOLD=datetime.datetime(2025, 3, 1)

CHATBOT_PROMPT="""
You are a helpful assistant that answers user questions strictly based on the provided retrieved knowledge. 
If the retrieved knowledge is not directly relevant to the question, kindly let the user know that you’re not sure about the answer and explain that you can only help with questions related to this game platform.
"""
# Avoid sounding like an AI and ensure your responses are natural and human-like.