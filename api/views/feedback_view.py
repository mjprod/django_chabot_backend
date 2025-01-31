import logging
import time
import asyncio

from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..mixins.mongodb_mixin import MongoDBMixin
from ..serializers import CaptureFeedbackSerializer, CaptureFeedbackSimpleSerializer

from ..chatbot import (
    translate_and_clean,
    generate_translations,
)

from ai_config.ai_constants import LANGUAGE_DEFAULT

# Initialize logger
logger = logging.getLogger(__name__)


# TODO: Implement confidence score for feedback
"""
class CaptureFeedbackView(MongoDBMixin, APIView):
    def post(self, request):
        start_time = time.time()
        logger.info("Starting feedback POST request")
        try:
            # Transform incoming data to match serializer format
            transformed_data = {
                "conversation_id": request.data.get("conversation_id", ""),
                "user_input": request.data.get("prompt", ""),
                "ai_response": request.data.get("generation", ""),
                "correct_bool": request.data.get("correct_bool", False),
                "chat_rating": request.data.get("chat_rating", 0),
                "correct_answer": request.data.get("correct_answer", ""),
                "metadata": {
                    **request.data.get("metadata", {}),
                    "user_id": request.data.get("user_id"),
                    "translations": request.data.get("translations", []),
                    "confidence": 0.0,  # Add fixed confidence score
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

            translations = asyncio.run(
                generate_translations(transformed_data.get("correct_answer", ""))
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
                "metadata": translations,
                "timestamp": datetime.now().isoformat(),
                "search_score": 0.0,
            }

            # MongoDB operations
            try:
                db = self.get_db()
                logger.info("Creating text index for feedback search")
                # db.feedback_data.create_index([("user_input", "text")])

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
            finally:
                if db is not None:
                    self.close_db()

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
"""


class CaptureFeedbackView(MongoDBMixin, APIView):
    def post(self, request):
        start_time = time.time()
        logger.info("Starting feedback POST request")
        try:
            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            # Transform incoming data to match serializer format
            transformed_data = {
                "user_input": request.data.get("prompt", ""),
                "correct_answer": request.data.get("correct_answer", ""),
            }

            # Validate transformed data
            logger.info("Validating request data")
            serializer = CaptureFeedbackSimpleSerializer(data=transformed_data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process translations
            logger.info("Processing feedback translations")
            translated_data = {
                "user_input": transformed_data["user_input"],
                "correct_answer": transformed_data.get("correct_answer", ""),
                "ai_response": "",
                "correct_bool": False,
                "chat_rating": 0,
                "conversation_id": "",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "translations": [],
                    "confidence": 0.0,
                },
            }

            # MongoDB operations
            try:
                db = self.get_db()
                logger.info("Creating text index for feedback search")
                # db.feedback_data.create_index([("user_input", "text")])

                db_start = time.time()
                logger.info("Starting MongoDB Write Operations")

                language_collections = {
                    "en": "feedback_data_en",
                    "ms_MY": "feedback_data_ms_MY",
                    "zh_CN": "feedback_data_zh_CN",
                    "zh_TW": "feedback_data_zh_TW",
                }

                collection_name = language_collections.get(language)
                if not collection_name:
                    raise ValueError(f"Unsupported language: {language}")

                db[collection_name].insert_one(translated_data)
                logger.info(
                    f"MongoDB operation completed in {time.time() - db_start:.2f}s"
                )

            except Exception as db_error:
                logger.error(f"MongoDB operation failed: {str(db_error)}")
                return Response(
                    {"error": f"Database operation failed: {str(db_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            finally:
                if db is not None:
                    self.close_db()

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


class CaptureFeedbackMultiView(MongoDBMixin, APIView):
    def post(self, request):
        start_time = time.time()
        logger.info("Starting feedback POST request")

        # Language
        language = request.GET.get("language", LANGUAGE_DEFAULT)

        # Debug: print the boolean value
        print(f"Use MongoDB: {language}")

        try:
            # Transform incoming data to match serializer format
            transformed_data = {
                "conversation_id": request.data.get("conversation_id", ""),
                "user_input": request.data.get("prompt", ""),
                "ai_response": request.data.get("generation", ""),
                "correct_bool": request.data.get("correct_bool", False),
                "chat_rating": request.data.get("chat_rating", 0),
                "correct_answer": request.data.get("correct_answer", ""),
                "metadata": {
                    **request.data.get("metadata", {}),
                    "user_id": request.data.get("user_id"),
                    "translations": request.data.get("translations", []),
                    "confidence": 0.0,  # Add fixed confidence score
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

            translations = asyncio.run(
                generate_translations(transformed_data.get("correct_answer", ""))
            )

            # Process translations
            logger.info("Processing feedback translations")
            translated_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "user_input": transformed_data["user_input"],
                "ai_response": serializer.validated_data["ai_response"],
                "correct_bool": serializer.validated_data["correct_bool"],
                "chat_rating": serializer.validated_data["chat_rating"],
                "correct_answer": (transformed_data.get("correct_answer", "")),
                "metadata": translations,
                "timestamp": datetime.now().isoformat(),
                "search_score": 0.0,
            }

            # MongoDB operations
            try:
                db = self.get_db()
                logger.info("Creating text index for feedback search")
                # db.feedback_data.create_index([("user_input", "text")])

                db_start = time.time()
                logger.info("Starting MongoDB Write Operations")

                language_collections = {
                    "en": "feedback_data_en",
                    "ms_MY": "feedback_data_ms_MY",
                    "zh_CN": "feedback_data_zh_CN",
                    "zh_TW": "feedback_data_zh_TW",
                }

                collection_name = language_collections.get(language)
                if not collection_name:
                    raise ValueError(f"Unsupported language: {language}")

                db[collection_name].insert_one(translated_data)
                logger.info(
                    f"MongoDB operation completed in {time.time() - db_start:.2f}s"
                )

            except Exception as db_error:
                logger.error(f"MongoDB operation failed: {str(db_error)}")
                return Response(
                    {"error": f"Database operation failed: {str(db_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            finally:
                if db is not None:
                    self.close_db()

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
