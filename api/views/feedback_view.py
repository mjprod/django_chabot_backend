import logging
import time

from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..mixins.mongodb_mixin import MongoDBMixin
from ..serializers import CaptureFeedbackSerializer

from ..chatbot import (
    translate_and_clean,
    translate_en_to_ms,
    translate_en_to_cn,
)

# Initialize logger
logger = logging.getLogger(__name__)


class CaptureFeedbackView(MongoDBMixin, APIView):
    def _process_correct_answer_translations(self, correct_answer):
        """Process and translate our correct answer into the languages needed"""
        if not correct_answer:
            return []
        logger.info(f"Processing translations for: {correct_answer}")
        translations = [
            {
                "language": "en",
                "text": correct_answer
            }
        ]
        try:
            # Try Malay translation
            logger.info("Attempting Malay translation...")
            translated_ms = translate_en_to_ms(correct_answer)
            logger.info(f"Malay translation result: {translated_ms}")
            if translated_ms and isinstance(translated_ms, dict):
                translations.append({
                    "language": "ms",
                    "text": translated_ms.get('text', '')  # Extract just the text,
                })
            else:
                logger.error("Malay translation returned empty or invalid format") 
        except Exception as e:
            logger.error(f"Error in Malay translation: {str(e)}")
        try:
            # Try Chinese translation
            logger.info("Attempting Chinese translation...")
            translated_cn = translate_en_to_cn(correct_answer)
            logger.info(f"Chinese translation result: {translated_cn}")
            if translated_cn and isinstance(translated_cn, dict):
                translations.append({
                    "language": "cn",
                    "text": translated_cn.get('text', '')  # Extract just the text
                })
            else:
                logger.error("Chinese translation returned empty or invalid format")     
        except Exception as e:
            logger.error(f"Error in Chinese translation: {str(e)}")
        logger.info(f"Final translations array: {translations}")
        return translations

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
                "correct_answer": self._process_correct_answer_translations(
                    request.data.get("correct_answer", "")
                ),
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
                "correct_answer": serializer.validated_data["correct_answer"],
                "metadata": {
                    **serializer.validated_data.get("metadata", {}),
                    "confidence": 0.97,
                },
                "timestamp": datetime.now().isoformat(),
                "search_score": 0.0,
            }

            # MongoDB operations
            db = self.get_db()
            logger.info("Creating text index for feedback search")
            db.feedback_data.create_index([("user_input", "text")])
            db_start = time.time()
            logger.info("Starting MongoDB Write Operations")
            db.feedback_data.insert_one(translated_data)
            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")
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
