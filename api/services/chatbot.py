import os
import logging
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from .brain import Brain
from .config import CHAT_MODEL


load_dotenv()
logger = logging.getLogger("chatbot")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

       
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
            self.llm = ChatOpenAI(model=CHAT_MODEL, api_key=OPENAI_API_KEY, temperature=0.3)
            self.prompt = hub.pull("rlm/rag-prompt")
            self.initialized = True
            logger.info("ChatBot initialized successfully.")
        except Exception as e:
            logger.exception(f"Initialization failed: {e}")
            raise RuntimeError("ChatBot initialization failed.") from e
    

    def generate_response(self, messages_history):
        response = self.llm.invoke(messages_history)
        return response.content
    
    def read_image_response(self, image_base64: str) -> str:
        """
        Process an image encoded in base64 and return the extracted text
        or a description of the image.
        """
        logger.info("Processing image for text extraction or description.")
        msg = HumanMessage(
            content=[
                {"type": "text", "text": "Extract and return all text in this image if it's a receipt. "
                                         "If it's not a receipt, explain what the image is doing."},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_base64}},
            ]
        )
        response = self.llm.invoke([msg])
        return response.content.strip()