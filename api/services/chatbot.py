import logging
import os
from typing import Annotated, List
from typing_extensions import TypedDict

from .brain import Brain
from .config import (
    # chat model constants
    CHAT_MODEL,
    CHAT_MODEL_PROVIDER,
    CHATBOT_PROMPT
)

from dotenv import load_dotenv

from langchain import hub
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.messages import HumanMessage

# from langgraph.graph import START, StateGraph, MessagesState
# from langgraph.graph.message import add_messages
# from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
logger = logging.getLogger("chatbot")

USER_AGENT = os.getenv("USER_AGENT","chatbot")
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY",None)
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY",None)
TOKENIZERS_PARALLELISM=os.getenv("TOKENIZERS_PARALLELISM", False)


class ChatBot:
    # store the singleton instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChatBot, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
         # access the singleton instance
        if not hasattr(self, 'initialised'):
            brain = Brain()
            self.vector_store = brain.vector_store
            self.llm = init_chat_model(
                CHAT_MODEL, 
                model_provider=CHAT_MODEL_PROVIDER, 
                api_key=OPENAI_API_KEY)
            
            self.prompt = hub.pull("rlm/rag-prompt")
            # self.memory = MemorySaver()
            # self.graph = self._build_graph()
            self.initialised = True

    # def _build_graph(self):
        # TODO: need to redefine the state scheme, if it is used for question and answer pair only
        # workflow = StateGraph(state_schema=MessagesState)
        # workflow.add_node("chatbot", self.chatbot_node)
        # workflow.add_edge(START, "chatbot")
        # return workflow.compile()

    # chatbot node
    ### def chatbot_node(self, state: MessagesState):
        
        # chat_history = str(state["messages"])
        ### last_query = str(state["messages"][-1])

        ### docs = self.vector_store.similarity_search_with_relevance_scores(last_query, k=4)

        # for doc, score in docs:
        #     logger.info(f"Document: {doc.page_content}, Score: {score:.4f}")

        ### context = "\n\n".join([doc.page_content for doc, score in docs])

        ### last_query = state["messages"][-1]

        ### retrieved_context = "\n\n".join([f"{doc.page_content}" for doc, score in docs])

       ###  augmented_message = f"""
                               ###  {CHATBOT_PROMPT}

                               ###  retrieved knowledge:
                               ###  {retrieved_context}

                                ### User's question:
                                ### {last_query.content}
                           ###  """

       ###  response = self.llm.invoke(augmented_message)        
       ###  return {"messages": response}
    
   ###  def query(self, message):
       ###  input_messages = [HumanMessage(content=message)]
       ###  response = self.graph.invoke({"messages": input_messages})
      ###   return response["messages"][-1].content