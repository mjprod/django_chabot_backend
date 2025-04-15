from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging

from ..serializers import (
    UpdateAnswerBrain,
    InsertAnswerBrain
)

from api.chatbot import (
    update_document_by_custom_id,
    insert_document
)

from api.app.mongo import MongoDB

logger = logging.getLogger(__name__)

class ListReviewAndUpdateBrainView(APIView):
    def get(self, request, *args, **kwargs):
        db = None
        try:
            db = MongoDB.get_db()
            query = {
                "$expr": {
                    "$lt": [
                        {"$size": {"$ifNull": ["$review_status", []]}},
                        3
                    ]
                }
            }
            results = list(db.review_and_update_brain.find(query))
        
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
        
            return Response(results, status=status.HTTP_200_OK)
    
        except Exception as e:
                logger.exception("Error retrieving session ids")
                return Response(
                {"error": f"Error retrieving session ids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
class UpdateBrainView(APIView):
    def get(self, request):
        try:
            # Validate input data
            input_serializer = UpdateAnswerBrain(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            doc_id = input_serializer.validated_data["doc_id"]
            answer_en = input_serializer.validated_data["answer_en"]
            answer_ms = input_serializer.validated_data["answer_ms"]
            answer_cn = input_serializer.validated_data["answer_cn"]

            conversations = update_document_by_custom_id(
                doc_id, answer_en, answer_ms, answer_cn)
            
            data = {
                "conversations": conversations,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving dashboard counts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )    
        
class InsertBrainView(APIView):
    def post(self, request):
        try:
            # Validate input data
            input_serializer = InsertAnswerBrain(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            question_text = input_serializer.validated_data["question"]
            answer_en = input_serializer.validated_data["answer_en"]
            answer_ms = input_serializer.validated_data["answer_ms"]
            answer_cn = input_serializer.validated_data["answer_cn"]

            insert_document(
                question_text, answer_en, answer_ms, answer_cn)
            
            data = {
                "conversations": question_text,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving dashboard counts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )    
  