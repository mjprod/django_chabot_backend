import json
import os
from datetime import datetime

from bson import ObjectId
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import (
    ConversationMetaData,
    GradeConfidenceLevel,
    GradeDocuments,
    confidence_grader,
    format_docs,
    generate_answer,
    retrieval_grader,
    save_interaction,
    save_interaction_outcome,
    translate_and_clean,
    translate_en_to_cn,
    translate_en_to_ms,
)
from .serializers import (
    AIResponseSerializer,
    CaptureSummaryMultilangSerializer,
    CaptureSummarySerializer,
    ChatRatingSerializer,
    CompleteConversationsSerializer,
    ConversationMetadataSerializer,
    CorrectBoolSerializer,
    IncorrectAnswerResponseSerializer,
    MessageDataSerializer,
    MessageSerializer,
    NewAIResponseSerializer,
    NewCaptureSummaryMultilangSerializer,
    NewCaptureSummarySerializer,
    NewUserInputSerializer,
    NewViewSummarySerializer,
    PromptConversationSerializer,
    UserInputSerializer,
    ViewSummarySerializer,
)


# added mongodb base view class
class MongoDBMixin:
    def get_db(self):
        client = MongoClient(settings.MONGODB_URI)
        return client[settings.MONGODB_DATABASE]


class UserInputView(APIView):
    def post(self, request):
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            user_id = serializer.validated_data["user_id"]

            # added the translation here
            cleaned_prompt = translate_and_clean(prompt)

            generation = generate_answer(cleaned_prompt)

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

            save_interaction(
                "user_input",
                {
                    "user_id": user_id,
                    "prompt": prompt,
                    "cleaned_prompt": cleaned_prompt,
                    "generation": generation["generation"],
                    "translations": generation["translations"],
                },
            )

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIResponseView(APIView):
    def post(self, request):
        serializer = AIResponseSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data["answer"]
            save_interaction("ai_response", {"answer": answer})
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewAIResponseView(MongoDBMixin, APIView):
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DATABASE]
        self.ai_responses = self.db.ai_responses
        # Create indexes for efficient querying
        self.ai_responses.create_index([("timestamp", -1)])
        self.ai_responses.create_index([("session_id", 1)])

    def post(self, request):
        try:
            serializer = AIResponseSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            answer = serializer.validated_data["answer"]

            # Create MongoDB document
            ai_response_doc = {
                "_id": ObjectId(),
                "answer": answer,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "ip_address": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "session_id": str(ObjectId()),
                    "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", "unknown"),
                },
            }

            # Save to MongoDB
            self.ai_responses.insert_one(ai_response_doc)

            # Prepare response
            response_data = {
                "answer": answer,
                "session_id": str(ai_response_doc["_id"]),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        try:
            # Pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))
            session_id = request.query_params.get("session_id")

            # Query filter
            query_filter = {}
            if session_id:
                query_filter["metadata.session_id"] = session_id

            # Get total count and paginated results
            total_count = self.ai_responses.count_documents(query_filter)
            cursor = (
                self.ai_responses.find(query_filter)
                .sort("timestamp", -1)
                .skip((page - 1) * limit)
                .limit(limit)
            )

            # Process results
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve AI responses: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data["is_correct"]
            save_interaction("correct_bool", {"is_correct": is_correct})
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data["rating"]
            save_interaction("chat_rating", {"rating": rating})
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncorrectAnswerResponseView(APIView):
    def post(self, request):
        serializer = IncorrectAnswerResponseSerializer(data=request.data)
        if serializer.is_valid():
            correct_answer = serializer.validated_data["incorrect_answer"]
            save_interaction(
                "incorrect_answer_response", {"correct_answer": correct_answer}
            )
            return Response(
                {"message": "Correct answer received"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptureSummaryView(APIView):
    def post(self, request):
        serializer = CaptureSummarySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            result = save_interaction("complete_interaction", data)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptureSummaryMultilangView(APIView):
    def post(self, request):
        serializer = CaptureSummaryMultilangSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Save to interaction_outcome.json with correct format
                outcome_data = {
                    "user_id": serializer.validated_data.get("user_id", 0),
                    "prompt": serializer.validated_data.get("prompt"),
                    "cleaned_prompt": serializer.validated_data.get("cleaned_prompt"),
                    "generation": serializer.validated_data.get("generation"),
                    "translations": serializer.validated_data.get("translations", []),
                    "correct_bool": serializer.validated_data.get("correct_bool"),
                    "correct_answer": serializer.validated_data.get("correct_answer"),
                    "chat_rating": serializer.validated_data.get("chat_rating"),
                }
                save_interaction_outcome(outcome_data)

                # Save to interactions.json
                interaction_data = {
                    "Date_time": datetime.now().isoformat(),
                    "Type": "complete_interaction",
                    "Data": outcome_data,
                }
                result = save_interaction("complete_interaction", interaction_data)

                return Response(
                    {
                        "status": "success",
                        "message": "Interaction saved successfully",
                        "data": result,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# changed the ViewSummary API to work for the new malay/english
class ViewSummaryView(APIView):
    def get(self, request):
        try:
            file_path = os.path.join(
                os.path.dirname(__file__), "../data/interactions.json"
            )

            if not os.path.exists(file_path):
                return Response(
                    {"error": "No data available"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                with open(file_path, "r") as f:
                    interactions = json.load(f)
                    if not isinstance(interactions, list):
                        return Response(
                            {"error": "Invalid data format"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            summaries = []
            for interaction in interactions:
                try:
                    if interaction.get("Type") == "user_input":
                        data = interaction.get("Data", {})
                        summary = {
                            "user_id": data.get("user_id", 0),
                            "Date_time": interaction.get("Date_time"),
                            "Question": data.get("prompt", ""),
                            "Cleaned_Question": data.get("cleaned_prompt", ""),
                            "generation": data.get("generation", ""),
                            "translations": data.get("translations", []),
                            "Question_correct": False,
                            "Correct_rating": 0,
                            "Correct_Answer": "",
                            "Metadata": {},
                        }
                        summaries.append(summary)
                except AttributeError:
                    continue  # Skip malformed entries

            return Response(summaries, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def save_to_json(self, filename, data):
        file_path = os.path.join(settings.BASE_DIR, "data", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a") as f:
            json.dump(data, f)
            f.write("\n")


# New API views functions here for history and conversation


class NewUserInputView(APIView):
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DATABASE]
        self.user_inputs = self.db.user_inputs
        # first go at the pagination
        self.user_inputs.create_index([("timestamp", -1)])
        self.user_inputs.create_index([("user_id", 1)])

    def post(self, request):
        try:
            # check the data for validity and return error if no good
            serializer = NewUserInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # fetch our data validated as prompt and user_id
            prompt = serializer.validated_data["prompt"]
            user_id = serializer.validated_data["user_id"]

            # Generate the rest of the answer via the response call
            response = generate_answer(
                user_prompt=prompt,
                session_id=str(ObjectId()),
                admin_id=request.data.get("admin_id", ""),
                agent_id=request.data.get("agent_id", ""),
                user_id=user_id,
            )

            # Create the mongodb interaction/object for storage
            user_input_doc = {
                "_id": ObjectId(),
                "user_id": user_id,
                "prompt": prompt,
                "cleaned_prompt": response.get("cleaned_prompt", prompt),
                "generation": response.get("generation", ""),
                "translations": response.get("translations", []),
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "ip_address": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "session_id": response.get("conversation", {}).get("session_id"),
                    "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", "unknown"),
                },
            }

            # Save to MongoDB
            self.user_inputs.insert_one(user_input_doc)

            # from the inserted document we take the relevant fields prep for the client
            response_data = {
                "user_id": user_id,
                "prompt": prompt,
                "generation": response.get("generation", ""),
                "translations": response.get("translations", []),
                "session_id": str(user_input_doc["_id"]),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        try:
            # Pagination parameters
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))
            user_id = request.query_params.get("user_id")

            # Query filter
            query_filter = {}
            if user_id:
                query_filter["user_id"] = user_id

            # Get total count and paginated results
            total_count = self.user_inputs.count_documents(query_filter)
            cursor = (
                self.user_inputs.find(query_filter)
                .sort("timestamp", -1)
                .skip((page - 1) * limit)
                .limit(limit)
            )

            # Process results
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            response_data = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "results": results,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user inputs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConversationHistoryView(MongoDBMixin, APIView):
    def get(self, request, session_id):
        db = self.get_db()
        conversations = db.conversations

        conversation = conversations.find_one({"session_id": session_id})
        if not conversation:
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        conversation["_id"] = str(conversation["_id"])
        return Response(conversation, status=status.HTTP_200_OK)

    def post(self, request, session_id):
        serializer = ConversationMetadataSerializer(data=request.data)
        if serializer.is_valid():
            conversation = ConversationMetaData(
                session_id=session_id,
                user_id=serializer.validated_data["user_id"],
                agent_id=serializer.validated_data["agent_id"],
                admin_id=serializer.validated_data["admin_id"],
            )
            save_conversation(conversation)
            return Response(conversation.to_dict(), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationMessagesView(APIView):
    def get(self, request, session_id):
        file_path = os.path.join(
            os.path.dirname(__file__), "../data/conversations.json"
        )
        if not os.path.exists(file_path):
            return Response([], status=status.HTTP_200_OK)

        with open(file_path, "r") as f:
            conversations = json.load(f)

        conversation = next(
            (conv for conv in conversations if conv["session_id"] == session_id), None
        )

        if conversation:
            return Response(conversation["messages"], status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)


class UserConversationsView(MongoDBMixin, APIView):
    def get(self, request, user_id):
        db = self.get_db()
        conversations = db.conversations

        user_conversations = []
        for conv in conversations.find({"user_id": user_id}):
            conv["_id"] = str(conv["_id"])
            user_conversations.append(conv)

        return Response(user_conversations, status=status.HTTP_200_OK)


class AgentConversationsView(APIView):
    def get(self, request, agent_id):
        file_path = os.path.join(
            os.path.dirname(__file__), "../data/conversations.json"
        )
        if not os.path.exists(file_path):
            return Response([], status=status.HTTP_200_OK)

        with open(file_path, "r") as f:
            conversations = json.load(f)

        agent_conversations = [
            conv for conv in conversations if conv["agent_id"] == agent_id
        ]

        return Response(agent_conversations, status=status.HTTP_200_OK)


# new api for start conversation
class PromptConversationView(MongoDBMixin, APIView):
    def post(self, request):
        try:
            serializer = PromptConversationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # takee the calidated data into variables
            prompt = serializer.validated_data["prompt"]
            conversation_id = serializer.validated_data["conversation_id"]
            user_id = serializer.validated_data["user_id"]

            # ai generated response goes here:
            response = generate_answer(
                user_prompt=prompt,
                session_id=conversation_id,
                admin_id="",  # added this for use later
                agent_id="",  # added this for user later aswell
                user_id=user_id,
            )

            # added the translations
            translations = []
            if response.get("translations"):
                translations = response["translations"]

            # Create new document instead of updating
            db = self.get_db()
            conversation_data = {
                "conversation_id": conversation_id,
                "prompt": prompt,
                "generation": response["generation"],
                "user_id": user_id,
                "translations": translations,
                "timestamp": datetime.now().isoformat(),
            }

            # Insert as new document instead of updating
            db.conversations.insert_one(conversation_data)

            # after addeding in the confidence we prep the response
            response_data = {
                "conversation_id": conversation_id,
                "generation": response["generation"],
                "confidence": response["confidence_score"],
                "translations": response.get("translations", []),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CompleteConversationsView(MongoDBMixin, APIView):
    def post(self, request):
        try:
            serializer = CompleteConversationsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid input data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            conversation_data = {
                "conversation_id": serializer.validated_data["conversation_id"],
                "user_id": serializer.validated_data["user_id"],
                "messages": serializer.validated_data["messages"],
                "translations": serializer.validated_data.get("translations", []),
                "timestamp": datetime.now().isoformat(),
            }

            db = self.get_db()
            db.complete_conversations.insert_one(conversation_data)

            return Response(
                {"message": "Conversation saved successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Request processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
