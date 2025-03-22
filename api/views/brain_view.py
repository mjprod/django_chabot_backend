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
        

class UpdateReviewStatusView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Update the review_status field of a document.
        Expects a JSON payload with:
            - doc_id: your custom document id (e.g. "0072")
            - review_status: a list of language codes (e.g. ["en", "ms"])
        """
        data = request.data
        doc_id = data.get("doc_id")
        review_status = data.get("review_status")
        review_text = data.get("review_text")

        if not doc_id or not review_status:
            return Response(
                {"error": "doc_id and review_status are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        db = None
        try:

            db = MongoDB.get_db()
            # Build the field path for the answer text, e.g., "answer.detailed.en"
            field_path = f"answer.detailed.{review_status}"
            
            # Update operation:
            #  - $set to update the specific language answer text
            #  - $addToSet to add the language code to review_status if not already present
            result = db.review_and_update_brain.update_one(
                {"id": doc_id},
                {
                    "$set": {field_path: review_text},
                    "$addToSet": {"review_status": review_status}
                }
            )
            
            if result.modified_count > 0:
                return Response(
                    {"message": f"Document {doc_id} updated successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"Document {doc_id} not found or not updated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.exception("Error updating review_status")
            return Response(
                {"error": f"Error updating review_status: {str(e)}"},
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
        
class PreBrainView(APIView):
     def get(self, request):
        db = None
        try:
            db = MongoDB.get_db()
            lists = list(db.band_aid_send_super_admin.find({}))
            for item in lists:
                item["_id"] = str(item["_id"]) 
            return Response(lists, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving lists: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )