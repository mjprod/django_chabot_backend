from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from datetime import datetime
import time

from rapidfuzz import fuzz

from api.chatbot import (
    extrair_knowledge_items,
    get_store,
)

from api.app.conversation import (
    prompt_conversation,
    prompt_conversation_admin,
    prompt_conversation_agent_ai,
 )

from ..serializers import (
    PromptConversationSerializer,
    PromptConversationAdminSerializer,
    PromptConversationAgentAiSerializer,
)

from ai_config.ai_constants import (
    LANGUAGE_DEFAULT,
)

from api.views.brain_file_reader import (
    get_document_count,
)

from api.app.mongo import MongoDB

logger = logging.getLogger(__name__)


class PromptConversationAdminView(APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation_admin request")

        try:
            # Get the header value as a string
            use_mongo_str = request.GET.get(
                "use_mongo", "0"
            )  # Default to "0" if not provided
            use_mongo = use_mongo_str in ("1", "true", "yes")
            print("Mongo: " + str(use_mongo))

            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            print("Language " + language)

            # Get language from query params or request data
            language_code = request.GET.get("language", LANGUAGE_DEFAULT)
            logger.info(f"Processing request for language: {language_code}")

            # Validate input data
            input_serializer = PromptConversationAdminSerializer(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = input_serializer.validated_data["prompt"]
            conversation_id = input_serializer.validated_data["conversation_id"]
            # user_id = input_serializer.validated_data["user_id"]              

            # Extract validated data
            validated_data = input_serializer.validated_data

            # Generate AI response
            # generation_start = time.time()
            logger.info("Starting AI response generation")

            response = prompt_conversation_admin(
                self,
                user_prompt=validated_data["prompt"],
                conversation_id=validated_data["conversation_id"],
                admin_id=validated_data.get("admin_id", ""),
                bot_id=validated_data.get("bot_id", ""),
                user_id=validated_data["user_id"],
                language_code=language_code,
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error in prompt_conversation_admin view: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = MongoDB.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class PromptConversationAgentAIView(APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation_admin request")

        try:
               # Validate input data
            input_serializer = PromptConversationAgentAiSerializer(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = input_serializer.validated_data["prompt"]
            # conversation_id = input_serializer.validated_data["conversation_id"]
            # user_id = input_serializer.validated_data["user_id"]              

            # Extract validated data
            validated_data = input_serializer.validated_data

            # Generate AI response
            # generation_start = time.time()
            logger.info("Starting AI response generation")

            response = prompt_conversation_agent_ai(
                user_prompt=validated_data["prompt"],
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error in prompt_conversation_admin view: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = MongoDB.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class PromptConversationView(APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation request")

        try:
            # Get the header value as a string
            use_mongo_str = request.GET.get(
                "use_mongo", "0"
            )  # Default to "0" if not provided
            use_mongo = use_mongo_str in ("1", "true", "yes")
            print("Mongo: " + str(use_mongo))

            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            print("Language " + language)

            # Get language from query params or request data
            language_code = request.GET.get("language", LANGUAGE_DEFAULT)
            logger.info(f"Processing request for language: {language_code}")

            # Validate input data
            input_serializer = PromptConversationSerializer(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = input_serializer.validated_data["prompt"]

            # Extract validated data
            validated_data = input_serializer.validated_data

            # Generate AI response
            # generation_start = time.time()
            logger.info("Starting AI response generation")

            response = prompt_conversation(
                self,
                user_prompt=validated_data["prompt"],
                store=get_store,
                language_code=language_code,
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error in prompt_conversation_admin view: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = MongoDB.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class ConversationDetailView(APIView):
    def get(self, request, conversation_id):
        db = None
        start_time = time.time()
        try:
            db = MongoDB.get_db()
            
            conversation = db.conversations.find_one({"session_id": conversation_id})            
            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Converte o ObjectId para string
            conversation["_id"] = str(conversation["_id"])
            
            return Response(conversation, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class AllConversationsIdsView(APIView):
    def get(self, request):
        db = None
        try:
            db = MongoDB.get_db()
            sessions = list(db.conversations.find({}, {"session_id": 1, "_id": 0}))
            return Response(sessions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving session ids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class UpdateKnowledgeView(APIView):
    def post(self, request):
        db = None
        try:
            conversation_id = request.data.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            db = MongoDB.get_db()
            # Busca a conversa usando o session_id
            conversation = db.conversations.find_one({"session_id": conversation_id})
            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            knowledge_items = extrair_knowledge_items(conversation)
            
            
            # Retorna os itens extraídos (candidatos) sem verificar no brain
            return Response({
                "message": "Candidate knowledge items extracted.",
                "candidate_items": knowledge_items,
                "count": len(knowledge_items)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error extracting candidate knowledge: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class DeleteConversationView(APIView):
    def delete(self, request, *args, **kwargs):
        conversation_id = kwargs.get("conversation_id")
        if not conversation_id:
            return Response(
                {"error": "conversation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        db = None
        try:
            db = MongoDB.get_db()
            result = db.conversations.delete_one({"session_id": conversation_id})
            if result.deleted_count == 0:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"message": "Conversation deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error deleting conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    