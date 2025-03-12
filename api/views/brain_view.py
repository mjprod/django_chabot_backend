from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework import serializers
from ..api_serializers.review_knowledge import (
    ReviewKnowledgeSerializer,
    BulkDeleteSerializer
)

from ..utils.utils import CustomPagination

import logging

from ..serializers import (
    UpdateAnswerBrain,
)

from api.chatbot import (
    update_document_by_custom_id,
)

from api.app.mongo import MongoDB
from bson import ObjectId


logger = logging.getLogger(__name__)

REVIEW_COLLECTION_NAME="review_and_update_brain"

class ReviewKnowledge(APIView):
    pagination_class = CustomPagination
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)        
        if id:
            return self.retrieve(id)
        
        # proceed with the list logic when id is not provided
        return self.list(request)
    
    def retrieve(self, document_id):
        """
            retrive single document by '_id'
            Endpoint: registered as review_knowledge/<str:id>/
        """
        try:
            # Retrieve the document with the specified review ID
            query = {"_id": ObjectId(document_id)}
            result = MongoDB.query_collection(collection_name=REVIEW_COLLECTION_NAME, query=query)

            if result:
                logger.info(f"{result}")
                # Convert _id to string and return the document
                result = result[0]
                result["_id"] = str(result["_id"])
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)


        except Exception as e:
            logger.exception(f"Error retrieving review with id {document_id}")
            return Response(
                {"error": f"Error retrieving review: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """
            List view for retrieving a paginated list of items based on provided query parameters.

            Query Parameters:
            - page (int): The page number to retrieve.
            - page_size (int): The number of items per page.
            - category (str): Filter items by category.
            - language (str): Filter items by language.

            Returns:
            - Response: A paginated list of items matching the applied filters.
        """

        # get filters
        category = request.query_params.get('category', None)
        language=request.query_params.get('language', None)
        comebined_query = {"$and":[]}
        try:
            # query 1:  retrieve documents do not have complete review status
            await_to_be_reviewed_query = {
                "$expr": {
                    "$lt": [
                        {"$size": {"$ifNull": ["$review_status", []]}},
                        3
                    ]
                }}
            
            comebined_query["$and"].append(await_to_be_reviewed_query)

            # apply filters
            if category:
                comebined_query["$and"].append({"metadata.category": {"$in": [category]}})
            if language:
                question_language_filter ={f"question.languages.{language}": {"$exists": "true"}}
                answer_language_filter ={f"answer.detailed.{language}": {"$exists": "true"}}
                comebined_query["$and"].extend([question_language_filter, answer_language_filter])

            results = MongoDB.query_collection(collection_name=REVIEW_COLLECTION_NAME,
                                               query=comebined_query)
            
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            paginator = self.pagination_class()
            paginated_results = paginator.paginate_queryset(results, request)
            
            return Response({
                "count": paginator.page.paginator.count,
                "total_pages": paginator.page.paginator.num_pages,
                "previous": paginator.get_previous_link(),
                "next": paginator.get_next_link(),
                "results": paginated_results,
            }, status=status.HTTP_200_OK)
        
            # return Response(results, status=status.HTTP_200_OK)
    
        except Exception as e:
                logger.exception("Error retrieving session ids")
                return Response(
                    {"error": f"Error retrieving session ids: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def delete(self, request):
        """
        Handles deletion of multiple review knowledge based on a list of IDs.
        """
        try:
            serializer = BulkDeleteSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_ids = serializer.validated_data["ids"]
            object_ids = [ObjectId(_id) for _id in validated_ids]

            # Bulk delete from MongoDB
            result = MongoDB.delete_many(REVIEW_COLLECTION_NAME,{"_id": {"$in": object_ids}})

            if result.deleted_count > 0:
                return Response({"message": f"{result.deleted_count} reviews deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No matching reviews found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception("Error in bulk deleting reviews")
            return Response(
                {"error": f"Error in bulk deleting reviews: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 

    # create a new knowledge to review
    def post(self, request, *args, **kwargs):
        pass

    # update knowledge/status in the review list 
    def patch(self, request, *args, **kwargs):

        """
        Update the document in the review list.
        
        Expected JSON payload:
        - id (str): The ID of the document to update.
        - language (str): The language of the review.
        - question (str): Updated question details.
        - answer (str): Updated answer details.
        - status (int): The new review status (e.g., '1: need approve', '2: pre-approved', '3: approved', '4: reject').
        
        Returns:
        - Response: Updated document or error message.
        """

        try:
            serializer = ReviewKnowledgeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data

            query = {"_id": ObjectId(data.get("id"))}
            update_fields = {}
            
            update_fields = {key: value for key, value in data.items() if key != "id"}

            # need to write a param and database key mapping function
            
            update_query = {"$set": update_fields}
            updated_document = MongoDB.update_one_document(collection_name=REVIEW_COLLECTION_NAME,
                                                           query=query, 
                                                           update=update_query)
            
            if updated_document:
                return Response({"message": "Review updated successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Review not found or update failed."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("Error updating review status")
            return Response(
                {"error": f"Error updating review: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReviewKnowledgeDashboard(APIView):
    def get(self, request, *args, **kwargs):
        aggregation = [
            { 
                "$unwind": "$metadata.category"
            },
            { 
                "$group": {
                    "_id": "$metadata.category",
                    "count": { "$sum": 1 }
                }
            },
            {
                "$project": {
                    "category": "$_id",  # Rename _id to category
                    "count": 1,  # Keep the count field
                    "_id": 0  # Remove the _id field
                }
            },
            { 
                "$sort": { "count": -1 }
            }
        ]

        try:
            results = MongoDB.aggregate_collection(
                collection_name=REVIEW_COLLECTION_NAME,
                aggregation=aggregation
            )
            
            # If no results found, raise a NotFound exception
            if not results:
                raise NotFound("No categories found in the collection.")

            categories = []
            for category in results:
                category_name = category["category"]
                # Add color to the category
                # category["color"] = self._get_category_color(category_name).value
                categories.append(category)
            
            # Return the results as a JSON response
            return Response(
                {"categories_count": categories},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Handle other errors
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    # def _get_category_color(self,category_id):
    #     category_mapping = {
    #         "finance": CategoryColorEnum.FINANCE,
    #         "technical": CategoryColorEnum.TECHNOLOGY,
    #         "account_management": CategoryColorEnum.ACCOUNT,
    #         "game": CategoryColorEnum.FOURDLOTTO,
    #         "sports_betting": CategoryColorEnum.FOURDLOTTO,
    #         "policy_explanation": CategoryColorEnum.SECURITY,
    #         "encouragement": CategoryColorEnum.FEEDBACK,
    #         "points_shop": CategoryColorEnum.POINTSSHOP,
    #         "other":CategoryColorEnum.OTHER
    #     }
        
    #     return category_mapping.get(category_id, CategoryColorEnum.OTHER)


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
        

