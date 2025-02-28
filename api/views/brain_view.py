from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from ..mixins.mongodb_mixin import MongoDBMixin

logger = logging.getLogger(__name__)

class ListReviewAndUpdateBrainView(MongoDBMixin, APIView):
    def get(self, request, *args, **kwargs):
        db = None
        try:
            db = self.get_db()
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
        finally:
            if db is not None:
                self.close_db()

class UpdateReviewStatusView(MongoDBMixin, APIView):
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
        
        if not doc_id or not review_status:
            return Response(
                {"error": "doc_id and review_status are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        db = None
        try:
            db = self.get_db()
            result = db.review_and_update_brain.update_one(
                {"id": doc_id},
                {
                    "$push": {
                        "review_status": review_status
                    }
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
        finally:
            if db is not None:
                self.close_db()