import json
import os

from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import capture_interaction, generate_answer, submit_feedback
from .serializers import (
    AIResponseSerializer,
    CaptureSummarySerializer,
    ChatRatingSerializer,
    CorrectBoolSerializer,
    IncorrectAnswerResponseSerializer,
    UserInputSerializer,
)


class UserInputView(APIView):
    def post(self, request):
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            generation = generate_answer(prompt)
            response_data = {"generation": generation}
            self.save_to_json(
                "chat_qna.json",
                {"type": "user_input", "prompt": prompt, "generation": generation},
            )
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIResponseView(APIView):
    def post(self, request):
        serializer = AIResponseSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data["answer"]
            self.save_to_json(
                "chat_qna.json", {"type": "ai_response", "answer": answer}
            )
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data["is_correct"]
            self.save_to_json(
                "chat_qna.json", {"type": "correct_bool", "is_correct": is_correct}
            )
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data["rating"]
            self.save_to_json(
                "chat_qna.json", {"type": "chat_rating", "rating": rating}
            )
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncorrectAnswerResponseView(APIView):
    def post(self, request):
        serializer = IncorrectAnswerResponseSerializer(data=request.data)
        if serializer.is_valid():
            correct_answer = serializer.validated_data["correct_answer"]
            self.save_to_json(
                "chat_qna.json",
                {"type": "incorrect_answer", "correct_answer": correct_answer},
            )
            return Response(
                {"message": "Correct answer received"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptureSummaryView(APIView):
    def post(self, request):
        serializer = CaptureSummarySerializer(data=request.data)
        if serializer.is_valid():
            user_input = serializer.validated_data["user_input"]
            ai_response = serializer.validated_data["ai_response"]
            correct_bool = serializer.validated_data["correct_bool"]
            chat_rating = serializer.validated_data["chat_rating"]
            incorrect_answer_response = serializer.validated_data.get(
                "incorrect_answer_response", ""
            )
            metadata = serializer.validated_data.get("metadata", {})

            result = capture_interaction(
                prompt=user_input,
                response=ai_response,
                question_correct=correct_bool,
                correct_rating=chat_rating,
                correct_answer=incorrect_answer_response,
                metadata=metadata,
            )
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR, "data", "chat_qna.json")
        if not os.path.exists(file_path):
            return Response(
                {"error": "No data available"}, status=status.HTTP_404_NOT_FOUND
            )

        with open(file_path, "r") as f:
            chat_qna_data = [json.loads(line) for line in f]

        return Response(chat_qna_data, status=status.HTTP_200_OK)


class ViewSummaryView(APIView):
    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR, "data", "interactions.json")
        if not os.path.exists(file_path):
            return Response(
                {"error": "No data available"}, status=status.HTTP_404_NOT_FOUND
            )

        with open(file_path, "r") as f:
            interaction_data = json.load(f)

        return Response(interaction_data, status=status.HTTP_200_OK)


def save_to_json(self, filename, data):
    file_path = os.path.join(settings.BASE_DIR, "data", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a") as f:
        json.dump(data, f)
        f.write("\n")
