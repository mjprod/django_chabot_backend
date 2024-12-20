# added logging
import gc
import logging
import time
import tracemalloc
from datetime import datetime

from bson import ObjectId
from django.conf import settings
from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import (
    compare_memory,
    generate_prompt_conversation,
    generate_user_input,
    monitor_memory,
    translate_and_clean,
)
from .serializers import (
    CaptureFeedbackSerializer,
    CompleteConversationsSerializer,
    PromptConversationSerializer,
    UserInputSerializer,
)


# added mongodb base view class
class MongoDBMixin:
    def get_db(self):
        memory_snapshot = monitor_memory()
        try:
            client = MongoClient(settings.MONGODB_URI)
            return client[settings.MONGODB_DATABASE]
        finally:
            compare_memory(memory_snapshot)
            gc.collect()

    def cleanup_db_connection(self, db):
        if db is not None:
            db.client.close()


logger = logging.getLogger(__name__)


class UserInputView(MongoDBMixin, APIView):
    def post(self, request):
        memory_snapshot = monitor_memory()
        db = None
        start_time = time.time()
        logger.info("Starting user_input request")

        try:
            # Validate input data
            logger.info("Validating request data")
            serializer = UserInputSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Extract data with default "None" for user_id
            prompt = serializer.validated_data["prompt"]
            user_id = serializer.validated_data.get("user_id", "None")

            # Generate response
            generation_start = time.time()
            logger.info("Starting AI response generation")
            cleaned_prompt = translate_and_clean(prompt)
            generation = generate_user_input(cleaned_prompt)
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # Prepare MongoDB document and response data
            response_data = {
                "user_id": user_id,
                "prompt": prompt,
                "cleaned_prompt": cleaned_prompt,
                "generation": generation["generation"],
                "translations": generation["translations"],
                "usage": {
                    "prompt_tokens": generation["usage"].get("prompt_tokens", 0),
                    "completion_tokens": generation["usage"].get(
                        "completion_tokens", 0
                    ),
                    "total_tokens": generation["usage"].get("total_tokens", 0),
                },
            }

            # Save to MongoDB
            db_start = time.time()
            logger.info("Starting MongoDB Write Operations")
            db = self.get_db()

            user_input_doc = {**response_data, "timestamp": datetime.now().isoformat()}

            db.user_inputs.insert_one(user_input_doc)
            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")

            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.cleanup_db_connection(db)
            compare_memory(memory_snapshot)
            gc.collect()
            del generation


class UserConversationsView(MongoDBMixin, APIView):
    def get(self, request, user_id):
        db = self.get_db()
        conversations = db.conversations

        user_conversations = []
        for conv in conversations.find({"user_id": user_id}):
            conv["_id"] = str(conv["_id"])
            user_conversations.append(conv)

        return Response(user_conversations, status=status.HTTP_200_OK)


# new api for start conversation
class PromptConversationView(MongoDBMixin, APIView):
    def post(self, request):
        memory_snapshot = monitor_memory()
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
                user_id="",
            )
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # MongoDB operations with timing
            db_start = time.time()
            logger.info("Starting MongoDB Write Operations")
            db = self.get_db()
            conversation_data = {
                "conversation_id": conversation_id,
                "prompt": prompt,
                "generation": response["generation"],
                "user_id": user_id,
                "translations": response.get("translations", []),
                "timestamp": datetime.now().isoformat(),
            }

            # Insert as new document
            db.conversations.insert_one(conversation_data)
            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")

            # Prepare response data
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
            if db is not None:
                self.cleanup_db_connection(db)
            compare_memory(memory_snapshot)
            gc.collect()
            del response


class CompleteConversationsView(MongoDBMixin, APIView):
    def get(self, request):
        start_time = time.time()
        logger.info("Starting complete_conversations GET request")

        try:
            # Get pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            # Get MongoDB connection
            db_start = time.time()
            logger.info("Starting MongoDB Read Operations")
            db = self.get_db()

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
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")

            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")

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

    def post(self, request):
        start_time = time.time()
        logger.info("Starting complete_conversations POST request")
        try:
            # Log the request data
            logger.info(f"Request Data: {request.data}")
            logger.info(f"Request Content-Type: {request.content_type}")
            logger.info(f"Request Headers: {request.headers}")

            # Clean up the messages data before validation
            cleaned_data = {
                "conversation_id": request.data["conversation_id"],
                "messages": [],
            }

            # Process each message and clean up [object Object] artifacts
            for message in request.data["messages"]:
                cleaned_message = {
                    "sender": message["sender"],
                    "user": message["user"],
                    "timestamp": message["timestamp"],
                }

                # Handle text field that can be either string or array
                if isinstance(message["text"], list):
                    cleaned_message["text"] = [
                        item.replace("[object Object]", "").strip()
                        for item in message["text"]
                        if item and isinstance(item, str)
                    ]
                else:
                    cleaned_message["text"] = message["text"]

                # Add optional agent_id if present
                if "agent_id" in message:
                    cleaned_message["agent_id"] = message["agent_id"]

                cleaned_data["messages"].append(cleaned_message)

            # Validate cleaned data
            logger.info("Validating request data")
            serializer = CompleteConversationsSerializer(data=cleaned_data)

            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save to MongoDB
            conversation_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "messages": serializer.validated_data["messages"],
                "timestamp": datetime.now().isoformat(),
            }

            db = self.get_db()
            db.complete_conversations.insert_one(conversation_data)

            return Response(
                {"message": "Conversation saved successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CaptureFeedbackView(MongoDBMixin, APIView):

    def post(self, request):
        start_time = time.time()
        logger.info("Starting feedback POST request")
        try:
            # Transform incoming data to match serializer format
            transformed_data = {
                "conversation_id": str(ObjectId()),  # Generate new ID if not provided
                "user_input": request.data.get("prompt", ""),
                "ai_response": request.data.get("generation", ""),
                "correct_bool": request.data.get("correct_bool", False),
                "chat_rating": request.data.get("chat_rating", 0),
                "correct_answer": request.data.get("correct_answer", ""),
                "metadata": {
                    **request.data.get("metadata", {}),
                    "user_id": request.data.get("user_id"),
                    "translations": request.data.get("translations", []),
                    "confidence": 0.97,  # Add fixed confidence score
                },
            }

            # Validate transformed data
            logger.info("Validating request data")
            serializer = CaptureFeedbackSerializer(data=transformed_data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process translations
            logger.info("Processing feedback translations")
            translated_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "user_input": translate_and_clean(transformed_data["user_input"]),
                "ai_response": serializer.validated_data["ai_response"],
                "correct_bool": serializer.validated_data["correct_bool"],
                "chat_rating": serializer.validated_data["chat_rating"],
                "correct_answer": translate_and_clean(
                    transformed_data.get("correct_answer", "")
                ),
                "metadata": {
                    **serializer.validated_data.get("metadata", {}),
                    "confidence": 0.97,
                },
                "timestamp": datetime.now().isoformat(),
                "search_score": 0.0,
            }

            # MongoDB operations
            try:
                db = self.get_db()
                logger.info("Creating text index for feedback search")
                db.feedback_data.create_index([("user_input", "text")])

                db_start = time.time()
                logger.info("Starting MongoDB Write Operations")
                db.feedback_data.insert_one(translated_data)
                logger.info(
                    f"MongoDB operation completed in {time.time() - db_start:.2f}s"
                )

            except Exception as db_error:
                logger.error(f"MongoDB operation failed: {str(db_error)}")
                return Response(
                    {"error": f"Database operation failed: {str(db_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")
            return Response(
                {"message": "Feedback saved successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": f"Failed to save feedback: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        start_time = time.time()
        logger.info("Starting feedback GET request")

        try:
            # Get pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            # MongoDB operations
            db_start = time.time()
            logger.info("Starting MongoDB Read Operations")
            db = self.get_db()
            total_count = db.feedback_data.count_documents({})

            cursor = (
                db.feedback_data.find({})
                .sort("timestamp", -1)
                .skip((page - 1) * limit)
                .limit(limit)
            )

            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")

            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")
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
                {"error": f"Failed to retrieve feedback: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def create_feedback_indexes():
    try:
        logger.info("Starting feedback index creation")
        start_time = time.time()

        db = MongoClient(settings.MONGODB_URI)[settings.MONGODB_DATABASE]
        db.feedback_data.create_index([("timestamp", -1)])

        total_time = time.time() - start_time
        logger.info(f"Feedback indexes created successfully in {total_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to create feedback indexes: {str(e)}")
