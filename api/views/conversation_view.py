from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging
from datetime import datetime
from ..mixins.mongodb_mixin import MongoDBMixin
import time

from rapidfuzz import fuzz

from api.chatbot import (
    check_answer_mongo_and_openai,
    extrair_knowledge_items,
    update_chroma_document,
    update_document_by_custom_id,
    get_store,
)

from api.conversation import (
    prompt_conversation,
    prompt_conversation_admin,
 )

from ..serializers import (
    PromptConversationSerializer,
    PromptConversationAdminSerializer,
    UpdateAnswerBrain,
)

from ai_config.ai_constants import (
    LANGUAGE_DEFAULT,
)

from api.views.brain_file_reader import (
    get_document_count,
)

logger = logging.getLogger(__name__)

def fuzzy_match_with_dynamic_context(
    self, query, collection_name, threshold, language="en"
):
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

    # Fetch all documents with 'user_input' and 'correct_answer'

    documents = list(
        collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1})
    )

    if not documents:
        print(f"No documents found in collection '{collection_name}'.")
        return []

    matches = []

    for doc in documents:
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        timestamp = doc.get("timestamp", "")

        combined_text = f"{user_input} {correct_answer} {timestamp}".strip()

        # Calculate fuzzy similarity
        similarity = fuzz.partial_ratio(query, combined_text)
        # Only include matches above the threshold
        if similarity >= threshold:
            matches.append({"similarity": min(similarity, 100), **doc})

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Return the first correct_answer if matches exist, otherwise return False
    for match in matches:
        match["timestamp"] = match.get("timestamp", "")  # Ensure field exists
        if isinstance(match["timestamp"], str):  # Convert timestamp string to datetime
            try:
                match["timestamp"] = datetime.fromisoformat(match["timestamp"])
            except ValueError:
                match["timestamp"] = datetime.min

    # Sort by similarity (descending) and then by timestamp (latest first)
    matches = sorted(
        matches, key=lambda x: (-x["similarity"], -x["timestamp"].timestamp())
    )

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
                    language=language,
                )
                if response:
                    print("Correct answer found in Mongo DB")
                    response_data = {
                        "generation": response,
                        "conversation_id": conversation_id,
                        "is_last_message": "false",
                        "language": language,
                    }
                    # time.sleep(6)
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
        logger.info("Starting prompt_conversation request")

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
                    language=language,
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
                store=get_store,
                language_code=language_code,
            )

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

class ConversationDetailView(MongoDBMixin, APIView):
    def get(self, request, conversation_id):
        db = None
        start_time = time.time()
        try:
            db = self.get_db()
            
            conversation = db.conversations.find_one({"session_id": conversation_id})            
            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Converte o ObjectId para string
            conversation["_id"] = str(conversation["_id"])
            
            return Response(conversation, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()

class AllConversationsIdsView(MongoDBMixin, APIView):
    def get(self, request):
        db = None
        try:
            db = self.get_db()
            sessions = list(db.conversations.find({}, {"session_id": 1, "_id": 0}))
            return Response(sessions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving session ids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()


class UpdateKnowledgeView(MongoDBMixin, APIView):
    def post(self, request):
        db = None
        try:
            conversation_id = request.data.get("conversation_id")
            if not conversation_id:
                return Response(
                    {"error": "conversation_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            db = self.get_db()
            # Busca a conversa usando o session_id
            conversation = db.conversations.find_one({"session_id": conversation_id})
            if not conversation:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            knowledge_items = extrair_knowledge_items(conversation)
            
            
            # Retorna os itens extraídos (candidatos) sem verificar no brain
            return Response({
                "message": "Candidate knowledge items extracted.",
                "candidate_items": knowledge_items,
                "count": len(knowledge_items)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error extracting candidate knowledge: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()

class DeleteConversationView(MongoDBMixin, APIView):
    def delete(self, request, *args, **kwargs):
        # Obtém o conversation_id dos kwargs (já que está na URL)
        conversation_id = kwargs.get("conversation_id")
        if not conversation_id:
            return Response(
                {"error": "conversation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        db = None
        try:
            db = self.get_db()
            result = db.conversations.delete_one({"session_id": conversation_id})
            if result.deleted_count == 0:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"message": "Conversation deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error deleting conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()

class FinaliseConversationView(MongoDBMixin, APIView):
    def post(self, request, *args, **kwargs):
        # Get the conversation_id from the URL kwargs
        conversation_id = kwargs.get("conversation_id")
        if not conversation_id:
            return Response(
                {"error": "conversation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        db = None
        try:
            db = self.get_db()
            # Update the conversation document by setting 'status' to 'done'
            result = db.conversations.update_one(
                {"session_id": conversation_id},
                {"$set": {"status": "done"}}
            )
            if result.matched_count == 0:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"message": "Conversation finalized successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error finalizing conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()
                
class FinaliseAllConversationsView(MongoDBMixin, APIView):
    """
    This view finalizes all conversations by setting their status to "done".
    """
    def post(self, request, *args, **kwargs):
        db = None
        try:
            db = self.get_db()
            # Update all documents in the "conversations" collection,
            # setting the "status" field to "done"
            result = db.conversations.update_many(
                {},
                {"$set": {"status": "done"}}
            )
            return Response(
                {
                    "message": "All conversations finalized successfully.",
                    "modified_count": result.modified_count
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error finalizing all conversations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()

def categorize_conversation_resolution(conversation: dict, db) -> dict:
    """
    Analyzes the conversation by extracting knowledge items.
    
    If candidate items are present:
      - If the short answer indicates that there is no relevant resolution,
        the conversation is categorized as "useless": it is inserted into the
        'read_conversation_useless' collection and removed from 'conversations'.
      - Else, if the candidate item has a non-empty 'raw' field,
        the candidate answer is added to the conversation, which is then moved
        to 'read_conversation_into_brain' and deleted from 'conversations'.
      - Else if the 'raw' field is empty,
        the conversation is updated with the candidate answer, moved to the
        'read_conversation_no_brain' collection, and deleted from 'conversations'.
        
    Returns:
        A dictionary representing the candidate answer if a relevant resolution is found,
        or an empty dictionary if the conversation is categorized as useless.
    """
    candidate_items = extrair_knowledge_items(conversation)
    
    if candidate_items:
        candidate_item = candidate_items[0]
        answer = candidate_item.get("answer", {})
        # Retrieve and standardize the short answer text
        short_text = answer.get("detailed", {}).get("en", "").strip().lower()
        
        # If the short answer explicitly indicates no relevant resolution
        if short_text == "there is no relevant resolution in this conversation.":
            db.read_conversation_useless.insert_one(conversation)
            db.conversations.delete_one({"session_id": conversation["session_id"]})
            return {}
        
        # Add the candidate answer into the conversation object.
        conversation["extracted_answer"] = answer
        
        # Check the 'raw' field in the candidate answer
        raw_value = answer.get("raw")
        if raw_value:
            # If 'raw' is not empty, move to 'read_conversation_into_brain'
            db.read_conversation_into_brain.insert_one(conversation)
        else:
            # If 'raw' is empty, move to 'read_conversation_no_brain'
            db.read_conversation_no_brain.insert_one(conversation)
            
        # Remove the conversation from the main 'conversations' collection
        db.conversations.delete_one({"session_id": conversation["session_id"]})
        
        return answer
    else:
        # If no candidate items were extracted, treat the conversation as useless.
        db.read_conversation_useless.insert_one(conversation)
        db.conversations.delete_one({"session_id": conversation["session_id"]})
        return {}

class SeparateConversationsView(MongoDBMixin, APIView):
    """
    This view retrieves all conversation session IDs from the "conversations" collection.
    For each conversation with status "done", it processes the conversation using the
    categorize_conversation_resolution function and moves it to the appropriate collection.
    It returns an array that shows which session ID was moved to which collection.
    """
    def get(self, request):
        db = None
        results = []
        try:
            db = self.get_db()
            # Retrieve only the "session_id" field from all conversations
            sessions = list(db.conversations.find({}, {"session_id": 1, "_id": 0}))
            logger.debug(f"Retrieved session IDs: {sessions}")

            for session in sessions:
                session_id = session.get("session_id")
                if not session_id:
                    logger.warning("Skipping a conversation with missing session_id.")
                    continue

                # Retrieve the full conversation based on session_id
                conversation = db.conversations.find_one({"session_id": session_id})
                if conversation is None:
                    logger.warning(f"Conversation with session_id {session_id} not found.")
                    continue

                # Process only conversations with status "done"
                if conversation.get("status") != "done":
                    logger.debug(f"Skipping conversation {session_id} with status: {conversation.get('status')}")
                    continue

                # Call the categorization method to process the conversation.
                candidate_answer = categorize_conversation_resolution(conversation, db)

                # Determine the category based on the candidate answer:
                if candidate_answer == {}:
                    category = "useless"
                else:
                    if candidate_answer.get("raw"):
                        category = "into_brain"
                    else:
                        category = "no_brain"

                results.append({
                    "session_id": session_id,
                    "category": category
                })
                logger.debug(f"Processed conversation {session_id} categorized as {category}")

            return Response({
                "message": "Conversations processed successfully.",
                "results": results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error processing conversations")
            return Response({
                "error": f"Error processing conversations: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if db is not None:
                self.close_db()

class DashboardCountsView(MongoDBMixin, APIView):
    """
    This endpoint returns the counts for:
      - Total conversations
      - Useless conversations
      - No Brain conversations
      - Into Brain conversations
      - Total knowledge in brain (sum of the three latter)
    """
    def get(self, request):
        db = None
        try:
            db = self.get_db()
            conversations_count = db.conversations.count_documents({})
            useless_count = db.read_conversation_useless.count_documents({})
            no_brain_count = db.read_conversation_no_brain.count_documents({})
            into_brain_count = db.read_conversation_into_brain.count_documents({})
            brain_count =  get_document_count()

            data = {
                "conversations": conversations_count,
                "useless": useless_count,
                "noBrain": no_brain_count,
                "intoBrain": into_brain_count,
                "brainCount": brain_count,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving dashboard counts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if db is not None:
                self.close_db()



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
            new_answer = input_serializer.validated_data["new_answer"]

            conversations = update_document_by_custom_id(
                doc_id, new_answer)
            
            data = {
                "conversations": conversations,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving dashboard counts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        