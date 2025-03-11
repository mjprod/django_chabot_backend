from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from datetime import datetime

from api.chatbot import (
    check_answer_mongo_and_openai,
    get_store,
)

from api.app.conversation import (
    prompt_conversation,
    prompt_conversation_admin,
 )

from ..serializers import (
    PromptConversationSerializer,
    PromptConversationAdminSerializer,
)

from api.constants.ai_constants import (
    LANGUAGE_DEFAULT,
)

from api.views.brain_file_reader import (
    get_document_count,
)

from api.app.mongo import MongoDB

logger = logging.getLogger(__name__)

def fuzzy_match_with_dynamic_context(
    self, query, collection_name, threshold, language="en"
):
    db = MongoDB.get_db()
    collection = db[collection_name]

    # Check if a text index exists and create it if not
    index_exists = False

    # Get all existing indexes
    indexes = collection.index_information()

    # Check if there's an existing text index
    for index_name, index_info in indexes.items():  # Unpack index name and info
        if index_info.get("key") == [
            ("user_input", "text")
        ]:  # Access 'key' in index_info
            index_exists = True
            break

    # Create the index if it doesn't exist
    if not index_exists:
        print("Creating text index on 'user_input'...")
        collection.create_index([("user_input", "text")])
        print("Text index created successfully.")
    else:
        print("Text index already exists.")

    # Fetch all documents with 'user_input' and 'correct_answer'

    documents = list(
        collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1})
    )

    if not documents:
        print(f"No documents found in collection '{collection_name}'.")
        return []

    matches = []

    for doc in documents:
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        timestamp = doc.get("timestamp", "")

        combined_text = f"{user_input} {correct_answer} {timestamp}".strip()

        # Calculate fuzzy similarity
        similarity = fuzz.partial_ratio(query, combined_text)
        # Only include matches above the threshold
        if similarity >= threshold:
            matches.append({"similarity": min(similarity, 100), **doc})

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Return the first correct_answer if matches exist, otherwise return False
    for match in matches:
        match["timestamp"] = match.get("timestamp", "")  # Ensure field exists
        if isinstance(match["timestamp"], str):  # Convert timestamp string to datetime
            try:
                match["timestamp"] = datetime.fromisoformat(match["timestamp"])
            except ValueError:
                match["timestamp"] = datetime.min

    # Sort by similarity (descending) and then by timestamp (latest first)
    matches = sorted(
        matches, key=lambda x: (-x["similarity"], -x["timestamp"].timestamp())
    )

    # Return the first correct_answer if matches exist, otherwise return False
    if matches:
        # Check if the first match has a similarity score greater than 80
        if matches[0]["similarity"] > 80:
            best_answer = matches[0]["correct_answer"]
            print("\nHigh Similarity Match Found:")
            print(best_answer)
            return best_answer  # Return immediately if it's a strong match

        # Otherwise, proceed with OpenAI validation
        limited_matches = matches[:5]

        openai_response = check_answer_mongo_and_openai(query, limited_matches)

        if openai_response:
            print("\nOpenAI Response:")
            print(openai_response)
            return openai_response
        else:
            print("No matches found.")
    else:
        print("No matches found.")

class PromptConversationAdminView(APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation_admin request")

        try:
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
            validated_data = input_serializer.validated_data

            logger.info("Starting AI response generation")

            response = prompt_conversation_admin(
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
        

class PromptConversationView(APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation request")

        try:
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
            validated_data = input_serializer.validated_data

            # Generate AI response
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
