import logging
import os
from typing import Optional

from dotenv import load_dotenv
from langchain import hub
from langchain.chat_models import init_chat_model

from .brain import Brain
from .config import CHAT_MODEL, CHAT_MODEL_PROVIDER

load_dotenv()
logger = logging.getLogger("chatbot")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

class ChatBot:
    _instance: Optional["ChatBot"] = None

    def __new__(cls, *args, **kwargs) -> "ChatBot":
        if cls._instance is None:
            cls._instance = super(ChatBot, cls).__new__(cls)
            logger.info("Creating new ChatBot singleton instance.")
        return cls._instance

    def __init__(self):
        if getattr(self, "initialized", False):
            return

        logger.info("Initializing ChatBot...")
        try:
            self.brain = Brain()
            logger.debug("Brain initialized.")

            self.vector_store = self.brain.vector_store
            logger.debug("Vector store initialized.")

            self.llm = init_chat_model(
                CHAT_MODEL,
                model_provider=CHAT_MODEL_PROVIDER,
                api_key=OPENAI_API_KEY
            )
            logger.debug("LLM initialized.")

            self.prompt = hub.pull("rlm/rag-prompt")
            logger.debug("Prompt retrieved successfully.")

            self.initialized = True
            logger.info("ChatBot initialization complete.")

        except Exception as e:
            logger.exception(f"ChatBot initialization failed: {e}")
            raise RuntimeError("ChatBot could not be initialized.") from e
        
    def generate_response(self, messages_history):
        response = self.llm.invoke(messages_history)
        return response.content