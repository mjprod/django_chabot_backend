from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..mixins.mongodb_mixin import MongoDBMixin

import logging

from ..serializers import (
    BrainSerialzer,
)

from api.chatbot import (
    update_brain_document_by_id
)

logger = logging.getLogger(__name__)

class BrainView(MongoDBMixin,APIView):
    def post(self, request):

        # Validate input data
        input_serializer = BrainSerialzer(data=request.data)
        if not input_serializer.is_valid():
            logger.error(f"Validation failed: {input_serializer.errors}")
            return Response(
                {"error": "Invalid input data", "details": input_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_id = input_serializer.validated_data["doc_id"]

        # check if the conversation exists in mongo db
        db = self.get_db()
        conversation = db.review_and_update_brain.find_one({"id": doc_id})

        if not conversation:
            return Response(
                {"error": "Conversation not found in the review list"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            # check if the review status is finalised in mongo db
            review_status = conversation.get("review_status")
            if len(review_status)!= 3:
                return Response(
                    {"error": "Conversation review is not finalised"},
                    status=status.HTTP_400_BAD_REQUEST)

        # update the answer in knowledge base (chromadb)
        try:
            update_brain_document_by_id(doc_id, conversation)
            data = {
                "details": "Knowledge updated successfully",
            }
            return Response(data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": f"{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   