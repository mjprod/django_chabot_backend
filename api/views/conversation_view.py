from ..chatbot import (
    generate_prompt_conversation,
    prompt_conversation_history,
)
from ..serializers import (
    CompleteConversationsSerializer,
    PromptConversationSerializer,
    PromptConversationHistorySerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from datetime import datetime
from ..mixins.mongodb_mixin import MongoDBMixin
import time

logger = logging.getLogger(__name__)


# new api for start conversation
class PromptConversationView(MongoDBMixin, APIView):
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
                "text": translation.get("text", "")
            }
            for translation in translations
        ]
    }
    return parsed_data

# Search and translate the top correct answer
def search_top_answer_and_translate(self,query, collection_name="feedback_data"):
    db = self.get_db()
    collection = db[collection_name]
    print(f"Searching for: '{query}' in collection '{collection_name}'")
    try:
        # Use the existing text index (on user_input)
        results = collection.find(
            {
                "$text": {"$search": query} ,  # Search in the existing text index
                #  # Search in the existing text index
            },
            {
                "score": {"$meta": "textScore"},  # Include relevance score
                "correct_answer": 1 ,
                "conversation_id": 1,
                "user_input": 1,
                "metadata": 1, # Ensure the `correct_answer` field is included
            }
        ).sort("score", {"$meta": "textScore"})  # Sort by relevance

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
                "message": "No related correct answers found."
            }
    except Exception as e:
        print(f"Error fetching highest confidence answer: {e}")

"""
this is the new View for the prompt_conversation_history,
it will be used to get the history of a conversation
with the context and conversation_id, it will be able to
get the history of the conversation along with the new question
and if the user where to ask "What was the first message i sent,
it will be able to find it and return that to the user
"""
class PromptConversationHistoryView(MongoDBMixin, APIView):
    def post(self, request):
        db = None
        try:
            # Log start of request processing
            logger.info("Starting prompt_conversation_history request")
            start_time = time.time()

            # Validate input data
            serializer = PromptConversationHistorySerializer(data=request.data)
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
            response = search_top_answer_and_translate(self,prompt)
            if response["correct_answer"]:
                time.sleep(6)
                return Response(response, status=status.HTTP_200_OK)

            # Generate AI response with timing
            generation_start = time.time()
            logger.info("Starting AI answer generation")
            response = prompt_conversation_history(
                user_prompt=prompt,
                conversation_id=conversation_id,
                admin_id="",
                agent_id="",
                user_id=user_id,
            )
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # this is the response data that is sent to user
            response_data = {
                "conversation_id": conversation_id,
                "user_input": prompt,
                "generation": response["generation"],
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
            if db is not None:
                self.close_db()

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
            db = self.get_db()
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
        finally:
            if db is not None:
                self.close_db()


class CompleteConversationsView(MongoDBMixin, APIView):
    def get(self, request):
        db = None
        start_time = time.time()
        logger.info("Starting complete_conversations GET request")

        try:
            # Get pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            # Connect to MongoDB
            db = self.get_db()
            logger.info("Connected to MongoDB")

            # Query filter
            query_filter = {}

            # Get total count and paginated results
            total_count = db.complete_conversations.count_documents(query_filter)
            cursor = (
                db.complete_conversations.find(query_filter)
                .sort("timestamp", -1)
                .skip((page - 1) * limit)
                .limit(limit)
            )

            # Process results
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
                results.append(doc)

            logger.info(f"Retrieved {len(results)} conversations from MongoDB")

            # Prepare response
            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            logger.info(
                f"Total request processing time: {time.time() - start_time:.2f}s"
            )

            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f"Invalid pagination parameters: {str(e)}")
            return Response(
                {"error": "Invalid pagination parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            # Cleanup database connection
            if db is not None:
                self.close_db()

    def post(self, request):
        db = None
        start_time = time.time()
        logger.info("Starting complete_conversations POST request")

        try:
            # Log incoming request details
            logger.info(f"Request Data: {request.data}")
            logger.info(f"Request Content-Type: {request.content_type}")
            logger.info(f"Request Headers: {request.headers}")

            # Validate request data
            logger.info("Validating request data")
            serializer = CompleteConversationsSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare document for MongoDB
            logger.info("Starting MongoDB Write Operations")
            conversation_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "messages": serializer.validated_data["messages"],
                "timestamp": datetime.utcnow().isoformat(),  # Use UTC for consistency
            }

            db = self.get_db()
            result = db.complete_conversations.insert_one(conversation_data)
            inserted_id = str(result.inserted_id)

            # Prepare and return response
            response_data = {
                "message": "Conversation saved successfully",
                "conversation_id": inserted_id,
            }

            logger.info(
                f"MongoDB operation completed in {time.time() - start_time:.2f}s"
            )
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.close_db()
            # gc.collect()
