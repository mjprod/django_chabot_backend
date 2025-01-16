from ..chatbot import (
    generate_prompt_conversation,
)
from ..serializers import (
    CompleteConversationsSerializer,
    PromptConversationSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from datetime import datetime
from ..mixins.mongodb_mixin import MongoDBMixin
import time

from django.conf import settings
from pymongo import MongoClient


logger = logging.getLogger(__name__)


mongo_client = None


# API functions
def get_mongodb_client():
    global mongo_client
    if mongo_client is None:
        mongo_client = MongoClient(settings.MONGODB_URI)
    return mongo_client[settings.MONGODB_DATABASE]


def parse_to_json(data):
    # Extract the required fields
    conversation_id = data.get("conversation_id", "")
    user_input = data.get("user_input", "")
    correct_answer = data.get("correct_answer", "")
    confidence = data.get("confidence", 0.0)
    translations = data.get("metadata", {}).get("translations", [])

    # Format the parsed data
    parsed_data = {
        "conversation_id": conversation_id,
        "user_input": user_input,
        "generation": correct_answer,
        "confidence": confidence,
        "translations": [
            {
                "language": translation.get("language", ""),
                "text": translation.get("text", ""),
            }
            for translation in translations
        ],
    }
    return parsed_data


# Search and translate the top correct answer
def search_top_answer_and_translate(query, collection_name="feedback_data"):
    db = get_mongodb_client()
    collection = db[collection_name]
    print(f"Searching for: '{query}' in collection '{collection_name}'")
    try:
        # Use the existing text index (on user_input)
        results = collection.find(
            {
                "$text": {"$search": query},  # Search in the existing text index
                #  # Search in the existing text index
            },
            {
                "score": {"$meta": "textScore"},  # Include relevance score
                "correct_answer": 1,
                "conversation_id": 1,
                "user_input": 1,
                "metadata": 1,  # Ensure the `correct_answer` field is included
            },
        ).sort(
            "score", {"$meta": "textScore"}
        )  # Sort by relevance

        results_list = list(results)
        if results_list:
            top_result = results_list[0]  # Select the result with the highest scor

            # Safely retrieve keys with .get() to avoid KeyErrors
            correct_answer = top_result.get("correct_answer")
            confidence = top_result.get("score", 0)
            conversation_id = top_result.get("conversation_id", "unknown-conversation")
            user_input = top_result.get("user_input", query)
            metadata = top_result.get("metadata", {})

            # Return the top answer and confidence score
            return {
                "correct_answer": correct_answer,
                "conversation_id": conversation_id,
                "user_input": user_input,
                "generation": correct_answer,
                "confidence": confidence,
                "translations": metadata.get("translations", []),
            }

        else:
            print("No related correct answers found.")
            return {
                "correct_answer": None,
                "confidence": 0,
                "message": "No related correct answers found.",
            }
    except Exception as e:
        print(f"Error fetching highest confidence answer: {e}")


# new api for start conversation
class PromptConversationWithDBView(MongoDBMixin, APIView):
    def post(self, request):
        db = None
        try:
            # Log start of request processing
            logger.info("Starting prompt_conversation request")
            start_time = time.time()

            # Validate input data
            serializer = PromptConversationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = serializer.validated_data["prompt"]
            conversation_id = serializer.validated_data["conversation_id"]
            user_id = serializer.validated_data["user_id"]

            # Search for the answer on mongo db
            response = search_top_answer_and_translate(prompt)
            if response["correct_answer"]:
                time.sleep(6)
                return Response(response, status=status.HTTP_200_OK)

            # Generate AI response with timing
            generation_start = time.time()
            logger.info("Starting AI response generation")
            response = generate_prompt_conversation(
                user_prompt=prompt,
                conversation_id=conversation_id,
                admin_id="",
                agent_id="",
                user_id=user_id,
            )
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # Prepare MongoDB document
            db = self.get_db()
            conversation_data = {
                "conversation_id": conversation_id,
                "prompt": prompt,
                "generation": response["generation"],
                "user_id": user_id,
                "translations": response.get("translations", []),
                "timestamp": datetime.now().isoformat(),
            }

            # Insert into MongoDB
            db.conversations.insert_one(conversation_data)
            logger.info("MongoDB operation successful.")

            # Prepare and send response
            response_data = {
                "conversation_id": conversation_id,
                "user_input": prompt,
                "generation": response["generation"],
                "confidence": response["confidence_score"],
                "translations": response.get("translations", []),
            }

            logger.info(
                f"Total request processing time: {time.time() - start_time:.2f}s"
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            # Cleanup database connection
            if db is not None:
                self.close_db()
            # Uncomment memory cleanup if needed
            # gc.collect()
