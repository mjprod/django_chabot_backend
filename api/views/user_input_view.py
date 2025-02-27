from api.translation import (
    translate_and_clean,
)

from api.conversation import (
    generate_user_input
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
import time
from datetime import datetime
from ..serializers import UserInputSerializer
from ..mixins.mongodb_mixin import MongoDBMixin

logger = logging.getLogger(__name__)

class UserInputView(MongoDBMixin, APIView):
    def post(self, request):
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

            # Extract input data
            prompt = serializer.validated_data["prompt"]
            user_id = serializer.validated_data.get("user_id", "None")
            logger.info(f"Received request from user_id: {user_id}, prompt: {prompt}")

            # Generate AI response
            generation_start = time.time()
            logger.info("Starting AI response generation")
            cleaned_prompt = translate_and_clean(prompt)
            generation = generate_user_input(cleaned_prompt)
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # Prepare response data
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
            logger.info("Starting MongoDB Write Operations in UserInputView")
            db = self.get_db()

            user_input_doc = {**response_data, "timestamp": datetime.now().isoformat()}
            db.user_inputs.insert_one(user_input_doc)
            logger.info(f"MongoDB operation completed in {time.time() - db_start:.2f}s")
            # Return the response
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(
                f"Error processing request: {str(e)}", exc_info=True  # Log stack trace
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            # Cleanup database connection
            if db is not None:
                self.close_db()
            # gc.collect()  # Explicit garbage collection for safety

            # Log total processing time
            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")
