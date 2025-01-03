import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pymongo.errors import PyMongoError
from ..mixins.mongodb_mixin import MongoDBMixin
from ..serializers import CaptureFeedbackSerializer

# Initialize logger
logger = logging.getLogger(__name__)

class CaptureFeedbackView(MongoDBMixin, APIView):
    """
    APIView to capture and save user feedback in MongoDB.
    Supports both POST and GET requests.
    """

    def post(self, request):
        """
        Handles POST requests to save feedback in MongoDB.
        """
        db = None  # Initialize database connection variable
        try:
            logger.info("Receiving feedback data.")

            # Validate incoming data
            serializer = CaptureFeedbackSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation error: {serializer.errors}")
                return Response(
                    {"error": "Invalid data.", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare data for saving
            feedback_data = {
                **serializer.validated_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Connect to MongoDB
            db = self.get_db()
            db.feedback_data.insert_one(feedback_data)
            logger.info("Feedback successfully saved to MongoDB.")

            return Response(
                {"message": "Feedback saved successfully."},
                status=status.HTTP_201_CREATED,
            )

        except PyMongoError as db_error:
            logger.error(f"Database error while saving feedback: {str(db_error)}", exc_info=True)
            return Response(
                {"error": "Failed to save feedback due to database error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Unexpected error while saving feedback: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db:
                self.close_db()
                logger.info("Database connection closed.")

    def get(self, request):
        """
        Handles GET requests to retrieve feedback data.
        Supports pagination for better performance.
        """
        db = None  # Initialize database connection variable
        try:
            logger.info("Fetching feedback data.")

            # Connect to MongoDB
            db = self.get_db()

            # Pagination parameters
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
            skip = (page - 1) * limit

            # Fetch feedbacks from MongoDB
            feedbacks = db.feedback_data.find().sort("timestamp", -1).skip(skip).limit(limit)
            total_count = db.feedback_data.count_documents({})

            # Process results
            results = []
            for feedback in feedbacks:
                feedback["_id"] = str(feedback["_id"])  # Convert ObjectId to string
                results.append(feedback)

            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            logger.info(f"Fetched {len(results)} feedback records.")
            return Response(response_data, status=status.HTTP_200_OK)

        except PyMongoError as db_error:
            logger.error(f"Database error while fetching feedback: {str(db_error)}", exc_info=True)
            return Response(
                {"error": "Failed to fetch feedback data due to database error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Unexpected error while fetching feedback: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db:
                self.close_db()
                logger.info("Database connection closed.")