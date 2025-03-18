from datetime import datetime
from openai import OpenAI
import uuid
import json
import re


import logging
from .config import (
    OPENAI_API_KEY,
    CHAT_MODEL,
    CONVERSATION_STREAMING_PROMPT,
)

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from api.models import Knowledge, KnowledgeContent, Context, Category
from api.utils.enum import KnowledgeType, KnowledgeContentStatus, KnowledgeContentLanguage
from api.app.mongo import MongoDB

STREAMING_COLLECTION="ck_old_conversations"

logger = logging.getLogger(__name__)


"""
TODO: 
1. configuration values are very messy. Refactoring needed
2. Hardcoded a lot!!
3. AI response can be so out of control
4. Need to use transaction atomic operation for data saving!
"""



class ConversationStreamingManager:
    _instance = None

    def __new__(cls, api_key: str = OPENAI_API_KEY):
        if cls._instance is None:
            if api_key is None:
                raise ValueError("API key must be provided during the first initialization.")
            cls._instance = super(ConversationStreamingManager, cls).__new__(cls)
            cls._instance.client = OpenAI(
                api_key=api_key,
            )
        return cls._instance
    

    def streaming_conversations_from_db(self, date):
      query = {"dateFr": date}  
      MongoDB.get_db()
      documents = MongoDB.query_collection(collection_name=STREAMING_COLLECTION, query=query)

      if not documents:
          logger.info(f"streamed conversations for date ({date}) is not ready yet")
          return

      document = documents[0]  
      for data in document.get("ResponseData", []):
          for conversation in data.get("ConversationsList", []):
              conversation_data = conversation.get("Conversations")

              if conversation_data:
                  extracted_data = self._extract_admin_responses(conversation_data)
                  
                  if extracted_data:
                    user_messages, admin_messages, conversation_context = extracted_data
                    ai_response_list = self._categorize_and_detect_language(admin_messages)
                    self._store_knowledge_context(user_messages, admin_messages, ai_response_list, conversation_context)


    def _categorize_and_detect_language(self, admin_messages: list):
        if not isinstance(admin_messages, list):
            raise ValueError("Expected a list of Admin responses.")
        
        admin_messages_text = "\n".join(admin_messages)
        full_prompt = f"{CONVERSATION_STREAMING_PROMPT}\n\nInput Admin Reply:\n{admin_messages_text}"

        completion = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )

        response_content = completion.choices[0].message.content

        try:
            response_dict = json.loads(response_content)
            return response_dict
        except json.JSONDecodeError as e:
            logger.error(f"Model response is not valid JSON: {str(e)}")
            return None
        

    def _extract_admin_responses(self, conversation):

      admin_messages = []
      user_messages = []

      found_flag = False
      
      for i, message in enumerate(conversation):
        if (message.get("IsService",False) 
            and message.get("AdminAction",2)< 2  
            and message.get("AdminReply",None) 
            and self._has_more_than_num_words(message.get("AdminReply"), 3)
            ):
            found_flag = True
            
            # get cooresponding user message
            user_message = ""
            if i-1>=0 and conversation[i-1].get("IsService")==False:
                user_message=conversation[i-1].get("UserMsg")
            admin_message = message.get("AdminReply")

            user_message = user_message.replace("\r\n", " ").strip()
            admin_message = admin_message.replace("\r\n", " ").strip()

            admin_messages.append(admin_message)
            user_messages.append(user_message)

      if found_flag:
            return user_messages, admin_messages, conversation

      return None
    

    def _has_more_than_num_words(self, text, num):
        words = re.findall(r'\b\w+\b', text)  # Extracts real words
        return len(words) > num


    def _store_knowledge_context(self, user_messages, admin_messages, ai_responses, conversation_context):

        # Step 1: Create a Context entry using conversation_context
        context_instance = Context(context=conversation_context)
        context_instance.save()

        # Step 2: Iterate through knowledge_content_list and create Knowledge and KnowledgeContent entries
        for question, answer in zip(user_messages, admin_messages):            
            category = None
            language = KnowledgeContentLanguage.MALAYSIAN.value

            # dealing with stupid AI response
            try:
                if len(ai_responses) == len(admin_messages):
                    ai_response = ai_responses[admin_messages.index(answer)]
                    category_id = ai_response.get('category', None)
                    category = Category.objects.get(id=int(category_id))
                    language = int(ai_response.get('language', language))
            except (IndexError, Exception, TypeError, ObjectDoesNotExist, Exception):
                category = None
                language = KnowledgeContentLanguage.MALAYSIAN.value
                logger.error(f"Invalid or missing category or language from AI response for context: {context_instance.id}")


            # Create a new Knowledge entry
            knowledge_instance = Knowledge(
                knowledge_uuid=uuid.uuid4(),
                category=category,
                subcategory=None,
                context=context_instance,
                type=KnowledgeType.FAQ.value
            )

            knowledge_instance.save()
            
            # Create a new KnowledgeContent entry
            KnowledgeContent.objects.create(
                knowledge=knowledge_instance,
                status=KnowledgeContentStatus.NEEDS_REVIEW.value,
                is_edited=False,
                in_brain=False,
                question=question,
                answer=answer,
                language=int(language),
            )


                      

def main():

    manager = ConversationStreamingManager(api_key=OPENAI_API_KEY)
    manager.streaming_conversations_from_db("2025-03-13")


if __name__ == "__main__":
    main()