import logging
import os

from .brain import Brain
from .config import (
    # chat model constants
    CHAT_MODEL,
    CHAT_MODEL_PROVIDER,
)

from dotenv import load_dotenv
from langchain import hub
from langchain.chat_models import init_chat_model

load_dotenv()
logger = logging.getLogger("chatbot")

OPENAI_API_KEY= os.getenv("OPENAI_API_KEY",None)

class ChatBot:
    # store the singleton instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChatBot, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
         # access the singleton instance
        if not hasattr(self, 'initialized'):
            self.brain = Brain()
            self.vector_store = self.brain.vector_store
            self.llm = init_chat_model(
                CHAT_MODEL, 
                model_provider=CHAT_MODEL_PROVIDER, 
                api_key=OPENAI_API_KEY)
            
            self.prompt = hub.pull("rlm/rag-prompt")
            self.initialized = True

    