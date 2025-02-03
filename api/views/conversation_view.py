from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from datetime import datetime
from ..mixins.mongodb_mixin import MongoDBMixin
import time
from sentence_transformers import SentenceTransformer, util

from ..chatbot import (
    prompt_conversation,
    prompt_conversation_history,
    translate_and_clean,
    prompt_conversation_admin,
    check_answer_mongo_and_openai,
)
from ..serializers import (
    CompleteConversationsSerializer,
    PromptConversationSerializer,
    PromptConversationHistorySerializer,
    PromptConversationAdminSerializer,
)

from ai_config.ai_constants import (
    LANGUAGE_DEFAULT,
)

logger = logging.getLogger(__name__)

model = SentenceTransformer("sentence-t5-large")


def fuzzy_match_with_dynamic_context(self, query, collection_name, threshold=10):
    """
    Find the most semantically similar question-answer pair in MongoDB.
    :param query: User's input query.
    :param collection_name: Name of the MongoDB collection.
    :param threshold: Minimum similarity score to return results.
    :return: List of top matches sorted by similarity.
    """

    db = self.get_db()
    collection = db[collection_name]

    # Check if a text index exists and create it if not
    index_exists = False

    # Get all existing indexes
    indexes = collection.index_information()

    # Check if there's an existing text index
    for index_name, index_info in indexes.items():  # Unpack index name and info
        if index_info.get("key") == [
            ("user_input", "text")
        ]:  # Access 'key' in index_info
            index_exists = True
            break

    # Create the index if it doesn't exist
    if not index_exists:
        print("Creating text index on 'user_input'...")
        collection.create_index([("user_input", "text")])
        print("Text index created successfully.")
    else:
        print("Text index already exists.")

    # Fetch all documents with 'user_input' (question) and 'correct_answer' (answer)
    # documents = list(collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1}))
    documents = list(
        collection.find(
            {}, {"user_input": 1, "correct_answer": 1, "timestamp": 1}
        ).sort("timestamp", -1)
    )

    if not documents:
        return []

    # Compute embeddings for the query
    latest_questions = {}
    for doc in documents:
        user_input = doc.get("user_input", "").strip().lower()
        if user_input and user_input not in latest_questions:
            latest_questions[user_input] = doc  # Store only the latest entry

    # Compute embeddings for the query
    query_embedding = model.encode(query, convert_to_tensor=True)

    matches = []

    for (
        doc
    ) in latest_questions.values():  # Iterate only through unique latest questions
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        timestamp = doc.get("timestamp", "")

        # Merge question + answer for better context
        combined_text = f"Q: {user_input} A: {correct_answer}"

        # Compute embeddings for combined question + answer
        document_embedding = model.encode(combined_text, convert_to_tensor=True)

        # Compute similarity using embeddings
        similarity = (
            util.pytorch_cos_sim(query_embedding, document_embedding).item() * 100
        )

        # Word Overlap Score (Ensures proper nouns like 'Glauco' match better)
        query_words = set(query.lower().split())
        answer_words = set(correct_answer.lower().split())
        overlap_score = (
            len(query_words & answer_words) / max(len(query_words), 1)
        ) * 100

        # Final Weighted Similarity: 90% on Answer, 10% on Overlap Boost
        final_similarity = (similarity * 0.9) + (overlap_score * 0.1)
        final_similarity = min(final_similarity, 100)

        # Only include matches above the threshold
        if final_similarity >= threshold:
            matches.append(
                {
                    "similarity": final_similarity,
                    "user_input": user_input,
                    "correct_answer": correct_answer,
                    "timestamp": timestamp,
                }
            )

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Return the first correct_answer if matches exist, otherwise return False
    if matches:
        # Check if the first match has a similarity score greater than 80
        if matches[0]["similarity"] > 80:
            best_answer = matches[0]["correct_answer"]
            print("\nHigh Similarity Match Found:")
            print(best_answer)
            return best_answer  # Return immediately if it's a strong match

        # Otherwise, proceed with OpenAI validation
        limited_matches = matches[:5]

        openai_response = check_answer_mongo_and_openai(query, limited_matches)

        if openai_response:
            print("\nOpenAI Response:")
            print(openai_response)
            return openai_response
        else:
            print("No matches found.")
    else:
        print("No matches found.")


class PromptConversationHistoryView(MongoDBMixin, APIView):
    def post(self, request):
        try:
            # db = self.get_db()
            # Log start of request processing
            logger.info("Starting prompt_conversation_history request")
            start_time = time.time()

            # Get the header value as a string
            use_mongo_str = request.GET.get(
                "use_mongo", "0"
            )  # Default to "0" if not provided
            use_mongo = use_mongo_str in ("1", "true", "yes")
            print("Mongo: " + str(use_mongo))

            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            print("Language " + language)

            # Validate input data
            serializer = PromptConversationHistorySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = serializer.validated_data["prompt"]
            conversation_id = serializer.validated_data["conversation_id"]
            user_id = serializer.validated_data["user_id"]

            if use_mongo:
                print("Using Mongo DB")
                # Search for the answer on mongo db

                response = fuzzy_match_with_dynamic_context(
                    self=self,
                    query=prompt,
                    collection_name="feedback_data_" + language,
                    threshold=10,
                )
                print(response)
                if response:
                    time.sleep(5)
                    return Response(response, status=status.HTTP_200_OK)

            # Generate AI response with timing
            generation_start = time.time()
            logger.info("Starting AI answer generation")
            response = prompt_conversation_history(
                self,
                user_prompt=translate_and_clean(prompt),
                conversation_id=conversation_id,
                admin_id="",
                bot_id="",
                user_id=user_id,
            )
            logger.info(
                f"AI Generation completed in {time.time() - generation_start:.2f}s"
            )

            # this is the response data that is sent to user
            response_data = {
                "conversation_id": conversation_id,
                "user_input": prompt,
                "generation": response["generation"],
                "language": language,
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
        # finally:
        # if db is not None:
        # self.close_db()

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = self.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.close_db()


class CompleteConversationsView(MongoDBMixin, APIView):
    def get(self, request):
        db = None
        start_time = time.time()
        logger.info("Starting complete_conversations GET request")

        try:
            # Get pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            # Connect to MongoDB
            db = self.get_db()
            logger.info("Connected to MongoDB")

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
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
                results.append(doc)

            logger.info(f"Retrieved {len(results)} conversations from MongoDB")

            # Prepare response
            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            logger.info(
                f"Total request processing time: {time.time() - start_time:.2f}s"
            )

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
        finally:
            # Cleanup database connection
            if db is not None:
                self.close_db()

    def post(self, request):
        db = None
        start_time = time.time()
        logger.info("Starting complete_conversations POST request")

        try:
            # Log incoming request details
            logger.info(f"Request Data: {request.data}")
            logger.info(f"Request Content-Type: {request.content_type}")
            logger.info(f"Request Headers: {request.headers}")

            # Validate request data
            logger.info("Validating request data")
            serializer = CompleteConversationsSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare document for MongoDB
            logger.info("Starting MongoDB Write Operations")
            conversation_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "messages": serializer.validated_data["messages"],
                "timestamp": datetime.utcnow().isoformat(),  # Use UTC for consistency
            }

            db = self.get_db()
            result = db.complete_conversations.insert_one(conversation_data)
            inserted_id = str(result.inserted_id)

            # Prepare and return response
            response_data = {
                "message": "Conversation saved successfully",
                "conversation_id": inserted_id,
            }

            logger.info(
                f"MongoDB operation completed in {time.time() - start_time:.2f}s"
            )
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.close_db()
            # gc.collect()


"""
this is the new api for the prompt_conversation_admin,
it will be used for AI chat with the admin panel
"""


class PromptConversationAdminView(MongoDBMixin, APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation_admin request")

        try:

            # Get the header value as a string
            use_mongo_str = request.GET.get(
                "use_mongo", "0"
            )  # Default to "0" if not provided
            use_mongo = use_mongo_str in ("1", "true", "yes")
            print("Mongo: " + str(use_mongo))

            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            print("Language " + language)

            # Get language from query params or request data
            language_code = request.GET.get("language", LANGUAGE_DEFAULT)
            logger.info(f"Processing request for language: {language_code}")

            # Validate input data
            input_serializer = PromptConversationAdminSerializer(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = input_serializer.validated_data["prompt"]
            conversation_id = input_serializer.validated_data["conversation_id"]
            # user_id = input_serializer.validated_data["user_id"]

            if use_mongo:
                print("Using Mongo DB")
                # Search for the answer on mongo db
                response = fuzzy_match_with_dynamic_context(
                    self=self,
                    query=prompt,
                    collection_name="feedback_data_" + language,
                    threshold=10,
                )
                if response:
                    print("Correct answer found in Mongo DB")
                    response_data = {
                        "generation": response,
                        "conversation_id": conversation_id,
                        "is_last_message": "false",
                        "language": language,
                    }
                    time.sleep(6)
                    return Response(response_data, status=status.HTTP_200_OK)

            # Extract validated data
            validated_data = input_serializer.validated_data

            # Generate AI response
            # generation_start = time.time()
            logger.info("Starting AI response generation")

            response = prompt_conversation_admin(
                self,
                user_prompt=validated_data["prompt"],
                conversation_id=validated_data["conversation_id"],
                admin_id=validated_data.get("admin_id", ""),
                bot_id=validated_data.get("bot_id", ""),
                user_id=validated_data["user_id"],
                language_code=language_code,
            )

            # generation_time = time.time() - generation_start
            # if generation_time < 3:
            time.sleep(6)

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error in prompt_conversation_admin view: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = self.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.close_db()


class PromptConversationView(MongoDBMixin, APIView):
    def post(self, request):
        logger.info("Starting prompt_conversation_admin request")

        try:

            # Get the header value as a string
            use_mongo_str = request.GET.get(
                "use_mongo", "0"
            )  # Default to "0" if not provided
            use_mongo = use_mongo_str in ("1", "true", "yes")
            print("Mongo: " + str(use_mongo))

            # Language
            language = request.GET.get("language", LANGUAGE_DEFAULT)
            print("Language " + language)

            # Get language from query params or request data
            language_code = request.GET.get("language", LANGUAGE_DEFAULT)
            logger.info(f"Processing request for language: {language_code}")

            # Validate input data
            input_serializer = PromptConversationSerializer(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract validated data
            prompt = input_serializer.validated_data["prompt"]

            if use_mongo:
                print("Using Mongo DB")
                # Search for the answer on mongo db
                response = fuzzy_match_with_dynamic_context(
                    self=self,
                    query=prompt,
                    collection_name="feedback_data_" + language,
                    threshold=10,
                )
                if response:
                    response_data = {
                        "generation": response,
                    }
                    print("Correct answer found in Mongo DB")
                    return Response(response_data, status=status.HTTP_200_OK)

            # Extract validated data
            validated_data = input_serializer.validated_data

            # Generate AI response
            # generation_start = time.time()
            logger.info("Starting AI response generation")

            response = prompt_conversation(
                self,
                user_prompt=validated_data["prompt"],
                language_code=language_code,
            )

            # generation_time = time.time() - generation_start
            # if generation_time < 3:
            time.sleep(6)

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error in prompt_conversation_admin view: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        db = None
        try:
            # Get conversation_id from query params
            conversation_id = request.query_params.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Connect to MongoDB and get conversation history
            db = self.get_db()
            conversation = db.conversations.find_one({"session_id": conversation_id})

            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # for our response data we have the updated_at
            response_data = {
                "conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "translations": conversation.get("translations", []),
                "user_id": conversation.get("user_id"),
                "updated_at": conversation.get("updated_at"),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve conversation history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if db is not None:
                self.close_db()
