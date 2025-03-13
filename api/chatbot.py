import logging
from .services.chatbot import ChatBot

# create our gloabl variables
logger = logging.getLogger(__name__)

# Process docs
try:
    chatbot = ChatBot()
    logger.info("Chatbot created successfully")

except Exception as e:
    logger.error(f"Failed to create vector store: {str(e)}")
    raise