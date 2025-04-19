import os
import logging
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI
from .brain import Brain
from .config import CHAT_MODEL
import re

load_dotenv()
logger = logging.getLogger("chatbot")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
def strip_markdown(text):
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'[`#>~-]', '', text)
        return text.strip() 
        
class ChatBot:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Creating ChatBot singleton instance.")
        return cls._instance

    def __init__(self):
        if getattr(self, "initialized", False):
            return

        logger.info("Initializing ChatBot...")
        try:
            self.brain = Brain()
            self.vector_store = self.brain.vector_store
            self.llm = ChatOpenAI(model=CHAT_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)
            self.prompt = hub.pull("rlm/rag-prompt")
            self.initialized = True
            logger.info("ChatBot initialized successfully.")
        except Exception as e:
            logger.exception(f"Initialization failed: {e}")
            raise RuntimeError("ChatBot initialization failed.") from e
    

    def generate_response(self, messages_history):
        response = self.llm.invoke(messages_history)
        clean_response = strip_markdown(response.content)

        return clean_response