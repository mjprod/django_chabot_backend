import datetime

# vector store constants
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
CHROMA_BRAIN_COLLECTION="brain"
CHROMA_CONVERSATION_COLLECTION="conversation"
CHROMA_DIR="./chroma"

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