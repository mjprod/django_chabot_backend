import logging

from dotenv import load_dotenv

from .services.chatbot import ChatBot

# create our gloabl variables
logger = logging.getLogger(__name__)
logger.info("Initializing vector database...")

# Load environment variables
load_dotenv()

# Process docs
try:
    logger.info("Vector store creation completed successfully")

    chatbot = ChatBot()
    logger.info("Chatbot created successfully")
    store = chatbot.vector_store    

except Exception as e:
    logger.error(f"Failed to create vector store: {str(e)}")
    raise